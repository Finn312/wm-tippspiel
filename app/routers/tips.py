from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Result, Tip, User, WeightClass
from app.routers.weight_classes import is_edit_locked, is_locked
from app.schemas import TipIn, TipOut
from app.scoring import score_tip
from app.validation import validate_athlete_slots

router = APIRouter(prefix="/tips", tags=["tips"])


def _tip_out(tip: Tip, result: Result | None) -> TipOut:
    out = TipOut.model_validate(tip)
    if result is not None:
        out.points = score_tip(tip, result)
    return out


def visible_tips(db: Session, wc: WeightClass, current_user: User) -> list[Tip]:
    """Tipps einer Gewichtsklasse, wie sie current_user sehen darf.

    Vor Kampfbeginn nur der eigene Tipp, danach alle - serverseitig erzwungen.
    """
    tips = db.query(Tip).filter(Tip.weight_class_id == wc.id).all()
    if not is_locked(wc):
        tips = [t for t in tips if t.user_id == current_user.id]
    return tips


def apply_tip(db: Session, wc: WeightClass, current_user: User, tip_in: TipIn) -> Tip:
    if is_edit_locked(wc):
        raise HTTPException(status_code=403, detail="Tipp-Fenster ist bereits geschlossen")

    validate_athlete_slots(
        [tip_in.platz_1, tip_in.platz_2, tip_in.platz_3a, tip_in.platz_3b],
        wc.id,
        db,
    )

    tip = (
        db.query(Tip)
        .filter(Tip.weight_class_id == wc.id, Tip.user_id == current_user.id)
        .first()
    )
    if tip is None:
        tip = Tip(weight_class_id=wc.id, user_id=current_user.id)
        db.add(tip)

    tip.platz_1 = tip_in.platz_1
    tip.platz_2 = tip_in.platz_2
    tip.platz_3a = tip_in.platz_3a
    tip.platz_3b = tip_in.platz_3b

    db.commit()
    db.refresh(tip)
    return tip


@router.get("/me", response_model=TipOut | None)
def get_my_tip(
    weight_class_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tip = (
        db.query(Tip)
        .filter(Tip.weight_class_id == weight_class_id, Tip.user_id == current_user.id)
        .first()
    )
    if tip is None:
        return None
    result = db.get(Result, weight_class_id)
    return _tip_out(tip, result)


@router.post("", response_model=TipOut)
def upsert_tip(
    weight_class_id: int,
    tip_in: TipIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wc = db.get(WeightClass, weight_class_id)
    if wc is None:
        raise HTTPException(status_code=404, detail="Gewichtsklasse nicht gefunden")

    tip = apply_tip(db, wc, current_user, tip_in)
    return _tip_out(tip, None)


@router.get("/weight-class/{weight_class_id}", response_model=list[TipOut])
def list_tips_for_weight_class(
    weight_class_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wc = db.get(WeightClass, weight_class_id)
    if wc is None:
        raise HTTPException(status_code=404, detail="Gewichtsklasse nicht gefunden")

    tips = visible_tips(db, wc, current_user)
    result = db.get(Result, weight_class_id)

    return [_tip_out(t, result) for t in tips]


@router.get("/day/{tag}")
def list_tips_for_day(
    tag: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    weight_classes = db.query(WeightClass).filter(WeightClass.tag == tag).all()

    day_view = []
    for wc in weight_classes:
        locked = is_locked(wc)
        result = db.get(Result, wc.id)
        tips = visible_tips(db, wc, current_user)

        day_view.append(
            {
                "weight_class_id": wc.id,
                "name": wc.name,
                "kampfbeginn": wc.kampfbeginn,
                "locked": locked,
                "tips": [_tip_out(t, result) for t in tips],
            }
        )

    return day_view
