
from fastapi import APIRouter, HTTPException, Depends, Request
from app.models.schemas import StatusUpdate
from app.core.security import verify_agent
from app.services.ticket_service import TicketService

router = APIRouter()

@router.get("/escalations", tags=["Agent Dashboard"], summary="Get Active Tickets", response_description="List of requests and escalations")
async def get_escalations():
    """
    Fetch all **Active** tickets (Requests & Escalations).
    
    Includes tickets with status: `OPEN`, `IN_PROGRESS`, `DISPATCHED`, `ON_SITE`.
    Does **NOT** include `RESOLVED` tickets (unless modified).
    """
    items = TicketService.get_open_tickets()
    if items is None:
         raise HTTPException(status_code=500, detail="DB Error")
    return items
        
@router.patch("/ticket/{item_id}/status", tags=["Agent Dashboard"], summary="Update Ticket Status")
async def update_status(item_id: int, update: StatusUpdate, request: Request):
    """
    Transition a ticket to a new status.
    
    *   **source**: Query param 'REQUEST' or 'ESCALATION' (default).
    *   **status**: One of `OPEN`, `IN_PROGRESS`, `DISPATCHED`, `ON_SITE`, `RESOLVED`, `CLOSED`.
    """
    source = request.query_params.get('source', 'ESCALATION')
    success = TicketService.update_ticket_status(item_id, source, update.status.upper())
    
    if success:
        return {"message": f"Updated ticket {item_id} to {update.status.upper()}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update ticket")
