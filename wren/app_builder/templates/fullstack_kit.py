"""Full-Stack Infrastructure Kit — generates database, auth, and API boilerplate.

Provides generator functions for:
  - SQLAlchemy models with migrations
  - JWT authentication middleware
  - Environment configuration
  - FastAPI route scaffolding
  - React state management (Zustand)
  - Error handling middleware
  - Docker/deployment configuration
"""

from __future__ import annotations

from typing import Any


# ── Database ──────────────────────────────────────────────────────────────


def generate_sqlalchemy_base() -> str:
    """Generate SQLAlchemy database setup with session management."""
    return """\
\"\"\"Database configuration and session management.\"\"\"

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from typing import Generator

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    \"\"\"FastAPI dependency: yields a database session.\"\"\"
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    \"\"\"Create all tables (idempotent).\"\"\"
    Base.metadata.create_all(bind=engine)
"""


def generate_user_model() -> str:
    """Generate User model with authentication fields."""
    return """\
\"\"\"User model with authentication and profile fields.\"\"\"

import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from .base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(255), default="")
    avatar_url = Column(String(500), default="")
    bio = Column(Text, default="")
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    role = Column(String(50), default="user", nullable=False)  # user, admin, moderator
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "display_name": self.display_name,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
"""


# ── Authentication ────────────────────────────────────────────────────────


def generate_jwt_auth() -> str:
    """Generate JWT authentication middleware and utilities."""
    return """\
\"\"\"JWT authentication middleware — sign, verify, decode tokens.\"\"\"

import os
import datetime
import json
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .database import get_db
from models.user import User

# ── Configuration ─────────────────────────────────────────────────────

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


# ── Password Helpers ───────────────────────────────────────────────────

def hash_password(password: str) -> str:
    \"\"\"Hash a password using bcrypt.\"\"\"
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    \"\"\"Verify a password against its hash.\"\"\"
    return pwd_context.verify(plain_password, hashed_password)


# ── Token Helpers ──────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    \"\"\"Create a JWT access token.\"\"\"
    to_encode = data.copy()
    expire = datetime.datetime.now(datetime.UTC) + (
        expires_delta or datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    \"\"\"Create a JWT refresh token.\"\"\"
    to_encode = data.copy()
    expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    \"\"\"Decode and validate a JWT token. Returns the payload.\"\"\"
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


# ── Dependency Injection ────────────────────────────────────────────────

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    \"\"\"FastAPI dependency: extract and validate current user from JWT.\"\"\"
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    user_id: int = payload.get("sub", 0)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    \"\"\"FastAPI dependency: get current user or None (for public endpoints).\"\"\"
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


# ── Auth Routes ─────────────────────────────────────────────────────────

from fastapi import APIRouter

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
async def register(email: str, username: str, password: str, db: Session = Depends(get_db)):
    \"\"\"Register a new user account.\"\"\"
    # Check if user exists
    existing = db.query(User).filter(
        (User.email == email) | (User.username == username)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username already registered",
        )

    user = User(
        email=email,
        username=username,
        password_hash=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token({"sub": user.id})
    refresh_token = create_refresh_token({"sub": user.id})

    return {
        "user": user.to_dict(),
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/login")
async def login(email: str, password: str, db: Session = Depends(get_db)):
    \"\"\"Authenticate and return tokens.\"\"\"
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user.last_login_at = datetime.datetime.now(datetime.UTC)
    db.commit()

    access_token = create_access_token({"sub": user.id})
    refresh_token = create_refresh_token({"sub": user.id})

    return {
        "user": user.to_dict(),
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh")
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    \"\"\"Issue a new access token using a refresh token.\"\"\"
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    new_access_token = create_access_token({"sub": user.id})

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
    }


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    \"\"\"Get the currently authenticated user's profile.\"\"\"
    return current_user.to_dict()
"""


# ── Environment Configuration ────────────────────────────────────────────


