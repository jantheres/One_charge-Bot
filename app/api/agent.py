
from fastapi import APIRouter, HTTPException, Query
from typing import List
from app.models.schemas import SessionFullDetails, TicketSummary, UpdateTicketStatusRequest
from app.services.db import (
    get_session_transcript,
    list_open_tickets,
    mark_session_resolved,
    update_ticket_status,
)

router = APIRouter()

@router.get("/escalations", response_model=List[TicketSummary], tags=["Agent Dashboard"])
async def get_escalations():
    """Returns a list of all open agent tickets (escalations/service)."""
    try:
        items = list_open_tickets()
        # Normalize output to what the dashboard expects
        normalized = []
        for t in items:
            normalized.append(
                {
                    "id": t["id"],
                    "session_id": t["session_id"],
                    "user_id": str(t["user_id"]),
                    "source": t.get("source") or "ESCALATION",
                    "reason": t.get("reason") or "STANDARD",
                    "priority": t.get("priority") or "normal",
                    "status": t.get("status") or "OPEN",
                    "customer_name": t.get("customer_name"),
                    "phone": t.get("phone"),
                    "vehicle_model": t.get("vehicle_model"),
                    "collected_data": t.get("collected_data") or {},
                    "created_at": t.get("created_at"),
                }
            )
        return normalized
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session/{session_id}", response_model=SessionFullDetails, tags=["Agent Dashboard"])
async def get_session(session_id: str):
    """Returns the full metadata and chat history for a specific session."""
    try:
        data = get_session_transcript(session_id)
        if not data:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")
        
        # Transcript in SessionFullDetails expects 'transcript' field
        return SessionFullDetails(
            session_id=data['session_id'],
            customer_id=data['customer_id'],
            current_flow_step=data['current_flow_step'],
            extracted_data=data['extracted_data'],
            transcript=data['messages']
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/session/{session_id}/resolve", tags=["Agent Dashboard"])
async def resolve_session(session_id: str):
    """Marks a session as RESOLVED in the database."""
    try:
        success = mark_session_resolved(session_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found or already closed.")
        
        return {"message": f"Ticket #{session_id} successfully marked as RESOLVED."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/ticket/{ticket_id}/status", tags=["Agent Dashboard"])
async def patch_ticket_status(
    ticket_id: int,
    req: UpdateTicketStatusRequest,
    source: str = Query(default="ESCALATION"),
):
    """
    Update ticket lifecycle status. `source` is accepted for dashboard compatibility.
    """
    try:
        ok = update_ticket_status(ticket_id, req.status)
        if not ok:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return {"message": "Ticket updated", "id": ticket_id, "source": source, "status": req.status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
