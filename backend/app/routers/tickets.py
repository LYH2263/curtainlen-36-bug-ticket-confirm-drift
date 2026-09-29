from fastapi import APIRouter, HTTPException

from app.modules import TicketError
from app.schemas.estimate import TicketIssueRequest
from app.services import ticket_service

router = APIRouter()


@router.post("/tickets")
def issue(body: TicketIssueRequest):
    try:
        return ticket_service.issue_ticket(body.window_id, body.fabric_id)
    except TicketError as e:
        raise HTTPException(e.status_code, e.detail)


@router.post("/tickets/{ticket_no}/confirm")
def confirm(ticket_no: str):
    try:
        return ticket_service.confirm_ticket(ticket_no)
    except TicketError as e:
        raise HTTPException(e.status_code, e.detail)
