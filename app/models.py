from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    pin: Mapped[str | None] = mapped_column(String(10), nullable=True)

    tips: Mapped[list["Tip"]] = relationship(back_populates="user")


class WeightClass(Base):
    __tablename__ = "weight_classes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    kampfbeginn: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    tag: Mapped[date] = mapped_column(Date, nullable=False)

    athletes: Mapped[list["Athlete"]] = relationship(back_populates="weight_class")
    tips: Mapped[list["Tip"]] = relationship(back_populates="weight_class")
    result: Mapped["Result | None"] = relationship(back_populates="weight_class")


class Athlete(Base):
    __tablename__ = "athletes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    weight_class_id: Mapped[int] = mapped_column(ForeignKey("weight_classes.id"))
    nation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    nation_code: Mapped[str | None] = mapped_column(String(3), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(1), nullable=True)
    wrl_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)

    weight_class: Mapped["WeightClass"] = relationship(back_populates="athletes")


class Tip(Base):
    __tablename__ = "tips"
    __table_args__ = (UniqueConstraint("user_id", "weight_class_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    weight_class_id: Mapped[int] = mapped_column(ForeignKey("weight_classes.id"))
    platz_1: Mapped[int | None] = mapped_column(ForeignKey("athletes.id"))
    platz_2: Mapped[int | None] = mapped_column(ForeignKey("athletes.id"))
    platz_3a: Mapped[int | None] = mapped_column(ForeignKey("athletes.id"))
    platz_3b: Mapped[int | None] = mapped_column(ForeignKey("athletes.id"))

    user: Mapped["User"] = relationship(back_populates="tips")
    weight_class: Mapped["WeightClass"] = relationship(back_populates="tips")


class Result(Base):
    __tablename__ = "results"

    weight_class_id: Mapped[int] = mapped_column(
        ForeignKey("weight_classes.id"), primary_key=True
    )
    platz_1: Mapped[int | None] = mapped_column(ForeignKey("athletes.id"))
    platz_2: Mapped[int | None] = mapped_column(ForeignKey("athletes.id"))
    platz_3a: Mapped[int | None] = mapped_column(ForeignKey("athletes.id"))
    platz_3b: Mapped[int | None] = mapped_column(ForeignKey("athletes.id"))

    weight_class: Mapped["WeightClass"] = relationship(back_populates="result")
