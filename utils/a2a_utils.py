print("=== [DEBUG] utils/a2a_utils.py LOADED ===", flush=True)

import json
from loguru import logger
from typing import Any, Dict, Union, AsyncGenerator
from a2a.types import Message, Task, TaskStatus, TaskState, Artifact, TaskStatusUpdateEvent, TaskArtifactUpdateEvent
import datetime
import uuid
import aiohttp

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Loads a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Dict containing the JSON data
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(data: Dict[str, Any], file_path: str) -> None:
    """Saves data to a JSON file.
    
    Args:
        data: Dictionary to save
        file_path: Path where to save the file
        
    Raises:
        IOError: If the file cannot be written
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def construct_agent_url(host: str, port: int) -> str:
    """Constructs an A2A agent URL.
    
    Args:
        host: Host address
        port: Port number
        
    Returns:
        Full URL string
    """
    return f"http://{host}:{port}"

def log_a2a_message(message: Union[Message, Dict], direction: str = "outgoing") -> None:
    """Logs an A2A message.
    
    Args:
        message: Message to log (Message object or dict)
        direction: Message direction ("incoming" or "outgoing")
    """
    if hasattr(message, "model_dump"):
        def default_encoder(obj):
            if hasattr(obj, "value"):
                return obj.value
            return str(obj)
        logger.debug(f"A2A {direction} message: {json.dumps(message.model_dump(), indent=2, default=default_encoder)}")
    else:
        logger.debug(f"A2A {direction} message: {json.dumps(message, indent=2)}")

def create_task_status(state: TaskState, error: str = None) -> TaskStatus:
    """Creates a task status with the given state and optional error message.
    
    Args:
        state: Task state
        error: Optional error message
        
    Returns:
        TaskStatus object
    """
    return TaskStatus(
        state=state,
        timestamp=datetime.datetime.utcnow().isoformat(),
        error=error
    )

def create_artifact(name: str, data: dict) -> Artifact:
    """Creates an artifact with the given name and data.
    
    Args:
        name: Artifact name
        data: Artifact data
        
    Returns:
        Artifact object
    """
    return Artifact(
        artifactId=str(uuid.uuid4()),
        name=name,
        parts=[{
            "type": "data",
            "data": data
        }]
    )

def create_message(content: str, role: str = "assistant", message_id: str = None) -> Message:
    """Creates a message with the given content and role.
    
    Args:
        content: Message content
        role: Message role ("user" or "assistant")
        message_id: Optional message ID
        
    Returns:
        Message object
    """
    return Message(
        role=role.value if hasattr(role, 'value') else role,
        parts=[{"type": "text", "text": content}],
        messageId=message_id or str(uuid.uuid4())
    )

def create_streaming_message(content: str, role: str = "assistant", message_id: str = None) -> Message:
    """Creates a streaming message with the given content and role.
    
    Args:
        content: Message content
        role: Message role ("user" or "assistant")
        message_id: Optional message ID
        
    Returns:
        Message object configured for streaming
    """
    return Message(
        role=role.value if hasattr(role, 'value') else role,
        parts=[{"type": "text", "text": content}],
        messageId=message_id or str(uuid.uuid4()),
        streaming=True
    )

def get_a2a_message_send_payload(message: Message, method: str = "message/send") -> dict:
    """Creates a JSON-RPC payload for sending a message according to A2A spec.
    
    Args:
        message: Message to send
        method: RPC method ("message/send" or "message/stream")
        
    Returns:
        JSON-RPC payload dictionary
    """
    def part_to_dict(part):
        if hasattr(part, "model_dump"):
            return part.model_dump()
        elif hasattr(part, "dict"):
            return part.dict()
        elif isinstance(part, dict):
            return part
        else:
            return dict(part)
            
    return {
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

async def stream_agent_response(url: str, user_input: str) -> AsyncGenerator[str, None]:
    print(f"[DEBUG] [A2A] Starting stream_agent_response with URL: {url}")
    print(f"[DEBUG] [A2A] User input: {user_input}")
    
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/stream",
        "params": {
            "message": {
                "role": "user",
                "parts": [
                    {
                        "kind": "text",
                        "metadata": None,
                        "text": user_input
                    }
                ],
                "messageId": str(uuid.uuid4())
            }
        }
    }
    
    print(f"[DEBUG] [A2A] Prepared payload: {json.dumps(payload, indent=2)}")
    print(f"[DEBUG] [A2A] Sending POST request to: {url}")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            print(f"[DEBUG] [A2A] Response status: {response.status}")
            print(f"[DEBUG] [A2A] Response headers: {dict(response.headers)}")
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        print(f"[DEBUG] [A2A] Stream response data: {json.dumps(data, indent=2)}")
                        
                        if "result" in data:
                            result = data["result"]
                            print(f"[DEBUG] [A2A] Stream result: {json.dumps(result, indent=2)}")
                            
                            if "status" in result:
                                status = result["status"]
                                print(f"[DEBUG] [A2A] Stream status: {json.dumps(status, indent=2)}")
                                
                                if "message" in status:
                                    message = status["message"]
                                    print(f"[DEBUG] [A2A] Stream message: {json.dumps(message, indent=2)}")
                                    
                                    if "parts" in message:
                                        parts = message["parts"]
                                        print(f"[DEBUG] [A2A] Stream parts: {json.dumps(parts, indent=2)}")
                                        
                                        for part in parts:
                                            if "text" in part:
                                                print(f"[DEBUG] [A2A] Yielding text: {part['text']}")
                                                yield part["text"]
                    except json.JSONDecodeError as e:
                        print(f"[DEBUG] [A2A] Error decoding JSON: {e}")
                        print(f"[DEBUG] [A2A] Raw line: {line}")
                    except Exception as e:
                        print(f"[DEBUG] [A2A] Unexpected error: {e}")
                        print(f"[DEBUG] [A2A] Raw line: {line}")

def create_task_status_event(task_id: str, status: TaskStatus) -> dict:
    """Creates a task status event.
    
    Args:
        task_id: Task ID
        status: Task status
        
    Returns:
        Task status event dictionary
    """
    return {
        "type": "task_status",
        "task_id": task_id,
        "status": status
    }

def create_artifact_event(task_id: str, artifact: Artifact) -> dict:
    """Creates an artifact event.
    
    Args:
        task_id: Task ID
        artifact: Artifact object
        
    Returns:
        Artifact event dictionary
    """
    return {
        "type": "task_artifact",
        "task_id": task_id,
        "artifact": artifact
    }

def create_artifact_part_text(text: str) -> dict:
    """Creates a text part for an artifact (A2A compatible).
    
    Args:
        text: Text content
        
    Returns:
        Text part dictionary
    """
    return {
        "kind": "text",
        "text": text,
        "metadata": None
    } 