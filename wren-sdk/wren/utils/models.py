"""Pydantic v2 base model for Wren SDK."""

from __future__ import annotations

import inspect
import threading
from datetime import datetime, timezone
from typing import Annotated, Any, Self, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Discriminator,
    Field,
    ModelWrapValidatorHandler,
    SerializationInfo,
    SerializerFunctionWrapHandler,
    Tag,
    ValidationInfo,
    computed_field,
    model_serializer,
    model_validator,
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema


_thread_local = threading.local()


def _get_schemas_in_progress() -> dict[type, JsonSchemaValue]:
    if not hasattr(_thread_local, "schemas_in_progress"):
        _thread_local.schemas_in_progress = {}
    return _thread_local.schemas_in_progress


def _is_abstract(type_: type) -> bool:
    try:
        return inspect.isabstract(type_) or ABC in type_.__bases__
    except Exception:
        return False


def get_handler_class_name(handler: SerializerFunctionWrapHandler) -> str:
    repr_str = str(handler)
    _, name = repr_str.split("=", 1)
    return name[:-1]


def kind_of(obj) -> str:
    if isinstance(obj, dict):
        return obj["kind"]
    if not hasattr(obj, "__name__"):
        obj = obj.__class__
    return obj.__name__


def _get_all_subclasses(cls) -> set[type]:
    result = set()
    for subclass in cls.__subclasses__():
        result.add(subclass)
        result.update(_get_all_subclasses(subclass))
    return result


_subclass_generation: int = 0
_subclass_generation_lock = threading.Lock()
_concrete_cache: dict[type, tuple[int, tuple[type, ...]]] = {}
_checked_cache: dict[type, tuple[int, dict[str, type]]] = {}


def _bump_subclass_generation() -> None:
    global _subclass_generation
    with _subclass_generation_lock:
        _subclass_generation += 1


def get_known_concrete_subclasses(cls) -> tuple[type, ...]:
    cached = _concrete_cache.get(cls)
    if cached is not None and cached[0] == _subclass_generation:
        return cached[1]

    out: list[type] = []
    for sub in cls.__subclasses__():
        out.extend(get_known_concrete_subclasses(sub))
        if not _is_abstract(sub):
            out.append(sub)

    out.sort(key=lambda t: (t.__module__, getattr(t, "__qualname__", t.__name__)))
    result = tuple(out)
    _concrete_cache[cls] = (_subclass_generation, result)
    return result


def _get_checked_concrete_subclasses(cls: type) -> dict[str, type]:
    cached = _checked_cache.get(cls)
    if cached is not None and cached[0] == _subclass_generation:
        return cached[1]

    result: dict[str, type] = {}
    for sub in get_known_concrete_subclasses(cls):
        existing = result.get(sub.__name__)
        if existing:
            raise ValueError(
                f"Duplicate class definition for {cls.__module__}.{cls.__name__}: "
                f"{existing.__module__}.{existing.__name__} : "
                f"{sub.__module__}.{sub.__name__}"
            )
        if "<locals>" in sub.__qualname__:
            raise ValueError(
                f"Local classes not supported! {sub.__module__}.{sub.__name__} "
                f"/ {cls.__module__}.{cls.__name__} "
                "(Since they may not exist at deserialization time)"
            )
        result[sub.__name__] = sub
    _checked_cache[cls] = (_subclass_generation, result)
    return result


def clear_subclass_cache() -> None:
    _bump_subclass_generation()


class OpenHandsModel(BaseModel):
    """Deprecated: Use pydantic.BaseModel directly."""

    pass


class WrenModel(BaseModel):
    """Base model for all Wren SDK types.

    Features:
    - Pydantic v2
    - UTC timestamps by default
    - Frozen (immutable) instances
    - camelCase serialization for JSON
    """

    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
        serialize_by_alias=True,
        str_strip_whitespace=True,
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict with camelCase keys."""
        return self.model_dump(by_alias=True, exclude_none=True)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return self.model_dump_json(by_alias=True, exclude_none=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WrenModel:
        """Deserialize from dict."""
        return cls.model_validate(data)

    @classmethod
    def from_json(cls, json_str: str) -> WrenModel:
        """Deserialize from JSON string."""
        return cls.model_validate_json(json_str)


def utc_now() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


def ensure_utc(dt: datetime) -> datetime:
    """Ensure datetime is UTC timezone-aware."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


