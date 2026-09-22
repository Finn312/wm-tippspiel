from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.database import get_db
from app.models import Result, WeightClass
from app.schemas import ResultIn, ResultOut
from app.validation import validate_athlete_slots

router = APIRouter(prefix="/results", tags=["results"])


@router.get("/{weight_class_id}", response_model=ResultOut | None)
def get_result(weight_class_id: int, db: Session = Depends(get_db)):
    return db.get(Result, weight_class_id)


@router.put("/{weight_class_id}", response_model=ResultOut, dependencies=[Depends(require_admin)])
def upsert_result(weight_class_id: int, result_in: ResultIn, db: Session = Depends(get_db)):
    wc = db.get(WeightClass, weight_class_id)
    if wc is None:
        raise HTTPException(status_code=404, detail="Gewichtsklasse nicht gefunden")

    validate_athlete_slots(
        [result_in.platz_1, result_in.platz_2, result_in.platz_3a, result_in.platz_3b],
        weight_class_id,
        db,
    )

    result = db.get(Result, weight_class_id)
    if result is None:
        result = Result(weight_class_id=weight_class_id)
        db.add(result)

    result.platz_1 = result_in.platz_1
    result.platz_2 = result_in.platz_2
    result.platz_3a = result_in.platz_3a
    result.platz_3b = result_in.platz_3b

    db.commit()
    db.refresh(result)
    return result
