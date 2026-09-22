from fastapi import FastAPI

from app.auth import router as auth_router
from app.routers.admin_pages import router as admin_pages_router
from app.routers.leaderboard import router as leaderboard_router
from app.routers.pages import router as pages_router
from app.routers.results import router as results_router
from app.routers.tip_pages import router as tip_pages_router
from app.routers.tips import router as tips_router
from app.routers.users import router as users_router
from app.routers.weight_classes import router as weight_classes_router

app = FastAPI(title="Judo-WM Tippspiel")

# JSON-API
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(weight_classes_router, prefix="/api")
app.include_router(tips_router, prefix="/api")
app.include_router(results_router, prefix="/api")
app.include_router(leaderboard_router, prefix="/api")

# Server-gerenderte Seiten (Jinja2 + htmx)
app.include_router(pages_router)
app.include_router(tip_pages_router)
app.include_router(admin_pages_router)


@app.get("/health")
def health():
    return {"status": "ok"}
