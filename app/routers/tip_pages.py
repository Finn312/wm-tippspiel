from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth import get_current_user_optional
from app.database import get_db
from app.models import Athlete, Tip, User, WeightClass
from app.routers.tips import apply_tip
from app.routers.weight_classes import is_edit_locked
from app.schemas import TipIn
from app.templating import templates

router = APIRouter(tags=["tip-pages"])


def _form_context(db: Session, wc: WeightClass, current_user: User) -> dict:
    athletes = db.query(Athlete).filter(Athlete.weight_class_id == wc.id).all()
    tip = (
        db.query(Tip)
        .filter(Tip.weight_class_id == wc.id, Tip.user_id == current_user.id)
        .first()
    )
    return {
        "id": wc.id,
        "name": wc.name,
        "tag": wc.tag.isoformat(),
        "kampfbeginn_iso": wc.kampfbeginn.isoformat(),
        "locked": is_edit_locked(wc),
        "athletes": athletes,
        "tip": tip,
    }


@router.get("/weight-classes/{weight_class_id}/tip")
def tip_form_page(
    weight_class_id: int,
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    if current_user is None:
        return RedirectResponse(url="/login", status_code=303)
    wc = db.get(WeightClass, weight_class_id)
    if wc is None:
        raise HTTPException(status_code=404, detail="Gewichtsklasse nicht gefunden")

    context = _form_context(db, wc, current_user)
    return templates.TemplateResponse(
        "tip_form.html",
        {"request": request, "current_user": current_user, "wc": context, "athletes": context["athletes"], "tip": context["tip"], "success": False, "error": None},
    )


@router.post("/weight-classes/{weight_class_id}/tip")
def tip_form_submit(
    weight_class_id: int,
    request: Request,
    platz_1: str = Form(""),
    platz_2: str = Form(""),
    platz_3a: str = Form(""),
    platz_3b: str = Form(""),
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    if current_user is None:
        return RedirectResponse(url="/login", status_code=303)
    wc = db.get(WeightClass, weight_class_id)
    if wc is None:
        raise HTTPException(status_code=404, detail="Gewichtsklasse nicht gefunden")

    tip_in = TipIn(
        platz_1=int(platz_1) if platz_1 else None,
        platz_2=int(platz_2) if platz_2 else None,
        platz_3a=int(platz_3a) if platz_3a else None,
        platz_3b=int(platz_3b) if platz_3b else None,
    )

    error = None
    try:
        apply_tip(db, wc, current_user, tip_in)
    except HTTPException as exc:
        error = exc.detail

    context = _form_context(db, wc, current_user)
    return templates.TemplateResponse(
        "_tip_form_fragment.html",
        {
            "request": request,
            "wc": context,
            "athletes": context["athletes"],
            "tip": context["tip"],
            "success": error is None,
            "error": error,
        },
    )
