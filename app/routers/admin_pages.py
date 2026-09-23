import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth import ADMIN_COOKIE, ADMIN_SECRET, is_admin_request
from app.database import get_db
from app.models import Athlete, Result, Tip, User, WeightClass
from app.schemas import ResultIn
from app.templating import templates
from app.validation import validate_athlete_slots

router = APIRouter(prefix="/admin", tags=["admin-pages"])


def _result_context(db: Session, wc: WeightClass) -> dict:
    return {
        "id": wc.id,
        "name": wc.name,
        "tag": wc.tag.isoformat(),
        "athletes": db.query(Athlete).filter(Athlete.weight_class_id == wc.id).all(),
        "result": db.get(Result, wc.id),
        "success": False,
        "error": None,
    }


@router.get("/login")
def admin_login_page(request: Request):
    if is_admin_request(request):
        return RedirectResponse(url="/admin", status_code=303)
    return templates.TemplateResponse("admin_login.html", {"request": request, "current_user": None, "error": None})


@router.post("/login")
def admin_login_submit(request: Request, secret: str = Form(...)):
    if secret != ADMIN_SECRET:
        return templates.TemplateResponse(
            "admin_login.html",
            {"request": request, "current_user": None, "error": "Falsches Secret"},
            status_code=401,
        )
    response = RedirectResponse(url="/admin", status_code=303)
    response.set_cookie(ADMIN_COOKIE, secret, httponly=True, samesite="lax")
    return response


@router.get("")
def admin_page(request: Request, db: Session = Depends(get_db)):
    if not is_admin_request(request):
        return RedirectResponse(url="/admin/login", status_code=303)
    weight_classes_db = db.query(WeightClass).order_by(WeightClass.kampfbeginn).all()
    weight_classes = [_result_context(db, wc) for wc in weight_classes_db]
    return templates.TemplateResponse(
        "admin.html", {"request": request, "current_user": None, "weight_classes": weight_classes}
    )


@router.post("/results/{weight_class_id}")
def admin_result_submit(
    weight_class_id: int,
    request: Request,
    platz_1: str = Form(""),
    platz_2: str = Form(""),
    platz_3a: str = Form(""),
    platz_3b: str = Form(""),
    db: Session = Depends(get_db),
):
    if not is_admin_request(request):
        return RedirectResponse(url="/admin/login", status_code=303)

    wc = db.get(WeightClass, weight_class_id)
    if wc is None:
        raise HTTPException(status_code=404, detail="Gewichtsklasse nicht gefunden")

    result_in = ResultIn(
        platz_1=int(platz_1) if platz_1 else None,
        platz_2=int(platz_2) if platz_2 else None,
        platz_3a=int(platz_3a) if platz_3a else None,
        platz_3b=int(platz_3b) if platz_3b else None,
    )

    error = None
    try:
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
    except HTTPException as exc:
        db.rollback()
        error = exc.detail

    context = _result_context(db, wc)
    context["success"] = error is None
    context["error"] = error
    return templates.TemplateResponse("_admin_result_fragment.html", {"request": request, "wc": context})


def _wc_edit_context(wc: WeightClass, success: bool = False, error: str | None = None) -> dict:
    return {
        "id": wc.id,
        "name": wc.name,
        "kampfbeginn_input": wc.kampfbeginn.strftime("%Y-%m-%dT%H:%M"),
        "success": success,
        "error": error,
    }


@router.get("/users")
def admin_users_page(request: Request, db: Session = Depends(get_db)):
    if not is_admin_request(request):
        return RedirectResponse(url="/admin/login", status_code=303)
    users = db.query(User).order_by(User.name).all()
    return templates.TemplateResponse(
        "admin_users.html", {"request": request, "current_user": None, "users": users, "error": None}
    )


@router.post("/users")
def admin_users_create(request: Request, name: str = Form(...), db: Session = Depends(get_db)):
    if not is_admin_request(request):
        return RedirectResponse(url="/admin/login", status_code=303)

    name = name.strip()
    error = None
    if not name:
        error = "Name darf nicht leer sein"
    elif len(name) > 50:
        error = "Name ist zu lang (max. 50 Zeichen)"
    elif db.query(User).filter(User.name == name).first() is not None:
        error = "Name ist bereits vergeben"

    if not error:
        db.add(User(name=name, pin=None))
        db.commit()

    users = db.query(User).order_by(User.name).all()
    return templates.TemplateResponse(
        "admin_users.html", {"request": request, "current_user": None, "users": users, "error": error}
    )


