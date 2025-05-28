import a2a.types
import uuid

print("\n=== Klasy w a2a.types zawierające 'Part' i 'Artifact' ===")
for name in dir(a2a.types):
    if "Part" in name or "Artifact" in name:
        print(name, getattr(a2a.types, name))

# Próbujemy utworzyć Part i Artifact
try:
    from a2a.types import Part, Artifact, TaskArtifactUpdateEvent
    # Przykładowy tekst odpowiedzi
    response_text = "To jest testowa odpowiedź bota."
    # Tworzymy Part (sprawdzamy jakie argumenty przyjmuje konstruktor)
    part = Part(root={"kind": "text", "text": response_text, "metadata": None})
    print("\nInstancja Part:")
    print(part)
    print("model_dump:", part.model_dump())

    # Tworzymy Artifact
    artifact = Artifact(
        artifactId=str(uuid.uuid4()),
        name="bot_response",
        parts=[part]
    )
    print("\nInstancja Artifact:")
    print(artifact)
    print("model_dump:", artifact.model_dump())

    # Tworzymy TaskArtifactUpdateEvent
    event = TaskArtifactUpdateEvent(
        taskId="test-task-id",
        artifact=artifact
    )
    print("\nInstancja TaskArtifactUpdateEvent:")
    print(event)
    print("model_dump:", event.model_dump())

except Exception as e:
    print("Błąd przy tworzeniu Part/Artifact/Event:", e)
