from fastapi.templating import Jinja2Templates

from app.sorting import athlete_display_name

templates = Jinja2Templates(directory="app/templates")
templates.env.filters["athlete_display"] = athlete_display_name
