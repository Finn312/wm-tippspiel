import re
from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth import SESSION_COOKIE, TOKEN_MAX_AGE, create_token, get_current_user_optional
from app.database import get_db
from app.models import Athlete, Result, Tip, User, WeightClass
from app.routers.leaderboard import compute_leaderboard
from app.routers.weight_classes import is_edit_locked, is_locked
from app.scoring import score_tip
from app.templating import templates

router = APIRouter(tags=["pages"])

PIN_PATTERN = re.compile(r"^\d{4}$")

WM_START = date(2026, 10, 4)
WM_END = date(2026, 10, 11)


def _wc_context(db: Session, wc: WeightClass, current_user: User | None) -> dict:
    """Kontext fuer die Tipp-Tabelle einer Gewichtsklasse.

    Vor Kampfbeginn ist nur der eigene Tipp mit Inhalt sichtbar - alle anderen
    Zeilen (auch fuer nicht eingeloggte Besucher) zeigen nur, dass ueberhaupt
    getippt wurde, ohne die Auswahl preiszugeben. Nach Kampfbeginn ist alles
    fuer alle sichtbar, auch ohne Login.
    """
    locked = is_locked(wc)
    tips = db.query(Tip).filter(Tip.weight_class_id == wc.id).all()
    result = db.get(Result, wc.id)

    athletes = {a.id: a.name for a in db.query(Athlete).filter(Athlete.weight_class_id == wc.id).all()}
    users = {u.id: u.name for u in db.query(User).all()}

    tip_rows = []
    my_tip = None
    for t in tips:
        is_own = current_user is not None and t.user_id == current_user.id
        visible = locked or is_own
        row = {
            "user_id": t.user_id,
            "user_name": users.get(t.user_id, "?"),
            "visible": visible,
        }
        if visible:
            row.update(
                {
                    "platz_1_name": athletes.get(t.platz_1),
                    "platz_2_name": athletes.get(t.platz_2),
                    "platz_3a_name": athletes.get(t.platz_3a),
                    "platz_3b_name": athletes.get(t.platz_3b),
                    "points": score_tip(t, result) if result else None,
                }
            )
        tip_rows.append(row)
        if is_own:
            my_tip = row

    return {
        "id": wc.id,
        "name": wc.name,
        "tag": wc.tag.isoformat(),
        "kampfbeginn_iso": wc.kampfbeginn.isoformat(),
        "locked": locked,
        "tip_rows": tip_rows,
        "show_points": result is not None,
        "my_tip": my_tip,
        "logged_in": current_user is not None,
        "editable": not is_edit_locked(wc),
    }


@router.get("/")
def root():
    today = date.today()
    target = today if WM_START <= today <= WM_END else WM_START
    return RedirectResponse(url=f"/day/{target.isoformat()}", status_code=303)


@router.get("/info")
def info_page(
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
):
    return templates.TemplateResponse("info.html", {"request": request, "current_user": current_user})


