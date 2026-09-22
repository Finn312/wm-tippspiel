from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class LoginRequest(BaseModel):
    name: str
    pin: str | None = None


class LoginResponse(BaseModel):
    token: str
    user: UserOut


class AthleteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    weight_class_id: int


class WeightClassOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    kampfbeginn: datetime
    tag: date
    locked: bool = False


class TipIn(BaseModel):
    platz_1: int | None = None
    platz_2: int | None = None
    platz_3a: int | None = None
    platz_3b: int | None = None


class TipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    weight_class_id: int
    platz_1: int | None
    platz_2: int | None
    platz_3a: int | None
    platz_3b: int | None
    points: int | None = None


class ResultIn(BaseModel):
    platz_1: int | None = None
    platz_2: int | None = None
    platz_3a: int | None = None
    platz_3b: int | None = None


class ResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    weight_class_id: int
    platz_1: int | None
    platz_2: int | None
    platz_3a: int | None
    platz_3b: int | None


class LeaderboardEntry(BaseModel):
    user_id: int
    name: str
    points: int
