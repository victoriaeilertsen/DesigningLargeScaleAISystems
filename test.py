import requests
import uuid

ORCHESTRATOR_URL = "http://localhost:8000/stream"

def test_a2a_message_stream():
    # Tworzymy wiadomość zgodnie ze specyfikacją A2A
    message = {
        "kind": "message",
        "messageId": str(uuid.uuid4()),
        "role": "user",
        "parts": [
            {
                "kind": "text",
                "text": "I want to buy a red shirt"
            }
        ]
    }

    # JSON-RPC request zgodnie ze specyfikacją
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/stream",
        "params": {
            "message": message
        }
    }

    print("Wysyłam żądanie do Orchestratora (A2A message/stream)...")
    try:
        response = requests.post(
            ORCHESTRATOR_URL,
            json=payload,
            timeout=15,
            stream=True
        )
        print("Kod odpowiedzi HTTP:", response.status_code)
        print("Nagłówki:", response.headers)
        print("Odpowiedź:")
        for line in response.iter_lines():
            if line:
                print(line.decode())
    except Exception as e:
        print("Błąd podczas komunikacji z Orchestrator:", e)

if __name__ == "__main__":
    test_a2a_message_stream()
