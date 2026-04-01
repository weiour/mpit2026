from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.events import router as events_router
from app.api.gift_search import router as gift_search_router
from app.api.recommendations import router as recommendations_router
from app.api.wishlist import router as wishlist_router
from app.api.invitations import router as invitations_router, public_router as invitations_public_router
from app.core.database import Base, engine

from app.models import chat, event, user, wishlist, invitation  # noqa: F401


Base.metadata.create_all(bind=engine)

try:
    with engine.begin() as conn:
        for statement in [
            "ALTER TABLE events ADD COLUMN google_calendar_link TEXT",
            "ALTER TABLE events ADD COLUMN google_calendar_error TEXT",
            "ALTER TABLE events ADD COLUMN guest_emails TEXT",
            "ALTER TABLE events ADD COLUMN city TEXT",
            "ALTER TABLE events ADD COLUMN status TEXT",
            "ALTER TABLE events ADD COLUMN venue_mode TEXT",
            "ALTER TABLE events ADD COLUMN selected_option TEXT",
            "ALTER TABLE events ADD COLUMN selected_option_kind TEXT",
            "ALTER TABLE users ADD COLUMN region TEXT",
        ]:
            try:
                conn.exec_driver_sql(statement)
            except Exception:
                pass
except Exception:
    pass

app = FastAPI(title="Birthday AI Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(events_router)
app.include_router(chat_router)
app.include_router(recommendations_router)
app.include_router(wishlist_router)
app.include_router(gift_search_router)
app.include_router(invitations_router)
app.include_router(invitations_public_router)


@app.get("/")
def root():
    return {"status": "ok"}
