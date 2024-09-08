from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(unique=True)


class UserSettings(Base):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True)
    current_language: Mapped[int] = mapped_column(ForeignKey("language.id"), default=1)


class Language(Base):
    __tablename__ = "language"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    language_code: Mapped[str] = mapped_column(unique=True)
    language_name: Mapped[str] = mapped_column()
