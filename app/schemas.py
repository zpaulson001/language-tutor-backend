from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    pass


class User(UserBase):
    id: int

    class Config:
        from_attributes = True
