from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Result, Tip, User
from app.schemas import LeaderboardEntry
from app.scoring import score_tip

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


def compute_leaderboard(db: Session) -> list[LeaderboardEntry]:
    results_by_class = {r.weight_class_id: r for r in db.query(Result).all()}

    points_by_user: dict[int, int] = {}
    for tip in db.query(Tip).all():
        result = results_by_class.get(tip.weight_class_id)
        if result is None:
            continue
        points_by_user[tip.user_id] = points_by_user.get(tip.user_id, 0) + score_tip(tip, result)

    entries = [
        LeaderboardEntry(user_id=user.id, name=user.name, points=points_by_user.get(user.id, 0))
        for user in db.query(User).all()
    ]
    entries.sort(key=lambda e: e.points, reverse=True)
    return entries


@router.get("", response_model=list[LeaderboardEntry])
def get_leaderboard(db: Session = Depends(get_db)):
    return compute_leaderboard(db)
