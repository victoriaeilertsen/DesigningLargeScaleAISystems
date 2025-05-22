from typing import Any, Dict
import json
from loguru import logger

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Wczytuje plik JSON."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(data: Dict[str, Any], file_path: str) -> None:
    """Zapisuje dane do pliku JSON."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def construct_agent_url(host: str, port: int) -> str:
    """Konstruuje URL agenta A2A.
    
    Args:
        host: Host agenta
        port: Port agenta
        
    Returns:
        URL agenta w formacie http://host:port
    """
    return f"http://{host}:{port}"

def validate_a2a_message(message: Dict[str, Any]) -> bool:
    """Waliduje wiadomość A2A.
    
    Args:
        message: Wiadomość do walidacji
        
    Returns:
        True jeśli wiadomość jest poprawna, False w przeciwnym razie
    """
    required_fields = ["type", "content", "task_id"]
    return all(field in message for field in required_fields)

def create_a2a_message(
    content: Any,
    message_type: str = "message",
    task_id: str = None
) -> Dict[str, Any]:
    """Tworzy wiadomość w formacie A2A.
    
    Args:
        content: Zawartość wiadomości
        message_type: Typ wiadomości (domyślnie "message")
        task_id: ID zadania (opcjonalne)
        
    Returns:
        Wiadomość w formacie A2A
    """
    message = {
        "type": message_type,
        "content": content
    }
    
    if task_id:
        message["task_id"] = task_id
        
    return message

def create_a2a_error(error: str, task_id: str = None) -> Dict[str, Any]:
    """Tworzy wiadomość błędu w formacie A2A.
    
    Args:
        error: Opis błędu
        task_id: ID zadania (opcjonalne)
        
    Returns:
        Wiadomość błędu w formacie A2A
    """
    return create_a2a_message(
        content={"error": error},
        message_type="error",
        task_id=task_id
    )

def create_a2a_success(content: Any, task_id: str = None) -> Dict[str, Any]:
    """Tworzy wiadomość sukcesu w formacie A2A.
    
    Args:
        content: Zawartość odpowiedzi
        task_id: ID zadania (opcjonalne)
        
    Returns:
        Wiadomość sukcesu w formacie A2A
    """
    return create_a2a_message(
        content=content,
        message_type="message",
        task_id=task_id
    )

def log_a2a_message(message: Dict[str, Any], direction: str = "outgoing"):
    """Loguje wiadomość A2A.
    
    Args:
        message: Wiadomość do zalogowania
        direction: Kierunek wiadomości ("incoming" lub "outgoing")
    """
    logger.debug(f"A2A {direction} message: {json.dumps(message, indent=2)}") 