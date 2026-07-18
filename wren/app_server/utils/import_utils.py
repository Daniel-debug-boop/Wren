import importlib
from functools import lru_cache
from typing import TypeVar

T = TypeVar('T')


def import_from(qual_name: str) -> Any:
    """Import a value from its fully qualified name.

    This function is a utility to dynamically import any Python value (class,
    function, variable) from its fully qualified name. For example,
    'wren.app_server.user_auth.UserAuth' would import the UserAuth class from the
    wren.app_server.user_auth module.

    Args:
        qual_name: A fully qualified name in the format 'module.submodule.name'
                  e.g. 'wren.app_server.user_auth.UserAuth'

    Returns:
        The imported value (class, function, or variable)

    Example:
        >>> UserAuth = import_from('wren.app_server.user_auth.UserAuth')
        >>> auth = UserAuth()
    """
    parts = qual_name.split('.')
    module_name = '.'.join(parts[:-1])
    module = importlib.import_module(module_name)
    result = getattr(module, parts[-1])
    return result


@lru_cache()
def _get_impl(cls: type[T], impl_name: str | None) -> type[T]:
    if impl_name is None:
        return cls
    impl_class = import_from(impl_name)
    if not (cls == impl_class or issubclass(impl_class, cls)):
        raise TypeError(
            f"Implementation {impl_name!r} must be a subclass of "
            f"{cls.__module__}.{cls.__qualname__}, "
            f"got {impl_class.__module__}.{impl_class.__qualname__}"
        )
    return impl_class


def get_impl(cls: type[T], impl_name: str | None) -> type[T]:
    """Import and validate a named implementation of a base class.

    This function is an extensibility mechanism in OpenHands that allows runtime
    substitution of implementations. It enables applications to customize behavior by
    providing their own implementations of OpenHands base classes.

    The function ensures type safety by validating that the imported class is either
    the same as or a subclass of the specified base class.

    Args:
        cls: The base class that defines the interface
        impl_name: Fully qualified name of the implementation class, or None to use
                  the base class
                  e.g. 'wren.server.conversation_service.'
                       'StandaloneConversationService'

    Returns:
        The implementation class, which is guaranteed to be a subclass of cls

    Example:
        >>> # Get default implementation
        >>> ConversationService = get_impl(ConversationService, None)
        >>> # Get custom implementation
        >>> CustomService = get_impl(
        ...     ConversationService, 'myapp.CustomConversationService'
        ... )

    Common Use Cases:
        - Server components (ConversationService, UserAuth, etc.)
        - Storage implementations (SettingsStore, SecretsStore, etc.)
        - Service integrations (GitHub, GitLab, Bitbucket, Azure DevOps services)

    The implementation is cached to avoid repeated imports of the same class.
    """
    return _get_impl(cls, impl_name)  # type: ignore
