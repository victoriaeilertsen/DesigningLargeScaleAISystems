import { useState } from "react";

// ---------------------------------------------------------------------------
// Simple chat UI for the Shopping‑Assistant project
// ---------------------------------------------------------------------------
// * Displays message bubbles for user (blue) and agent (green)
// * Sends POST /chat to the FastAPI backend running at localhost:8000
// * Shows a tiny "Agent is typing…" indicator while waiting for the response
// * TailwindCSS classes for quick styling (configured by default in Vite + Tailwind)
// ---------------------------------------------------------------------------

export default function App() {
  // Full chat history, each message: { role: "user" | "agent", content: string }
  const [messages, setMessages] = useState([]);
  // Current text in the input box
  const [input, setInput] = useState("");
  // Loading flag for spinner / indicator
  const [loading, setLoading] = useState(false);

  // -------------------------------------------------------------------------
  // sendMessage – called on click or Enter key
  // -------------------------------------------------------------------------
  const sendMessage = async () => {
    if (!input.trim()) return; // ignore empty messages

    // 1. push user message to UI immediately
    const userMsg = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      // 2. call backend REST endpoint
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg.content })
      });
      const data = await res.json();

      // 3. show agent reply
      const botMsg = { role: "agent", content: data.response };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        { role: "agent", content: "⚠️ Error contacting backend." }
      ]);
    } finally {
      setLoading(false);
    }
  };

  // -------------------------------------------------------------------------
  // JSX layout – chat window & input bar
  // -------------------------------------------------------------------------
  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center p-4">
      <div className="w-full max-w-xl bg-white rounded-2xl shadow p-4 flex flex-col gap-3">
        <h1 className="text-2xl font-semibold mb-2">Shopping Assistant</h1>

        {/* Message list */}
        <div className="flex-1 overflow-y-auto max-h-[60vh] space-y-2 pr-2">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`rounded-xl p-3 shadow-sm whitespace-pre-line ${
                m.role === "user" ? "bg-blue-100 self-end" : "bg-green-100 self-start"
              }`}
            >
              {m.content}
            </div>
          ))}
          {/* Typing indicator */}
          {loading && (
            <div className="italic text-sm text-gray-500">Agent is typing…</div>
          )}
        </div>

        {/* Input bar */}
        <div className="flex gap-2 mt-2">
          <input
            className="flex-1 border rounded-xl p-2 focus:outline-none"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            placeholder="Type your message…"
          />
          <button
            className="px-4 py-2 rounded-xl bg-blue-600 text-white disabled:opacity-50"
            onClick={sendMessage}
            disabled={loading}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
