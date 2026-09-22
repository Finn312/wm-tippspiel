import os

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, LoginResponse, UserOut

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "admin-secret-change-me")
TOKEN_MAX_AGE = 60 * 60 * 24 * 30

SESSION_COOKIE = "session"
ADMIN_COOKIE = "admin_secret"

_serializer = URLSafeTimedSerializer(SECRET_KEY, salt="wm-tips-auth")

router = APIRouter(prefix="/auth", tags=["auth"])


def create_token(user_id: int) -> str:
    return _serializer.dumps({"user_id": user_id})


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.name == payload.name).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unbekannter Name")

    if user.pin:
        if payload.pin != user.pin:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Falsche PIN")

    token = create_token(user.id)
    return LoginResponse(token=token, user=UserOut.model_validate(user))


def _token_from_request(request: Request, authorization: str | None) -> str | None:
    if authorization and authorization.startswith("Bearer "):
        return authorization.removeprefix("Bearer ")
    return request.cookies.get(SESSION_COOKIE)


def _user_from_token(token: str | None, db: Session) -> User | None:
    if not token:
        return None
    try:
        data = _serializer.loads(token, max_age=TOKEN_MAX_AGE)
    except BadSignature:
        return None
    return db.get(User, data["user_id"])


def get_current_user(
    request: Request,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    """Fuer die JSON-API: Bearer-Header oder Session-Cookie, sonst 401."""
    user = _user_from_token(_token_from_request(request, authorization), db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nicht eingeloggt")
    return user


def get_current_user_optional(
    request: Request,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User | None:
    """Fuer HTML-Seiten: liefert None statt 401, damit die Route selbst redirecten kann."""
    return _user_from_token(_token_from_request(request, authorization), db)


def require_admin(x_admin_secret: str | None = Header(default=None)) -> None:
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nicht erlaubt")


def is_admin_request(request: Request) -> bool:
    return request.cookies.get(ADMIN_COOKIE) == ADMIN_SECRET
