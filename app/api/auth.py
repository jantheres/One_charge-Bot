
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
    # Validate phone is not empty
    if not request.phone or not request.phone.strip():
        raise HTTPException(status_code=400, detail="Phone number is required")
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database service unavailable")
    
    user = None
    role = "user"
    
    # Simple Admin Logic for MVP - agent can login without being in customers table
    if request.phone == "9999999999":
        access_token = create_access_token({
            "sub": request.phone,
            "role": "agent",
            "name": "Support Agent",
        })
        return {"access_token": access_token, "token_type": "bearer"}
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM customers WHERE phone = %s", (request.phone,))
        user = cursor.fetchone()
        cursor.close()
    finally:
        conn.close()
    
    # Reject unregistered phone numbers
    if not user:
        raise HTTPException(status_code=401, detail="Phone number not registered. Please contact support.")
    
    token_data = {
        "sub": request.phone,
        "role": "user",
        "user_id": user["id"],
        "name": user.get("name", "User"),
        "vehicle_model": user.get("vehicle_model", ""),
    }
        
    access_token = create_access_token(token_data)
    return {"access_token": access_token, "token_type": "bearer"}

