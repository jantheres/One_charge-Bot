
from fastapi import APIRouter, HTTPException, Depends
from app.db.connection import get_db_connection
from app.models.schemas import LoginRequest, Token
from app.core.security import create_access_token

router = APIRouter()

@router.post("/login", response_model=Token, tags=["Authentication"], summary="User Login", response_description="JWT Access Token")
async def login(request: LoginRequest):
    """
    Authenticate a user via phone number.
    
    *   **phone**: Registered mobile number (e.g., '9876543211')
    
    Returns a short-lived **JWT Bearer Token** for authorized access to Chat and Agent APIs.
    """
    conn = get_db_connection()
    user_id = None
    role = "user"
    
    # Simple Admin Logic for MVP
    if request.phone == "9999999999":
        role = "agent"
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM customers WHERE phone = %s", (request.phone,))
        user = cursor.fetchone()
        if user:
            user_id = user['id']
        else:
            # Auto-register logic (omitted for brevity)
            pass
        cursor.close()
        conn.close()

    token_data = {"sub": request.phone, "role": role}
    if user_id:
        token_data["user_id"] = user_id
        
    access_token = create_access_token(token_data)
    return {"access_token": access_token, "token_type": "bearer"}
