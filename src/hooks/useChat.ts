import { useState, useCallback } from "react";
import { sendChatMessage } from "../services/api";

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: number;
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentModel, setCurrentModel] = useState(
    "anthropic/claude-3.5-sonnet"
  );

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isLoading) return;

      const userMsg: Message = {
        id: crypto.randomUUID(),
        role: "user",
        content: content.trim(),
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);

      // Add placeholder assistant message
      const assistantId = crypto.randomUUID();
      const assistantMsg: Message = {
        id: assistantId,
        role: "assistant",
        content: "",
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, assistantMsg]);

      try {
        const history = messages.map((m) => ({
          role: m.role,
          content: m.content,
        }));

        const response = await sendChatMessage(content, currentModel, history);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No reader available");

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = line.slice(6).trim();
              if (data === "[DONE]") continue;
              try {
                const parsed = JSON.parse(data);
                if (parsed.error) {
                  console.error("Stream error:", parsed.message);
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantId
                        ? { ...m, content: `Error: ${parsed.message}` }
                        : m
                    )
                  );
                  break;
                }
                if (parsed.content) {
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantId
                        ? { ...m, content: m.content + parsed.content }
                        : m
                    )
                  );
                }
              } catch {
                // skip parse errors
              }
            }
          }
        }
      } catch (err) {
        const errorMsg =
          err instanceof Error ? err.message : "Unknown error occurred";
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, content: `Error: ${errorMsg}` } : m
          )
        );
      } finally {
        setIsLoading(false);
      }
    },
    [messages, isLoading, currentModel]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    isLoading,
    currentModel,
    setCurrentModel,
    sendMessage,
    clearMessages,
  };
}