from typing import Any, Dict
import json
from loguru import logger

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Loads a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(data: Dict[str, Any], file_path: str) -> None:
    """Saves data to a JSON file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def construct_agent_url(host: str, port: int) -> str:
    """Constructs an A2A agent URL.
    
    Args:
        host: Agent host
        port: Agent port
        
    Returns:
        Agent URL in format http://host:port
    """
    return f"http://{host}:{port}"

def validate_a2a_message(message: Dict[str, Any]) -> bool:
    """Validates an A2A message.
    
    Args:
        message: Message to validate
        
    Returns:
        True if message is valid, False otherwise
    """
    required_fields = ["type", "content", "task_id"]
    return all(field in message for field in required_fields)

def create_a2a_message(
    content: Any,
    message_type: str = "message",
    task_id: str = None
) -> Dict[str, Any]:
    """Creates a message in A2A format.
    
    Args:
        content: Message content
        message_type: Message type (default: "message")
        task_id: Task ID (optional)
        
    Returns:
        Message in A2A format
    """
    message = {
        "type": message_type,
        "content": content
    }
    
    if task_id:
        message["task_id"] = task_id
        
    return message

def create_a2a_error(error: str, task_id: str = None) -> Dict[str, Any]:
    """Creates an error message in A2A format.
    
    Args:
        error: Error description
        task_id: Task ID (optional)
        
    Returns:
        Error message in A2A format
    """
    return create_a2a_message(
        content={"error": error},
        message_type="error",
        task_id=task_id
    )

def create_a2a_success(content: Any, task_id: str = None) -> Dict[str, Any]:
    """Creates a success message in A2A format.
    
    Args:
        content: Response content
        task_id: Task ID (optional)
        
    Returns:
        Success message in A2A format
    """
    return create_a2a_message(
        content=content,
        message_type="message",
        task_id=task_id
    )

def log_a2a_message(message: Dict[str, Any], direction: str = "outgoing"):
    """Logs an A2A message.
    
    Args:
        message: Message to log
        direction: Message direction ("incoming" or "outgoing")
    """
    logger.debug(f"A2A {direction} message: {json.dumps(message, indent=2)}") 