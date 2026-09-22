import { useState, useEffect } from "react";
import { listen } from "@tauri-apps/api/event";
import { useChat } from "./hooks/useChat";
import { ModelPicker } from "./components/ModelPicker";
import { SettingsPanel } from "./components/SettingsPanel";
import { VoiceIndicator } from "./components/VoiceIndicator";

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
    <div className="flex h-screen bg-tesseract-dark">
      {/* Sidebar */}
      <aside
        className={`${
          sidebarOpen ? "w-64" : "w-0"
        } transition-all duration-200 bg-tesseract-darker border-r border-tesseract-border overflow-hidden flex flex-col`}
      >
        <div className="p-4">
          <h1 className="text-lg font-bold text-tesseract-accent">Tesseract</h1>
          <nav className="mt-6 space-y-2">
            <button
              onClick={() => handleNavClick("chat")}
              className={`w-full text-left px-3 py-2 rounded transition-colors ${
                activeView === "chat"
                  ? "bg-tesseract-surface text-tesseract-text"
                  : "text-tesseract-text-muted hover:bg-tesseract-surface"
              }`}
            >
              💬 Chat
            </button>
            <button
              onClick={() => handleNavClick("settings")}
              className={`w-full text-left px-3 py-2 rounded transition-colors ${
                activeView === "settings"
                  ? "bg-tesseract-surface text-tesseract-text"
                  : "text-tesseract-text-muted hover:bg-tesseract-surface"
              }`}
            >
              ⚙️ Settings
            </button>
          </nav>
        </div>
        <div className="mt-auto p-4 border-t border-tesseract-border">
          <button
            onClick={clearMessages}
            className="w-full text-left px-3 py-2 rounded text-tesseract-text-muted hover:bg-tesseract-surface transition-colors text-sm"
          >
            🗑️ Clear chat
          </button>
        </div>
      </aside>

      {/* Main Area */}
      <main className="flex-1 flex flex-col">
        {/* Header */}
        <header className="h-12 border-b border-tesseract-border flex items-center px-4 gap-3">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-tesseract-text-muted hover:text-tesseract-text"
          >
            ☰
          </button>
          <span className="text-sm text-tesseract-text-muted flex-1">Tesseract AI</span>
          {activeView === "chat" && (
            <>
              <ModelPicker currentModel={currentModel} onModelChange={setCurrentModel} />
              <VoiceIndicator
                onTranscription={(text) => {
                  // Send transcribed text as a chat message
                  if (text.trim()) {
                    sendMessage(text.trim());
                  }
                }}
              />
            </>
          )}
        </header>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {activeView === "chat" && (
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 && (
                <div className="flex items-center justify-center h-full text-tesseract-text-muted">
                  <div className="text-center">
                    <h2 className="text-2xl font-bold text-tesseract-accent mb-2">Tesseract</h2>
                    <p>How can I help you today?</p>
                    <div className="mt-4 text-xs text-tesseract-text-muted/50">
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
                        ? "bg-tesseract-accent text-white"
                        : "bg-tesseract-surface text-tesseract-text"
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
                  <div className="bg-tesseract-surface rounded-lg px-4 py-2">
                    <span className="animate-pulse text-tesseract-text-muted">▌</span>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeView === "settings" && <SettingsPanel />}
        </div>

        {/* Input (only shown in chat view) */}
        {activeView === "chat" && (
          <div className="border-t border-tesseract-border p-4">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
                placeholder={isLoading ? "Waiting for response..." : "Type a message..."}
                disabled={isLoading}
                className="flex-1 bg-tesseract-surface border border-tesseract-border rounded-lg px-4 py-2 text-tesseract-text placeholder-tesseract-text-muted focus:outline-none focus:border-tesseract-accent disabled:opacity-50"
              />
              <button
                onClick={handleSend}
                disabled={isLoading}
                className="bg-tesseract-accent hover:bg-tesseract-accent-hover text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
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