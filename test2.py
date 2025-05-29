import uuid
from a2a.types import Message, Task, TaskState, Role, TextPart, TaskStatusUpdateEvent
from a2a.server.agent_execution.context import RequestContext
import streamlit as st

def print_object_info(obj, name):
    print(f"\n{name}:")
    print("type:", type(obj))
    print("dir:", dir(obj))
    print("vars:", vars(obj))
    print()

# Sprawdź RequestContext
context = RequestContext(
    context_id=str(uuid.uuid4()),
    task_id=str(uuid.uuid4())
)
print_object_info(context, "RequestContext")

# Sprawdź Task
task = Task(
    id=str(uuid.uuid4()),
    contextId=str(uuid.uuid4()),
    status={"state": TaskState.submitted.value}
)
print_object_info(task, "Task")

# Sprawdź TaskStatusUpdateEvent
event = TaskStatusUpdateEvent(
    contextId=str(uuid.uuid4()),
    taskId=str(uuid.uuid4()),
    status={"state": TaskState.working.value},
    final=False
)
print_object_info(event, "TaskStatusUpdateEvent")

# Sprawdź Message
message = Message(
    messageId=str(uuid.uuid4()),
    role=Role.user,
    parts=[TextPart(text="test message")]
)
print_object_info(message, "Message")

# Sprawdź, jakie wartości mają statusy TaskState
print("\nTaskState values:")
for state in TaskState:
    print(f"{state} = {state.value}")

def test_request_context_message_property():
    message = Message(
        messageId=str(uuid.uuid4()),
        role=Role.user,
        parts=[TextPart(text="test message")]
    )
    context = RequestContext(
        context_id=str(uuid.uuid4()),
        task_id=str(uuid.uuid4())
    )
    context._message = message
    print("context.message:", context.message)
    print("context._message:", context._message)
    print("Czy context.message == context._message?", context.message == context._message)

# Test tworzenia obiektu Task
try:
    task = Task(
        id="test-task-id",
        contextId="test-context-id",
        status={"state": TaskState.submitted.value}
    )
    print("Task utworzony poprawnie:", task)
except Exception as e:
    print("Błąd przy tworzeniu Task:", e)

def test_extract_text_from_parts_dict():
    # Simulate deserialized Message.parts as list of dicts
    parts = [
        {"kind": "text", "text": "hello "},
        {"kind": "text", "text": "world!"},
        {"kind": "image", "url": "http://example.com/image.png"},
    ]
    message_text = ""
    for part in parts:
        if part.get('kind') == 'text':
            message_text += part.get('text', '')
    print("Extracted message_text from dict parts:", repr(message_text))

def test_manual_message_display():
    # Ręcznie ustawiamy wiadomość asystenta
    st.session_state.messages = [
        {"role": "assistant", "content": "This is a test message from the assistant."}
    ]
    
    # Wyświetlamy wiadomość w UI
    for msg in st.session_state.messages:
        st.write(f"{msg['role']}: {msg['content']}")
    
    # Sprawdzamy, czy wiadomość jest poprawnie wyświetlana
    assert "This is a test message from the assistant." in st.session_state.messages[-1]["content"]

if __name__ == "__main__":
    test_request_context_message_property()
    test_extract_text_from_parts_dict()
    test_manual_message_display()
