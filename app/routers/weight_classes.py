from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Athlete, WeightClass
from app.schemas import AthleteOut, WeightClassOut
from app.sorting import athlete_surname_key

router = APIRouter(prefix="/weight-classes", tags=["weight-classes"])

EDIT_CUTOFF = timedelta(minutes=30)


def is_locked(weight_class: WeightClass) -> bool:
    """Reveal-Sperre: ab kampfbeginn sind Tipps aller Nutzer fuer alle sichtbar."""
    return datetime.now() >= weight_class.kampfbeginn


def is_edit_locked(weight_class: WeightClass) -> bool:
    """Editier-Sperre: Tipps sind nur bis 30 Minuten vor kampfbeginn aenderbar."""
    return datetime.now() >= weight_class.kampfbeginn - EDIT_CUTOFF


def to_out(weight_class: WeightClass) -> WeightClassOut:
    out = WeightClassOut.model_validate(weight_class)
    out.locked = is_locked(weight_class)
    return out


@router.get("", response_model=list[WeightClassOut])
def list_weight_classes(tag: date | None = None, db: Session = Depends(get_db)):
    query = db.query(WeightClass)
    if tag is not None:
        query = query.filter(WeightClass.tag == tag)
    weight_classes = query.order_by(WeightClass.kampfbeginn).all()
    return [to_out(wc) for wc in weight_classes]


@router.get("/{weight_class_id}", response_model=WeightClassOut)
def get_weight_class(weight_class_id: int, db: Session = Depends(get_db)):
    wc = db.get(WeightClass, weight_class_id)
    if wc is None:
        raise HTTPException(status_code=404, detail="Gewichtsklasse nicht gefunden")
    return to_out(wc)


@router.get("/{weight_class_id}/athletes", response_model=list[AthleteOut])
def list_athletes(weight_class_id: int, db: Session = Depends(get_db)):
    wc = db.get(WeightClass, weight_class_id)
    if wc is None:
        raise HTTPException(status_code=404, detail="Gewichtsklasse nicht gefunden")
    athletes = db.query(Athlete).filter(Athlete.weight_class_id == weight_class_id).all()
    return sorted(athletes, key=lambda a: athlete_surname_key(a.name))
