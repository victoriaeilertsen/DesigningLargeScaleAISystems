from dataclasses import dataclass, field
from typing import List, Optional, Dict
import uuid
import datetime

@dataclass
class A2AMessage:
    sender: str
    receiver: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    debug: Optional[dict] = None

@dataclass
class A2ATask:
    task_id: str
    status: str  # e.g. 'submitted', 'working', 'completed'
    messages: List[A2AMessage]
    context: Optional[Dict] = field(default_factory=dict)

    @staticmethod
    def create(sender: str, receiver: str, content: str) -> 'A2ATask':
        msg = A2AMessage(sender=sender, receiver=receiver, content=content)
        return A2ATask(
            task_id=str(uuid.uuid4()),
            status='submitted',
            messages=[msg]
        )
