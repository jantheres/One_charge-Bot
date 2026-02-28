
import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router
from app.api.agent import router as agent_router
from app.services.db import setup_db

app = FastAPI(title="1Charge Chatbot API")

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

@app.on_event("startup")
async def startup_event():
    try:
        setup_db()
    except Exception as e:
        print(f"DB Setup error: {e}")

@app.get("/health")
async def health():
    return {"status": "online", "project": "1Charge"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(chat_router, prefix="/api")
app.include_router(agent_router, prefix="/api/agent")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
