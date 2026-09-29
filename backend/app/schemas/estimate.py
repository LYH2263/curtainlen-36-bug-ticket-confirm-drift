from pydantic import BaseModel

class EstimateRequest(BaseModel):
    window_id: int
    fabric_id: int
    save: bool = False
    note: str = ""


class TicketIssueRequest(BaseModel):
    window_id: int
    fabric_id: int
