import { useState, useEffect, useRef } from "react";
import { listModels } from "../services/api";

interface Model {
  id: string;
  name?: string;
}

interface ModelPickerProps {
  currentModel: string;
  onModelChange: (model: string) => void;
}

export function ModelPicker({ currentModel, onModelChange }: ModelPickerProps) {
  const [models, setModels] = useState<Model[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function fetchModels() {
      try {
        const result = await listModels();
        if (result.length > 0) {
          setModels(result);
        } else {
          // Fallback models when no API key configured
          setModels([
            { id: "anthropic/claude-3.5-sonnet", name: "Claude 3.5 Sonnet" },
            { id: "openai/gpt-4o", name: "GPT-4o" },
            { id: "meta-llama/llama-3.1-70b-instruct", name: "Llama 3.1 70B" },
            { id: "google/gemini-pro-1.5", name: "Gemini Pro 1.5" },
          ]);
        }
      } catch {
        setModels([
          { id: "anthropic/claude-3.5-sonnet", name: "Claude 3.5 Sonnet" },
          { id: "openai/gpt-4o", name: "GPT-4o" },
        ]);
      } finally {
        setLoading(false);
      }
    }
    fetchModels();
  }, []);

  // Close on click outside
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const displayName = (model: Model) =>
    model.name || model.id.split("/").pop() || model.id;

  return (
    <div ref={dropdownRef} className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 text-xs bg-tesseract-surface border border-tesseract-border rounded-md text-tesseract-text hover:border-tesseract-accent transition-colors"
        disabled={loading}
      >
        {loading ? "Loading..." : displayName({ id: currentModel })}
        <span className="text-tesseract-text-muted">▼</span>
      </button>

      {isOpen && (
        <div className="absolute top-full mt-1 right-0 w-64 bg-tesseract-surface border border-tesseract-border rounded-lg shadow-xl z-50 max-h-64 overflow-y-auto">
          {models.map((model) => (
            <button
              key={model.id}
              onClick={() => {
                onModelChange(model.id);
                setIsOpen(false);
              }}
              className={`w-full text-left px-4 py-2 text-sm hover:bg-tesseract-accent/20 transition-colors ${
                currentModel === model.id
                  ? "text-tesseract-accent bg-tesseract-accent/10"
                  : "text-tesseract-text"
              }`}
            >
              {displayName(model)}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}