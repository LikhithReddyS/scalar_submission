from pydantic import BaseModel, Field
from typing import Union, Literal, List, Optional, Dict

class SearchKB(BaseModel):
    action_type: Literal["search_kb"] = "search_kb"
    query: str = Field(description="The search query to look up in the knowledge base.")

class ReplyTicket(BaseModel):
    action_type: Literal["reply_ticket"] = "reply_ticket"
    ticket_id: str = Field(description="The ID of the ticket to reply to.")
    response: str = Field(description="The reply text to send to the customer.")

class AssignTicket(BaseModel):
    action_type: Literal["assign_ticket"] = "assign_ticket"
    ticket_id: str = Field(description="The ID of the ticket to assign.")
    department: Literal["Billing", "Technical Support", "Escalations"] = Field(description="The department to assign the ticket to.")

class CloseTicket(BaseModel):
    action_type: Literal["close_ticket"] = "close_ticket"
    ticket_id: str = Field(description="The ID of the ticket to close.")

class Submit(BaseModel):
    action_type: Literal["submit"] = "submit"
    reason: Optional[str] = Field(default=None, description="Reason for submitting the task.")

class CustomerAction(BaseModel):
    action: Union[SearchKB, ReplyTicket, AssignTicket, CloseTicket, Submit] = Field(..., discriminator='action_type')

class Ticket(BaseModel):
    ticket_id: str
    customer_name: str
    issue_description: str
    status: Literal["open", "closed"]
    assigned_to: Optional[str] = None
    replies: List[str] = []

class CustomObservation(BaseModel):
    feedback: str = Field(description="Feedback from the last action.")
    current_tickets: List[Ticket] = Field(description="List of current tickets in the queue.")
    kb_results: Optional[List[Dict[str, str]]] = Field(default=None, description="Results from the last knowledge base search.")

class CustomReward(BaseModel):
    value: float = Field(description="The reward value from 0.0 to 1.0.")
    reason: str = Field(description="The reason for the reward.")
