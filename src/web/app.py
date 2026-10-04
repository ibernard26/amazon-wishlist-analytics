"""
FastAPI Application Entrypoint
Serves REST API, Dashboard HTML Templates, and Static Assets.
"""
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from src.config import settings
from src.database.connection import init_db, get_db, get_db_context
from src.database.models import WishlistItem
from src.sync.sample_data import seed_sample_database
from src.web.api_routes import router as api_router

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern lifespan handler: initialize DB and seed initial dataset if empty."""
    init_db()
    with get_db_context() as db:
        item_count = db.query(WishlistItem).count()
        if item_count == 0:
            print("🌱 First-time initialization: seeding database with sample Amazon Wishlist items & 30-day trends...")
            seed_sample_database(db)
            print("✅ Database ready with full visualization trends!")
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Intelligent Amazon Wishlist Analytics & Shopping Cart Execution Platform",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include API Router
app.include_router(api_router)


@app.get("/", response_class=HTMLResponse)
def render_dashboard(request: Request, db: Session = Depends(get_db)):
    """Render the main interactive dashboard."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": settings.app_name,
            "version": settings.version,
            "max_budget": settings.max_single_order_budget
        }
    )
