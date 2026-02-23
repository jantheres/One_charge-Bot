
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

# Import Routers
from app.api.chat import router as chat_router
from app.api.agent import router as agent_router

app = FastAPI(title=settings.PROJECT_NAME)

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to the 1Charge Chatbot API. Visit /docs for documentation."}

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
