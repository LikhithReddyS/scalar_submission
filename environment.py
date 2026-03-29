import copy
from typing import Tuple, Dict, Any, List

from schema import CustomObservation, CustomReward, CustomerAction, Ticket
from tasks import TASKS, KNOWLEDGE_BASE

class CustomerSupportEnv:
    def __init__(self):
        self.current_task_id = "easy"
        self.tickets: List[Ticket] = []
        self.done = False
        self.reset("easy")

    def reset(self, task_name: str = "easy") -> CustomObservation:
        self.current_task_id = task_name if task_name in TASKS else "easy"
        
        # Deepcopy to ensure clean state
        initial_tickets = copy.deepcopy(TASKS[self.current_task_id]["tickets"])
        self.tickets = [Ticket(**t) for t in initial_tickets]
        self.done = False
        
        return CustomObservation(
            feedback="Environment reset. Ready for actions.",
            current_tickets=self.tickets,
            kb_results=None
        )

    def state(self) -> CustomObservation:
        return CustomObservation(
            feedback="Current state.",
            current_tickets=self.tickets,
            kb_results=None
        )

    def step(self, action: CustomerAction) -> Tuple[CustomObservation, CustomReward, bool, Dict[str, Any]]:
        if self.done:
             raise ValueError("Episode is already done. Call reset().")
        
        feedback = ""
        kb_results = None
        reward_val = 0.0
        reason = ""
        done = False
        
        inner_action = action.action
        atype = inner_action.action_type
        
        if atype == "submit":
            self.done = True
            done = True
            
            # Calculate final score using the task's grader
            grader = TASKS[self.current_task_id]["grader"]
            final_score = grader([t.dict() for t in self.tickets])
            
            reward_val = final_score
            reason = f"Task completed. Grader score: {final_score}"
            feedback = "Submitted successfully."
            
        elif atype == "search_kb":
            query = inner_action.query.lower()
            results = [doc for doc in KNOWLEDGE_BASE if query in doc["title"].lower() or query in doc["content"].lower()]
            kb_results = results
            feedback = f"Found {len(results)} results in Knowledge Base."
            # Small intermediate reward for using the KB correctly
            reward_val = 0.01
            reason = "Used Knowledge Base."
            
        elif atype == "reply_ticket":
            t_id = inner_action.ticket_id
            ticket = next((t for t in self.tickets if t.ticket_id == t_id), None)
            if ticket:
                if ticket.status == "closed":
                    feedback = f"Ticket {t_id} is already closed."
                    reward_val = -0.1
                    reason = "Replied to a closed ticket."
                else:
                    ticket.replies.append(inner_action.response)
                    feedback = f"Replied to ticket {t_id}."
                    reward_val = 0.05
                    reason = "Replied to a ticket."
            else:
                feedback = f"Ticket {t_id} not found."
                reward_val = -0.1
                reason = "Invalid ticket ID."
                
        elif atype == "assign_ticket":
            t_id = inner_action.ticket_id
            ticket = next((t for t in self.tickets if t.ticket_id == t_id), None)
            if ticket:
                if ticket.status == "closed":
                    feedback = f"Ticket {t_id} is already closed."
                    reward_val = -0.1
                    reason = "Assigned a closed ticket."
                else:
                    ticket.assigned_to = inner_action.department
                    feedback = f"Assigned ticket {t_id} to {inner_action.department}."
                    reward_val = 0.05
                    reason = "Assigned a ticket."
            else:
                feedback = f"Ticket {t_id} not found."
                reward_val = -0.1
                reason = "Invalid ticket ID."
                
        elif atype == "close_ticket":
            t_id = inner_action.ticket_id
            ticket = next((t for t in self.tickets if t.ticket_id == t_id), None)
            if ticket:
                if ticket.status == "closed":
                    feedback = f"Ticket {t_id} is already closed."
                    reward_val = -0.1
                    reason = "Closed an already closed ticket."
                else:
                    ticket.status = "closed"
                    feedback = f"Closed ticket {t_id}."
                    reward_val = 0.05
                    reason = "Closed a ticket."
            else:
                feedback = f"Ticket {t_id} not found."
                reward_val = -0.1
                reason = "Invalid ticket ID."
                
        else:
            feedback = "Unknown action."
            reward_val = -0.1
            reason = "Invalid action."
            
        observation = CustomObservation(
            feedback=feedback,
            current_tickets=self.tickets,
            kb_results=kb_results
        )
        reward = CustomReward(value=reward_val, reason=reason)
        info = {}
        
        return observation, reward, done, info
