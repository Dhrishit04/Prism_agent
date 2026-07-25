import { useState } from "react";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: number;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleSend = () => {
    if (!input.trim()) return;
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: input.trim(),
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    // TODO: Send to Python sidecar → LLM
  };

  return (
    <div className="flex h-screen bg-prism-dark">
      {/* Sidebar */}
      <aside
        className={`${
          sidebarOpen ? "w-64" : "w-0"
        } transition-all duration-200 bg-prism-darker border-r border-prism-border overflow-hidden`}
      >
        <div className="p-4">
          <h1 className="text-lg font-bold text-prism-accent">Prism</h1>
          <nav className="mt-6 space-y-2">
            <button className="w-full text-left px-3 py-2 rounded bg-prism-surface text-prism-text hover:bg-prism-accent/20 transition-colors">
              💬 Chat
            </button>
            <button className="w-full text-left px-3 py-2 rounded text-prism-text-muted hover:bg-prism-surface transition-colors">
              ⚙️ Settings
            </button>
          </nav>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col">
        {/* Header */}
        <header className="h-12 border-b border-prism-border flex items-center px-4 gap-3">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-prism-text-muted hover:text-prism-text"
          >
            ☰
          </button>
          <span className="text-sm text-prism-text-muted">Prism AI</span>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex items-center justify-center h-full text-prism-text-muted">
              <div className="text-center">
                <h2 className="text-2xl font-bold text-prism-accent mb-2">Prism</h2>
                <p>How can I help you today?</p>
              </div>
            </div>
          )}
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[70%] rounded-lg px-4 py-2 ${
                  msg.role === "user"
                    ? "bg-prism-accent text-white"
                    : "bg-prism-surface text-prism-text"
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Input */}
        <div className="border-t border-prism-border p-4">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Type a message..."
              className="flex-1 bg-prism-surface border border-prism-border rounded-lg px-4 py-2 text-prism-text placeholder-prism-text-muted focus:outline-none focus:border-prism-accent"
            />
            <button
              onClick={handleSend}
              className="bg-prism-accent hover:bg-prism-accent-hover text-white px-4 py-2 rounded-lg transition-colors"
            >
              Send
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;