from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisSettings(BaseModel):
    url: str = Field(..., description="Redis connection URI")
    use_ssl: bool = Field(False, description="Whether to enforce SSL on Redis connections")


class JWTSettings(BaseModel):
    secret_key: str = Field(..., description="HMAC secret used to sign JWT access tokens")
    algorithm: str = Field("HS256", description="Signing algorithm for JWT tokens")
    access_token_ttl_minutes: int = Field(15, ge=5, le=120, description="Minutes before access token expires")
    refresh_token_ttl_days: int = Field(30, ge=1, le=120, description="Days before refresh token expires")


class MailSettings(BaseModel):
    api_key: str = Field(..., description="Resend API key for transactional emails")
    from_email: str = Field(..., description="Sender email address used for OTP emails")
    otp_template_id: str | None = Field(None, description="Optional Resend template ID for OTP emails")


class CloudinarySettings(BaseModel):
    cloud_name: str = Field(..., description="Cloudinary cloud name")
    api_key: str = Field(..., description="Cloudinary API key for signature generation")
    api_secret: str = Field(..., description="Cloudinary API secret used to sign upload requests")
    upload_folder: str = Field("stiky/uploads", description="Default folder for uploaded assets")
    unsigned_preset: str | None = Field(
        None,
        description="Optional preset name when using unsigned uploads (not recommended for production)",
    )


class SecuritySettings(BaseModel):
    cors_origins: list[AnyHttpUrl] = Field(default_factory=list)
    cookie_domain: str | None = Field(None, description="Domain attribute for auth cookies")
    secure_cookies: bool = Field(True, description="Mark auth cookies as Secure")
    same_site: Literal["lax", "strict", "none"] = Field("lax", description="SameSite policy for cookies")


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(".env"), env_prefix="APP_", env_nested_delimiter="__"
    )

    env: Literal["local", "dev", "staging", "prod", "test"] = Field(
        "local", description="Application environment name"
    )
    project_name: str = Field("Stiky API", description="Human readable project name")
    api_v1_prefix: str = Field("/api/v1", description="Root prefix for versioned API routes")
    frontend_base_url: AnyHttpUrl | None = Field(None, description="Primary frontend origin for CORS")
    backend_base_url: AnyHttpUrl | None = Field(None, description="Public API base URL")
    database_url: str = Field(..., description="SQLAlchemy compatible PostgreSQL DSN")
    redis: RedisSettings
    jwt: JWTSettings
    mail: MailSettings
    cloudinary: CloudinarySettings
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    otp_code_length: int = Field(6, ge=4, le=10)
    otp_ttl_minutes: int = Field(10, ge=5, le=30)
    otp_retry_limit: int = Field(5, ge=1, le=10)
    otp_request_limit_per_email: int = Field(20, ge=1, le=100)
    otp_request_limit_window_minutes: int = Field(30, ge=5, le=180)
    otp_request_limit_per_ip: int = Field(20, ge=1, le=200)
    resend_tracking: bool = Field(True, description="Enable message tracking metadata on emails")


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()


settings = get_settings()