def generate_env_example(has_database: bool = True, has_auth: bool = True) -> str:
    """Generate .env.example with all required environment variables."""
    lines = [
        "# ── Application ───────────────────────────────────────",
        "APP_NAME=my-app",
        "APP_ENV=development  # development | staging | production",
        "DEBUG=true",
        "LOG_LEVEL=info",
        "",
        "# ── Server ─────────────────────────────────────────────",
        "HOST=0.0.0.0",
        "PORT=8000",
        "CORS_ORIGINS=http://localhost:5173,http://localhost:3000",
        "",
    ]

    if has_database:
        lines.extend([
            "# ── Database ─────────────────────────────────────────",
            "DATABASE_URL=sqlite:///./app.db",
            "# DATABASE_URL=postgresql://user:password@localhost:5432/myapp",
            "",
        ])

    if has_auth:
        lines.extend([
            "# ── Authentication ───────────────────────────────────",
            "JWT_SECRET_KEY=change-me-to-a-random-64-char-string",
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30",
            "JWT_REFRESH_TOKEN_EXPIRE_DAYS=7",
            "",
        ])

    lines.extend([
        "# ── External APIs ─────────────────────────────────────",
        "# OPENAI_API_KEY=sk-...",
        "# ANTHROPIC_API_KEY=sk-ant-...",
        "",
        "# ── Redis (optional) ───────────────────────────────────",
        "# REDIS_URL=redis://localhost:6379/0",
        "",
        "# ── Email (optional) ───────────────────────────────────",
        "# SMTP_HOST=smtp.sendgrid.net",
        "# SMTP_PORT=587",
        "# SMTP_USER=apikey",
        "# SMTP_PASSWORD=...",
        "",
        "# ── Storage (optional) ────────────────────────────────",
        "# S3_BUCKET=my-bucket",
        "# S3_REGION=us-east-1",
        "# S3_ACCESS_KEY=...",
        "# S3_SECRET_KEY=...",
    ])

    return "\n".join(lines) + "\n"


# ── Docker Configuration ─────────────────────────────────────────────────


def generate_dockerfile() -> str:
    """Generate multi-stage Dockerfile for Python/FastAPI backend."""
    return """\
# ── Build Stage ───────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    gcc libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ── Runtime Stage ─────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Create non-root user
RUN addgroup --system app && adduser --system --group app

# Copy installed dependencies
COPY --from=builder /root/.local /home/app/.local

# Copy application code
COPY . .

# Set ownership
RUN chown -R app:app /app

USER app

ENV PATH=/home/app/.local/bin:$PATH \\
    PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""


def generate_docker_compose() -> str:
    """Generate docker-compose.yml with app, db, and optional services."""
    return """\
version: "3.9"

services:
  app:
    build: .
    container_name: myapp-api
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./app.db:/app/app.db
      - ./uploads:/app/uploads
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # PostgreSQL (optional — uncomment for production)
  # db:
  #   image: postgres:16-alpine
  #   container_name: myapp-db
  #   restart: unless-stopped
  #   environment:
  #     POSTGRES_USER: myapp
  #     POSTGRES_PASSWORD: myapp_secret
  #     POSTGRES_DB: myapp
  #   ports:
  #     - "5432:5432"
  #   volumes:
  #     - pgdata:/var/lib/postgresql/data
  #   healthcheck:
  #     test: ["CMD-SHELL", "pg_isready -U myapp"]
  #     interval: 10s
  #     timeout: 5s

# volumes:
#   pgdata:
"""


# ── Frontend State Management (Zustand) ────────────────────────────────────


def generate_zustand_store() -> str:
    """Generate Zustand store pattern for state management."""
    return """\
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// ── Types ─────────────────────────────────────────────────────────

interface User {
    id: number
    email: string
    username: string
    display_name: string
    avatar_url: string
    role: string
}

interface AuthState {
    user: User | null
    accessToken: string | null
    refreshToken: string | null
    isAuthenticated: boolean
    isLoading: boolean
    error: string | null

    // Actions
    login: (email: string, password: string) => Promise<void>
    register: (email: string, username: string, password: string) => Promise<void>
    logout: () => void
    setUser: (user: User) => void
    clearError: () => void
}

interface UIState {
    sidebarOpen: boolean
    theme: 'dark' | 'light'
    toggleSidebar: () => void
    setTheme: (theme: 'dark' | 'light') => void
}

// ── Auth Store ────────────────────────────────────────────────────

export const useAuthStore = create<AuthState>()(
    persist(
        (set, get) => ({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,

            login: async (email: string, password: string) => {
                set({ isLoading: true, error: null })
                try {
                    const response = await fetch('/api/auth/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ email, password }),
                    })
                    if (!response.ok) {
                        const err = await response.json()
                        throw new Error(err.detail || 'Login failed')
                    }
                    const data = await response.json()
                    set({
                        user: data.user,
                        accessToken: data.access_token,
                        refreshToken: data.refresh_token,
                        isAuthenticated: true,
                        isLoading: false,
                    })
                } catch (err) {
                    set({
                        error: err instanceof Error ? err.message : 'Login failed',
                        isLoading: false,
                    })
                }
            },

            register: async (email: string, username: string, password: string) => {
                set({ isLoading: true, error: null })
                try {
                    const response = await fetch('/api/auth/register', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ email, username, password }),
                    })
                    if (!response.ok) {
                        const err = await response.json()
                        throw new Error(err.detail || 'Registration failed')
                    }
                    const data = await response.json()
                    set({
                        user: data.user,
                        accessToken: data.access_token,
                        refreshToken: data.refresh_token,
                        isAuthenticated: true,
                        isLoading: false,
                    })
                } catch (err) {
                    set({
                        error: err instanceof Error ? err.message : 'Registration failed',
                        isLoading: false,
                    })
                }
            },

            logout: () => {
                set({
                    user: null,
                    accessToken: null,
                    refreshToken: null,
                    isAuthenticated: false,
                    error: null,
                })
            },

            setUser: (user: User) => set({ user }),

            clearError: () => set({ error: null }),
        }),
        {
            name: 'auth-storage',
            partialize: (state) => ({
                user: state.user,
                accessToken: state.accessToken,
                refreshToken: state.refreshToken,
                isAuthenticated: state.isAuthenticated,
            }),
        }
    )
)