@router.get("/login")
def login_page(
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    if current_user is not None:
        return RedirectResponse(url="/", status_code=303)
    users = db.query(User).order_by(User.name).all()
    return templates.TemplateResponse("login.html", {"request": request, "current_user": None, "users": users})


@router.get("/login/{user_id}")
def login_user_page(
    user_id: int,
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    if current_user is not None:
        return RedirectResponse(url="/", status_code=303)
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Nutzer nicht gefunden")
    return templates.TemplateResponse(
        "login_user.html",
        {"request": request, "current_user": None, "user": user, "has_pin": user.pin is not None, "error": None},
    )


@router.post("/login/{user_id}")
def login_user_submit(
    user_id: int,
    request: Request,
    pin: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Nutzer nicht gefunden")

    error = None
    if user.pin is None:
        if not PIN_PATTERN.match(pin):
            error = "PIN muss genau 4 Ziffern haben"
        else:
            user.pin = pin
            db.commit()
    elif pin != user.pin:
        error = "Falsche PIN"

    if error:
        return templates.TemplateResponse(
            "login_user.html",
            {
                "request": request,
                "current_user": None,
                "user": user,
                "has_pin": user.pin is not None,
                "error": error,
            },
            status_code=401,
        )

    token = create_token(user.id)
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=TOKEN_MAX_AGE)
    return response


@router.post("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE)
    return response


@router.get("/day/{tag}")
def day_view(
    tag: date,
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    weight_classes_db = (
        db.query(WeightClass).filter(WeightClass.tag == tag).order_by(WeightClass.kampfbeginn).all()
    )
    weight_classes = [_wc_context(db, wc, current_user) for wc in weight_classes_db]
    return templates.TemplateResponse(
        "day.html",
        {"request": request, "current_user": current_user, "tag": tag.isoformat(), "weight_classes": weight_classes},
    )


@router.get("/partials/weight-classes/{weight_class_id}/tips")
def partial_wc_tips(
    weight_class_id: int,
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    wc = db.get(WeightClass, weight_class_id)
    if wc is None:
        raise HTTPException(status_code=404, detail="Gewichtsklasse nicht gefunden")
    ctx = _wc_context(db, wc, current_user)
    return templates.TemplateResponse("_tips_fragment.html", {"request": request, "wc": ctx})


@router.get("/my-tips")
def my_tips_page(
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    if current_user is None:
        return RedirectResponse(url="/login", status_code=303)

    weight_classes = db.query(WeightClass).order_by(WeightClass.kampfbeginn).all()
    rows = []
    for wc in weight_classes:
        t = (
            db.query(Tip)
            .filter(Tip.weight_class_id == wc.id, Tip.user_id == current_user.id)
            .first()
        )
        tip_out = None
        if t is not None:
            athletes = {
                a.id: a.name
                for a in db.query(Athlete).filter(Athlete.weight_class_id == wc.id).all()
            }
            tip_out = {
                "platz_1_name": athletes.get(t.platz_1),
                "platz_2_name": athletes.get(t.platz_2),
                "platz_3a_name": athletes.get(t.platz_3a),
                "platz_3b_name": athletes.get(t.platz_3b),
            }

        rows.append(
            {
                "id": wc.id,
                "name": wc.name,
                "editable": not is_edit_locked(wc),
                "tip": tip_out,
            }
        )

    return templates.TemplateResponse(
        "my_tips.html", {"request": request, "current_user": current_user, "rows": rows}
    )


@router.get("/users/{user_id}")
def user_detail(
    user_id: int,
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    target_user = db.get(User, user_id)
    if target_user is None:
        raise HTTPException(status_code=404, detail="Nutzer nicht gefunden")

    weight_classes = db.query(WeightClass).order_by(WeightClass.kampfbeginn).all()
    rows = []
    for wc in weight_classes:
        locked = is_locked(wc)
        is_owner = current_user is not None and target_user.id == current_user.id
        visible = locked or is_owner

        t = (
            db.query(Tip)
            .filter(Tip.weight_class_id == wc.id, Tip.user_id == target_user.id)
            .first()
        )

        tip_out = None
        points = None
        if visible and t is not None:
            athletes = {
                a.id: a.name
                for a in db.query(Athlete).filter(Athlete.weight_class_id == wc.id).all()
            }
            tip_out = {
                "platz_1_name": athletes.get(t.platz_1),
                "platz_2_name": athletes.get(t.platz_2),
                "platz_3a_name": athletes.get(t.platz_3a),
                "platz_3b_name": athletes.get(t.platz_3b),
            }
            result = db.get(Result, wc.id)
            if result is not None:
                points = score_tip(t, result)

        rows.append(
            {
                "wc_name": wc.name,
                "visible": visible,
                "has_tip": t is not None,
                "tip": tip_out,
                "points": points,
            }
        )

    return templates.TemplateResponse(
        "user_detail.html",
        {"request": request, "current_user": current_user, "target_user": target_user, "rows": rows},
    )


@router.get("/leaderboard")
def leaderboard_page(
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    entries = compute_leaderboard(db)
    return templates.TemplateResponse(
        "leaderboard.html", {"request": request, "current_user": current_user, "entries": entries}
    )


@router.get("/partials/leaderboard")
def partial_leaderboard(
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    entries = compute_leaderboard(db)
    return templates.TemplateResponse("_leaderboard_fragment.html", {"request": request, "entries": entries})
