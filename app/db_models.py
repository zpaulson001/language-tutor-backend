from sqlalchemy import ForeignKey, ForeignKeyConstraint, PrimaryKeyConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(unique=True)


class UserSettings(Base):
    __tablename__ = "user_settings"
    user_id: Mapped[int] = mapped_column(unique=True)
    current_language: Mapped[int] = mapped_column(server_default=text("1"))

    __table_args__ = (
        ForeignKeyConstraint(["user_id"], ["user.id"]),
        ForeignKeyConstraint(["current_language"], ["language.id"]),
        PrimaryKeyConstraint("user_id"),
    )


class Language(Base):
    __tablename__ = "language"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    language_code: Mapped[str] = mapped_column(unique=True)
    language_name: Mapped[str] = mapped_column()