@router.post("/users/{user_id}/delete")
def admin_users_delete(user_id: int, request: Request, db: Session = Depends(get_db)):
    if not is_admin_request(request):
        return RedirectResponse(url="/admin/login", status_code=303)

    user = db.get(User, user_id)
    error = None
    if user is None:
        error = "Nutzer nicht gefunden"
    else:
        db.query(Tip).filter(Tip.user_id == user.id).delete(synchronize_session=False)
        db.delete(user)
        db.commit()

    users = db.query(User).order_by(User.name).all()
    return templates.TemplateResponse(
        "admin_users.html", {"request": request, "current_user": None, "users": users, "error": error}
    )


@router.get("/weight-classes")
def admin_weight_classes_page(request: Request, db: Session = Depends(get_db)):
    if not is_admin_request(request):
        return RedirectResponse(url="/admin/login", status_code=303)
    weight_classes_db = db.query(WeightClass).order_by(WeightClass.kampfbeginn).all()
    weight_classes = [_wc_edit_context(wc) for wc in weight_classes_db]
    return templates.TemplateResponse(
        "admin_weight_classes.html", {"request": request, "current_user": None, "weight_classes": weight_classes}
    )


@router.post("/weight-classes/{weight_class_id}")
def admin_weight_class_submit(
    weight_class_id: int,
    request: Request,
    kampfbeginn: str = Form(...),
    db: Session = Depends(get_db),
):
    if not is_admin_request(request):
        return RedirectResponse(url="/admin/login", status_code=303)

    wc = db.get(WeightClass, weight_class_id)
    if wc is None:
        raise HTTPException(status_code=404, detail="Gewichtsklasse nicht gefunden")

    error = None
    try:
        parsed = datetime.strptime(kampfbeginn, "%Y-%m-%dT%H:%M")
    except ValueError:
        error = "Ungueltiges Datum/Uhrzeit-Format"
    else:
        wc.kampfbeginn = parsed
        wc.tag = parsed.date()
        db.commit()
        db.refresh(wc)

    context = _wc_edit_context(wc, success=error is None, error=error)
    return templates.TemplateResponse("_admin_weight_class_fragment.html", {"request": request, "wc": context})


@router.get("/athletes/import")
def athlete_import_page(request: Request):
    if not is_admin_request(request):
        return RedirectResponse(url="/admin/login", status_code=303)
    return templates.TemplateResponse(
        "admin_athlete_import.html", {"request": request, "current_user": None, "result": None}
    )


@router.post("/athletes/import")
def athlete_import_submit(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not is_admin_request(request):
        return RedirectResponse(url="/admin/login", status_code=303)

    raw = file.file.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(raw))

    weight_classes = {wc.name: wc for wc in db.query(WeightClass).all()}

    created = 0
    updated = 0
    unmatched: dict[str, int] = {}

    for row in reader:
        wc_name = (row.get("weight_class") or "").strip()
        wc = weight_classes.get(wc_name)
        if wc is None:
            unmatched[wc_name] = unmatched.get(wc_name, 0) + 1
            continue

        name = (row.get("name") or "").strip()
        if not name:
            continue

        rank_raw = (row.get("wrl_rank") or "").strip().lstrip("#")
        wrl_rank = int(rank_raw) if rank_raw.isdigit() else None

        athlete = (
            db.query(Athlete)
            .filter(Athlete.weight_class_id == wc.id, Athlete.name == name)
            .first()
        )
        if athlete is None:
            athlete = Athlete(weight_class_id=wc.id, name=name)
            db.add(athlete)
            created += 1
        else:
            updated += 1

        athlete.nation = (row.get("nation") or "").strip() or None
        athlete.nation_code = (row.get("nation_code") or "").strip() or None
        athlete.gender = (row.get("gender") or "").strip() or None
        athlete.wrl_rank = wrl_rank

    db.commit()

    result = {"created": created, "updated": updated, "unmatched": unmatched}
    return templates.TemplateResponse(
        "admin_athlete_import.html", {"request": request, "current_user": None, "result": result}
    )