// ── UI Store ───────────────────────────────────────────────────────

export const useUIStore = create<UIState>()(
    persist(
        (set) => ({
            sidebarOpen: true,
            theme: 'dark',

            toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

            setTheme: (theme: 'dark' | 'light') => set({ theme }),
        }),
        {
            name: 'ui-storage',
        }
    )
)

// ── Auth API helper ───────────────────────────────────────────────

export function getAuthHeaders(): Record<string, string> {
    const token = useAuthStore.getState().accessToken
    if (!token) return {}
    return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
    }
}

export async function apiFetch<T>(
    url: string,
    options: RequestInit = {}
): Promise<T> {
    const headers = {
        ...getAuthHeaders(),
        ...options.headers,
    }

    const response = await fetch(url, { ...options, headers })

    if (response.status === 401) {
        // Try refresh
        const refreshToken = useAuthStore.getState().refreshToken
        if (refreshToken) {
            const refreshResponse = await fetch('/api/auth/refresh', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: refreshToken }),
            })
            if (refreshResponse.ok) {
                const data = await refreshResponse.json()
                useAuthStore.getState().accessToken = data.access_token
                // Retry with new token
                headers['Authorization'] = `Bearer ${data.access_token}`
                const retryResponse = await fetch(url, { ...options, headers })
                if (!retryResponse.ok) {
                    throw new Error(`Request failed: ${retryResponse.statusText}`)
                }
                return retryResponse.json()
            }
        }
        // Refresh failed — logout
        useAuthStore.getState().logout()
        throw new Error('Session expired')
    }

    if (!response.ok) {
        throw new Error(`Request failed: ${response.statusText}`)
    }

    return response.json()
    }
"""


# ── API Router Generator ────────────────────────────────────────────────


def generate_api_router() -> str:
    """Generate FastAPI router pattern with CRUD endpoints."""
    return """\
\"\"\"Generic CRUD API router — extend for specific resources.\"\"\"

from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user, get_optional_user
from models.user import User


def create_crud_router(
    prefix: str,
    tags: list[str],
    model_class: Any,
    create_schema: Any = None,
    update_schema: Any = None,
    response_schema: Any = None,
    auth_required: bool = True,
) -> APIRouter:
    \"\"\"Create a CRUD router for a given model.

    Args:
        prefix: URL prefix (e.g., '/api/items')
        tags: OpenAPI tags
        model_class: SQLAlchemy model class
        create_schema: Pydantic schema for creation
        update_schema: Pydantic schema for updates
        response_schema: Pydantic schema for responses
        auth_required: Whether auth is required for all endpoints
    \"\"\"
    router = APIRouter(prefix=prefix, tags=tags)
    auth_dep = Depends(get_current_user) if auth_required else None

    @router.get("")
    async def list_items(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        db: Session = Depends(get_db),
        current_user: Optional[User] = auth_dep,
    ):
        items = db.query(model_class).offset(skip).limit(limit).all()
        return items

    @router.post("", status_code=status.HTTP_201_CREATED)
    async def create_item(
        data: Any,
        db: Session = Depends(get_db),
        current_user: Optional[User] = auth_dep,
    ):
        if create_schema:
            data = create_schema(**data) if isinstance(data, dict) else data
        item = model_class(**data.model_dump() if hasattr(data, 'model_dump') else data)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @router.get("/{item_id}")
    async def get_item(
        item_id: int,
        db: Session = Depends(get_db),
        current_user: Optional[User] = auth_dep,
    ):
        item = db.query(model_class).filter(model_class.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return item

    @router.put("/{item_id}")
    async def update_item(
        item_id: int,
        data: Any,
        db: Session = Depends(get_db),
        current_user: Optional[User] = auth_dep,
    ):
        item = db.query(model_class).filter(model_class.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        if update_schema:
            data = update_schema(**data) if isinstance(data, dict) else data
        update_data = data.model_dump(exclude_unset=True) if hasattr(data, 'model_dump') else data
        for key, value in update_data.items():
            setattr(item, key, value)
        db.commit()
        db.refresh(item)
        return item

    @router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_item(
        item_id: int,
        db: Session = Depends(get_db),
        current_user: Optional[User] = auth_dep,
    ):
        item = db.query(model_class).filter(model_class.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        db.delete(item)
        db.commit()
        return None

    return router
"""
