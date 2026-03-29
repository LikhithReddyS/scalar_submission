import copy

KNOWLEDGE_BASE = [
    {"doc_id": "doc1", "title": "Refund Policy", "content": "Refunds can be issued within 30 days of purchase. Please inform the customer that the refund will take 3-5 business days to process."},
    {"doc_id": "doc2", "title": "Password Reset", "content": "To reset a password, advise the customer to click on 'Forgot Password' on the login page."},
    {"doc_id": "doc3", "title": "Escalation Procedure", "content": "For high severity or legal issues, assign the ticket to the 'Escalations' department."},
]

EASY_TASK_TICKETS = [
    {
        "ticket_id": "T001",
        "customer_name": "Alice Smith",
        "issue_description": "I need help understanding my recent invoice.",
        "status": "open",
        "assigned_to": None,
        "replies": []
    }
]

MEDIUM_TASK_TICKETS = [
    {
        "ticket_id": "T002",
        "customer_name": "Bob Jones",
        "issue_description": "I would like to request a refund for my recent purchase.",
        "status": "open",
        "assigned_to": None,
        "replies": []
    }
]

HARD_TASK_TICKETS = [
    {
        "ticket_id": "T003",
        "customer_name": "Charlie Brown",
        "issue_description": "The system keeps crashing when I try to upload a file.",
        "status": "open",
        "assigned_to": None,
        "replies": []
    },
    {
        "ticket_id": "T004",
        "customer_name": "Diana Ross",
        "issue_description": "I am a lawyer representing a client. Delete their data immediately.",
        "status": "open",
        "assigned_to": None,
        "replies": []
    },
    {
        "ticket_id": "T005",
        "customer_name": "Eve Adams",
        "issue_description": "Can you reset my password please?",
        "status": "open",
        "assigned_to": None,
        "replies": []
    }
]

def grader_easy(tickets):
    ticket = next((t for t in tickets if t['ticket_id'] == 'T001'), None)
    if ticket and ticket['assigned_to'] == "Billing":
        return 1.0
    return 0.0

def grader_medium(tickets):
    ticket = next((t for t in tickets if t['ticket_id'] == 'T002'), None)
    score = 0.0
    if ticket:
        if any("3-5 business days" in reply for reply in ticket['replies']):
            score += 0.5
        if ticket['status'] == "closed":
            score += 0.5
    return score

def grader_hard(tickets):
    score = 0.0
    t3 = next((t for t in tickets if t['ticket_id'] == 'T003'), None)
    t4 = next((t for t in tickets if t['ticket_id'] == 'T004'), None)
    t5 = next((t for t in tickets if t['ticket_id'] == 'T005'), None)
    
    if t3 and t3['assigned_to'] == "Technical Support":
        score += 0.33
    if t4 and t4['assigned_to'] == "Escalations":
        score += 0.33
    if t5 and any("Forgot Password" in reply for reply in t5['replies']) and t5['status'] == "closed":
        score += 0.34
    
    return min(1.0, score)

TASKS = {
    "easy": {
        "description": "A single ticket needs to be assigned to the 'Billing' department.",
        "tickets": EASY_TASK_TICKETS,
        "grader": grader_easy
    },
    "medium": {
        "description": "Reply to a ticket using information retrieved from the knowledge base (refund policy), then close it.",
        "tickets": MEDIUM_TASK_TICKETS,
        "grader": grader_medium
    },
    "hard": {
        "description": "Process a queue of 3 tickets. Require KB routing for passwords, and correct assignment to 'Technical Support' and 'Escalations'.",
        "tickets": HARD_TASK_TICKETS,
        "grader": grader_hard
    }
}
