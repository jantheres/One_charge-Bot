
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

# Import Routers
from app.api.chat import router as chat_router
from app.api.agent import router as agent_router

app = FastAPI(title=settings.PROJECT_NAME)

@app.get("/health", tags=["Root"])
async def health():
    from app.db.connection import get_db_connection
    from app.core.ai import client
    
    db_ok = False
    db_error = None
    try:
        conn = get_db_connection()
        if conn:
            db_ok = True
            conn.close()
    except Exception as e:
        db_error = str(e)
    
    return {
        "status": "online",
        "ai_client_active": client is not None,
        "openai_key_configured": bool(settings.OPENAI_API_KEY),
        "openai_key_preview": f"{settings.OPENAI_API_KEY[:6]}...{settings.OPENAI_API_KEY[-4:]}" if settings.OPENAI_API_KEY else "MISSING",
        "database_connected": db_ok,
        "database_error": db_error,
        "db_config": {
            "host": settings.DB_HOST,
            "user": settings.DB_USER,
            "db": settings.DB_NAME,
            "port": settings.DB_PORT
        }
    }

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(chat_router, prefix=f"{settings.API_V1_STR}/chatbot")
app.include_router(agent_router, prefix=f"{settings.API_V1_STR}/agent")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
