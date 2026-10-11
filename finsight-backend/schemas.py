"""Pydantic request/response models for the FinSight API."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be blank.")
        return value

    @field_validator("email")
    @classmethod
    def email_must_be_valid(cls, value: str) -> str:
        value = value.strip().lower()
        if not EMAIL_RE.match(value):
            raise ValueError("Enter a valid email address.")
        return value


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalise_email(cls, value: str) -> str:
        return value.strip().lower()


class UserPublic(BaseModel):
    id: int
    name: str
    email: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class PurchaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str = Field(default="Other", max_length=40)
    amount: float = Field(gt=0)
    days_from_now: int = Field(default=0, ge=0, le=365)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("category")
    @classmethod
    def strip_category(cls, value: str) -> str:
        return value.strip() or "Other"


class PurchasePublic(BaseModel):
    id: int
    name: str
    category: str
    amount: float
    days_from_now: int
