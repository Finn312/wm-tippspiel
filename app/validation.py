from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Athlete


def validate_athlete_slots(slots: list[int | None], weight_class_id: int, db: Session) -> None:
    chosen = [s for s in slots if s is not None]

    if len(chosen) != len(set(chosen)):
        raise HTTPException(status_code=400, detail="Jeder Athlet darf nur einmal vorkommen")

    if chosen:
        count = (
            db.query(Athlete)
            .filter(Athlete.id.in_(chosen), Athlete.weight_class_id == weight_class_id)
            .count()
        )
        if count != len(chosen):
            raise HTTPException(
                status_code=400,
                detail="Ein Athlet gehoert nicht zu dieser Gewichtsklasse",
            )
