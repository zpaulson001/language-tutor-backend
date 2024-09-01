from typing import Literal
from pydantic import BaseModel, EmailStr


class StoryGenerate(BaseModel):
    story_prompt: str
    level: Literal["beginner", "intermediate", "advanced"]


class LoginRequest(BaseModel):
    email: EmailStr


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    pass


class User(UserBase):
    id: int

    class Config:
        from_attributes = True
