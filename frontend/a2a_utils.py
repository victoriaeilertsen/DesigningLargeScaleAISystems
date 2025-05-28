import aiohttp
import json
from a2a.types import TaskStatusUpdateEvent, TaskArtifactUpdateEvent

ORCHESTRATOR_URL = "http://localhost:8000"

raise Exception("=== [DEBUG] a2a_utils.py IMPORTED ===")

print("=== [DEBUG] a2a_utils.py LOADED ===", flush=True)

async def stream_agent_response(user_input: str):
    """Stream agent response from the orchestrator."""
    print("=== [DEBUG] stream_agent_response CALLED ===", flush=True)
    print(f"[DEBUG] Initializing stream_agent_response for input: {user_input}")
    
    async with aiohttp.ClientSession() as session:
        print("[DEBUG] Sending request to orchestrator")
        async with session.post(
            f"{ORCHESTRATOR_URL}/stream",
            json={"message": user_input}
        ) as response:
            print(f"[DEBUG] Received response with status: {response.status}")
            
            if response.status != 200:
                error_text = await response.text()
                print(f"[ERROR] Orchestrator returned error: {error_text}")
                raise Exception(f"Orchestrator error: {error_text}")
            
            buffer = ""
            async for chunk in response.content:
                print(f"[DEBUG] Raw chunk: {repr(chunk)}")
                buffer += chunk.decode()
                while '\r\n\r\n' in buffer:
                    event, buffer = buffer.split('\r\n\r\n', 1)
                    event = event.strip()
                    if not event or not event.startswith('data: '):
                        continue
                    json_str = event[6:]
                    if not json_str.strip():
                        continue
                    print(f"[DEBUG] Parsing JSON: {json_str}")
                    try:
                        event_data = json.loads(json_str)
                        if "result" not in event_data:
                            print("[WARNING] Event missing 'result' field")
                            continue
                        result = event_data["result"]
                        print(f"[DEBUG] Processing event result: {result}")
                        if result["kind"] == "status-update":
                            event_obj = TaskStatusUpdateEvent(**result)
                            print(f"[DEBUG] Created TaskStatusUpdateEvent: {event_obj}")
                            yield event_obj
                        elif result["kind"] == "artifact-update":
                            event_obj = TaskArtifactUpdateEvent(**result)
                            print(f"[DEBUG] Created TaskArtifactUpdateEvent: {event_obj}")
                            yield event_obj
                        else:
                            print(f"[WARNING] Unknown event kind: {result['kind']}")
                    except json.JSONDecodeError as e:
                        print(f"[ERROR] Failed to parse JSON: {e}")
                        print(f"[DEBUG] Raw event content: {event}")
                    except Exception as e:
                        print(f"[ERROR] Unexpected error processing event: {e}") 