from abc import ABC


class DiscriminatedUnionMixin(OpenHandsModel):
    """Mixin for discriminated union support in Pydantic models."""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        _bump_subclass_generation()

    @computed_field
    @property
    def kind(self) -> str:
        return self.__class__.__name__

    @model_validator(mode="wrap")
    @classmethod
    def _validate_subtype(
        cls, data: Any, handler: ModelWrapValidatorHandler[Self], info: ValidationInfo
    ) -> Self:
        if isinstance(data, cls):
            return data
        kind = data.pop("kind", None) if isinstance(data, dict) else None
        if not _is_abstract(cls):
            assert kind is None or kind == cls.__name__
            return handler(data)
        if kind is None:
            subclasses = _get_checked_concrete_subclasses(cls)
            if not subclasses:
                raise ValueError(f"No kinds defined for {cls.__module__}.{cls.__name__}")
            elif len(subclasses) == 1:
                kind = next(iter(subclasses))
            else:
                kind = ""
        subclass = cls.resolve_kind(kind)
        return subclass.model_validate(data, context=info.context)

    @model_serializer(mode="wrap")
    def _serialize_by_kind(self, handler: SerializerFunctionWrapHandler, info: SerializationInfo):
        if isinstance(self, dict):
            return self
        if self._is_handler_for_current_class(handler):
            result = handler(self)
            return result
        result = self.model_dump(
            mode=info.mode,
            context=info.context,
            by_alias=info.by_alias,
            exclude_unset=info.exclude_unset,
            exclude_defaults=info.exclude_defaults,
            exclude_none=info.exclude_none,
            exclude_computed_fields=info.exclude_computed_fields,
            round_trip=info.round_trip,
            serialize_as_any=info.serialize_as_any,
        )
        return result

    def _is_handler_for_current_class(self, handler: SerializerFunctionWrapHandler) -> bool:
        return self.__class__.__name__ == get_handler_class_name(handler)

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: CoreSchema, handler: Any) -> JsonSchemaValue:
        schemas_in_progress = _get_schemas_in_progress()
        schema = schemas_in_progress.get(cls)
        if schema:
            return schema
        schemas_in_progress[cls] = {"$ref": f"#/$defs/{cls.__name__}"}
        try:
            if _is_abstract(cls):
                subclasses = _get_checked_concrete_subclasses(cls)
                if not subclasses:
                    raise ValueError(f"No subclasses defined for {cls.__name__}")
                if len(subclasses) == 1:
                    gen = handler.generate_json_schema
                    sub_schema = gen.generate_inner(
                        next(iter(subclasses.values())).__pydantic_core_schema__
                    )
                    return sub_schema
                gen = handler.generate_json_schema
                schemas = []
                for sub in subclasses.values():
                    sub_schema = gen.generate_inner(sub.__pydantic_core_schema__)
                    schemas.append(sub_schema)
                mapping = {}
                for option in schemas:
                    if "$ref" in option:
                        kind = option["$ref"].split("/")[-1]
                        mapping[kind] = option["$ref"]
                schema = {
                    "oneOf": schemas,
                    "discriminator": {"propertyName": "kind", "mapping": mapping},
                }
            else:
                schema = handler(core_schema)
                schema["properties"]["kind"] = {
                    "const": cls.__name__,
                    "title": "Kind",
                    "type": "string",
                }
        finally:
            schemas_in_progress.pop(cls)
        return schema

    @classmethod
    def resolve_kind(cls, kind: str) -> type[Self]:
        subclasses = _get_checked_concrete_subclasses(cls)
        subclass = subclasses.get(kind)
        if subclass:
            return subclass
        raise ValueError(
            f"Unknown kind '{kind}' for {cls.__module__}.{cls.__name__}; "
            f"Expected one of: {list(subclasses)}"
        )

    @classmethod
    def get_serializable_type(cls) -> type:
        if not _is_abstract(cls):
            return cls
        subclasses = _get_checked_concrete_subclasses(cls)
        if not subclasses:
            return cls
        if len(subclasses) == 1:
            return next(iter(subclasses.values()))
        serializable_type = Annotated[
            Union[*tuple(Annotated[t, Tag(n)] for n, t in subclasses.items())],
            Discriminator(kind_of),
        ]
        return serializable_type
