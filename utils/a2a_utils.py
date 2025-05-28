print("=== [DEBUG] utils/a2a_utils.py LOADED ===", flush=True)

import json
from loguru import logger
from typing import Any, Dict
from a2a.types import Message, Task, TaskStatus, TaskState, Artifact
import datetime
import uuid

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Loads a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(data: Dict[str, Any], file_path: str) -> None:
    """Saves data to a JSON file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def construct_agent_url(host: str, port: int) -> str:
    """Constructs an A2A agent URL."""
    return f"http://{host}:{port}"

def log_a2a_message(message, direction: str = "outgoing"):
    """Logs an A2A message."""
    if hasattr(message, "model_dump"):
        def default_encoder(obj):
            if hasattr(obj, "value"):
                return obj.value
            return str(obj)
        logger.debug(f"A2A {direction} message: {json.dumps(message.model_dump(), indent=2, default=default_encoder)}")
    else:
        logger.debug(f"A2A {direction} message: {json.dumps(message, indent=2)}")

def create_task_status(state: TaskState, error: str = None) -> TaskStatus:
    """Creates a task status with the given state and optional error message."""
    return TaskStatus(
        state=state,
        timestamp=datetime.datetime.utcnow().isoformat(),
        error=error
    )

def create_artifact(name: str, data: dict) -> Artifact:
    """Creates an artifact with the given name and data."""
    return Artifact(
        artifactId=str(uuid.uuid4()),
        name=name,
        parts=[{
            "type": "data",
            "data": data
        }]
    )

def create_message(content: str, role: str = "assistant", message_id: str = None) -> Message:
    """Creates a message with the given content and role."""
    return Message(
        role=role.value if hasattr(role, 'value') else role,
        parts=[{"type": "text", "text": content}],
        messageId=message_id or str(uuid.uuid4())
    )

def get_a2a_message_send_payload(message: Message, method: str = "execute") -> dict:
    """Creates a JSON-RPC payload for sending a message."""
    print(f"=== [DEBUG] get_a2a_message_send_payload CALLED with method={method} ===", flush=True)
    def part_to_dict(part):
        if hasattr(part, "model_dump"):
            return part.model_dump()
        elif hasattr(part, "dict"):
            return part.dict()
        elif isinstance(part, dict):
            return part
        else:
            return dict(part)
    result = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": method,
        "params": {
            "message": {
                "role": message.role.value if hasattr(message.role, 'value') else message.role,
                "parts": [part_to_dict(p) for p in message.parts],
                "messageId": message.messageId
            }
        }
    }
    print(f"=== [DEBUG] get_a2a_message_send_payload RESULT: {json.dumps(result, indent=2)} ===", flush=True)
    return result

def create_streaming_message(content: str, role: str = "assistant") -> dict:
    """Creates a streaming message event."""
    print(f"=== [DEBUG] create_streaming_message CALLED with content={content[:100]}... ===", flush=True)
    result = {
        "type": "message",
        "message": create_message(content, role)
    }
    print(f"=== [DEBUG] create_streaming_message RESULT: {json.dumps(result, indent=2)} ===", flush=True)
    return result

def create_task_status_event(task_id: str, status: TaskStatus) -> dict:
    """Creates a task status event."""
    return {
        "type": "task_status",
        "task_id": task_id,
        "status": status
    }

def create_artifact_event(task_id: str, artifact: Artifact) -> dict:
    """Creates an artifact event."""
    return {
        "type": "task_artifact",
        "task_id": task_id,
        "artifact": artifact
    }

def create_artifact_part_text(text: str) -> dict:
    """Creates a text part for an artifact (A2A compatible)."""
    return {
        "kind": "text",
        "text": text,
        "metadata": None
    } 