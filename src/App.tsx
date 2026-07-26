import { useState, useEffect } from "react";
import { listen } from "@tauri-apps/api/event";
import { useChat } from "./hooks/useChat";
import { ModelPicker } from "./components/ModelPicker";
import { SettingsPanel } from "./components/SettingsPanel";

function App() {
  const {
    messages,
    isLoading,
    currentModel,
    setCurrentModel,
    sendMessage,
    clearMessages,
  } = useChat();

  const [input, setInput] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeView, setActiveView] = useState<"chat" | "settings">("chat");

  // Listen for open-settings event from tray menu
  useEffect(() => {
    let unlisten: () => void;
    listen("open-settings", () => {
      setActiveView("settings");
      setSidebarOpen(true);
    }).then((fn) => {
      unlisten = fn;
    });
    return () => {
      if (unlisten) unlisten();
    };
  }, []);

  const handleSend = () => {
    if (!input.trim() || isLoading) return;
    sendMessage(input.trim());
    setInput("");
  };

  const handleNavClick = (view: "chat" | "settings") => {
    setActiveView(view);
    setSidebarOpen(true);
  };

  return (
    <div className="flex h-screen bg-prism-dark">
      {/* Sidebar */}
      <aside
        className={`${
          sidebarOpen ? "w-64" : "w-0"
        } transition-all duration-200 bg-prism-darker border-r border-prism-border overflow-hidden flex flex-col`}
      >
        <div className="p-4">
          <h1 className="text-lg font-bold text-prism-accent">Prism</h1>
          <nav className="mt-6 space-y-2">
            <button
              onClick={() => handleNavClick("chat")}
              className={`w-full text-left px-3 py-2 rounded transition-colors ${
                activeView === "chat"
                  ? "bg-prism-surface text-prism-text"
                  : "text-prism-text-muted hover:bg-prism-surface"
              }`}
            >
              💬 Chat
            </button>
            <button
              onClick={() => handleNavClick("settings")}
              className={`w-full text-left px-3 py-2 rounded transition-colors ${
                activeView === "settings"
                  ? "bg-prism-surface text-prism-text"
                  : "text-prism-text-muted hover:bg-prism-surface"
              }`}
            >
              ⚙️ Settings
            </button>
          </nav>
        </div>
        <div className="mt-auto p-4 border-t border-prism-border">
          <button
            onClick={clearMessages}
            className="w-full text-left px-3 py-2 rounded text-prism-text-muted hover:bg-prism-surface transition-colors text-sm"
          >
            🗑️ Clear chat
          </button>
        </div>
      </aside>

      {/* Main Area */}
      <main className="flex-1 flex flex-col">
        {/* Header */}
        <header className="h-12 border-b border-prism-border flex items-center px-4 gap-3">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-prism-text-muted hover:text-prism-text"
          >
            ☰
          </button>
          <span className="text-sm text-prism-text-muted flex-1">Prism AI</span>
          {activeView === "chat" && (
            <ModelPicker currentModel={currentModel} onModelChange={setCurrentModel} />
          )}
        </header>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {activeView === "chat" && (
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 && (
                <div className="flex items-center justify-center h-full text-prism-text-muted">
                  <div className="text-center">
                    <h2 className="text-2xl font-bold text-prism-accent mb-2">Prism</h2>
                    <p>How can I help you today?</p>
                    <div className="mt-4 text-xs text-prism-text-muted/50">
                      Model: {currentModel}
                    </div>
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
                    <p className="text-sm whitespace-pre-wrap">
                      {msg.content || (msg.role === "assistant" ? "..." : "")}
                    </p>
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-prism-surface rounded-lg px-4 py-2">
                    <span className="animate-pulse text-prism-text-muted">▌</span>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeView === "settings" && <SettingsPanel />}
        </div>

        {/* Input (only shown in chat view) */}
        {activeView === "chat" && (
          <div className="border-t border-prism-border p-4">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
                placeholder={isLoading ? "Waiting for response..." : "Type a message..."}
                disabled={isLoading}
                className="flex-1 bg-prism-surface border border-prism-border rounded-lg px-4 py-2 text-prism-text placeholder-prism-text-muted focus:outline-none focus:border-prism-accent disabled:opacity-50"
              />
              <button
                onClick={handleSend}
                disabled={isLoading}
                className="bg-prism-accent hover:bg-prism-accent-hover text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
              >
                Send
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;