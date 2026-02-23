
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

# Import Routers
from app.api import auth, chat, agent
# Assuming we create app.api modules for chat and agent logic next.
# Wait, I haven't created app/api/chat.py or app/api/agent.py properly yet?
# Step 7 was ambiguous.
# I will create main.py assuming they exist (I will create them next).

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
# (Using placeholder logic if files not populated fully yet, but structure is here)
from app.api.auth import router as auth_router
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth")

from app.api.chat import router as chat_router
app.include_router(chat_router, prefix=f"{settings.API_V1_STR}/chatbot")

from app.api.agent import router as agent_router
app.include_router(agent_router, prefix=f"{settings.API_V1_STR}/agent")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
