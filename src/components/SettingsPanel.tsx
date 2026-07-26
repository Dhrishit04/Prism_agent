import { useState, useEffect } from "react";
import { getSettings, saveSettings, resetSettings, Settings } from "../services/settings";

export function SettingsPanel() {
  const [settings, setSettings] = useState<Settings>({
    openrouter_api_key: "",
    default_model: "anthropic/claude-3.5-sonnet",
    voice_enabled: false,
    automation_enabled: false,
    theme: "dark",
    language: "en",
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [showApiKey, setShowApiKey] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const loaded = await getSettings();
      setSettings(loaded);
    } catch (err) {
      console.error("Failed to load settings:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    try {
      await saveSettings(settings);
      // Notify sidecar to reload settings
      try {
        await fetch("http://127.0.0.1:8765/configure", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ api_key: settings.openrouter_api_key }),
        });
      } catch {
        // Sidecar might not be running, that's okay
      }
      setMessage({ type: "success", text: "Settings saved successfully!" });
    } catch (err) {
      setMessage({ type: "error", text: `Failed to save: ${err instanceof Error ? err.message : "Unknown error"}` });
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    setMessage(null);
    try {
      const defaults = await resetSettings();
      setSettings(defaults);
      setMessage({ type: "success", text: "Settings reset to defaults!" });
    } catch (err) {
      setMessage({ type: "error", text: `Failed to reset: ${err instanceof Error ? err.message : "Unknown error"}` });
    }
  };

  const handleChange = (key: keyof Settings, value: string | boolean) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-prism-text-muted">
        Loading settings...
      </div>
    );
  }

  const inputClass = "w-full bg-prism-surface border border-prism-border rounded-lg px-4 py-2 text-prism-text placeholder-prism-text-muted focus:outline-none focus:border-prism-accent";

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-8">
      <div>
        <h2 className="text-xl font-bold text-prism-accent mb-2">Settings</h2>
        <p className="text-prism-text-muted text-sm">Configure your Prism AI Agent preferences</p>
      </div>

      {/* API Key Section */}
      <section className="bg-prism-surface border border-prism-border rounded-xl p-6 space-y-4">
        <h3 className="text-lg font-semibold text-prism-text flex items-center gap-2">
          <span className="text-prism-accent">🔑</span> OpenRouter API Key
        </h3>
        <p className="text-prism-text-muted text-sm">
          Get your API key from <a href="https://openrouter.ai/keys" target="_blank" rel="noopener noreferrer" className="text-prism-accent hover:underline">OpenRouter</a>.
          The key is stored locally in ~/.prism/settings.json and never sent anywhere except OpenRouter.
        </p>
        <div className="relative">
          <input
            type={showApiKey ? "text" : "password"}
            value={settings.openrouter_api_key}
            onChange={(e) => handleChange("openrouter_api_key", e.target.value)}
            placeholder="sk-or-v1-..."
            className={`${inputClass} pr-12`}
          />
          <button
            type="button"
            onClick={() => setShowApiKey(!showApiKey)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-prism-text-muted hover:text-prism-text"
          >
            {showApiKey ? "🙈" : "👁️"}
          </button>
        </div>
      </section>

      {/* Model Selection Section */}
      <section className="bg-prism-surface border border-prism-border rounded-xl p-6 space-y-4">
        <h3 className="text-lg font-semibold text-prism-text flex items-center gap-2">
          <span className="text-prism-accent">🤖</span> Default Model
        </h3>
        <p className="text-prism-text-muted text-sm">The model used for new conversations.</p>
        <select
          value={settings.default_model}
          onChange={(e) => handleChange("default_model", e.target.value)}
          className={inputClass}
        >
          <option value="anthropic/claude-3.5-sonnet">Claude 3.5 Sonnet</option>
          <option value="openai/gpt-4o">GPT-4o</option>
          <option value="meta-llama/llama-3.1-70b-instruct">Llama 3.1 70B</option>
          <option value="google/gemini-pro-1.5">Gemini Pro 1.5</option>
          <option value="anthropic/claude-3-opus">Claude 3 Opus</option>
          <option value="openai/gpt-4-turbo">GPT-4 Turbo</option>
        </select>
      </section>

      {/* Voice Settings */}
      <section className="bg-prism-surface border border-prism-border rounded-xl p-6 space-y-4">
        <h3 className="text-lg font-semibold text-prism-text flex items-center gap-2">
          <span className="text-prism-accent">🎤</span> Voice
        </h3>
        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={settings.voice_enabled}
            onChange={(e) => handleChange("voice_enabled", e.target.checked)}
            className="w-5 h-5 accent-prism-accent border-prism-border bg-prism-darker rounded"
          />
          <span className="text-prism-text">Enable voice input (wake word + STT)</span>
        </label>
        <p className="text-prism-text-muted text-sm ml-8">Requires Porcupine + Whisper.cpp (configured in Phase 8)</p>
      </section>

      {/* Automation Settings */}
      <section className="bg-prism-surface border border-prism-border rounded-xl p-6 space-y-4">
        <h3 className="text-lg font-semibold text-prism-text flex items-center gap-2">
          <span className="text-prism-accent">⚙️</span> Automation
        </h3>
        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={settings.automation_enabled}
            onChange={(e) => handleChange("automation_enabled", e.target.checked)}
            className="w-5 h-5 accent-prism-accent border-prism-border bg-prism-darker rounded"
          />
          <span className="text-prism-text">Enable GUI automation (web + desktop)</span>
        </label>
        <p className="text-prism-text-muted text-sm ml-8">Allows Prism to control browser, apps, and desktop (Phases 9-11)</p>
      </section>

      {/* Appearance Settings */}
      <section className="bg-prism-surface border border-prism-border rounded-xl p-6 space-y-4">
        <h3 className="text-lg font-semibold text-prism-text flex items-center gap-2">
          <span className="text-prism-accent">🎨</span> Appearance
        </h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-prism-text-muted mb-2">Theme</label>
            <select
              value={settings.theme}
              onChange={(e) => handleChange("theme", e.target.value)}
              className={inputClass}
            >
              <option value="dark">Dark</option>
              <option value="light">Light</option>
              <option value="system">System</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-prism-text-muted mb-2">Language</label>
            <select
              value={settings.language}
              onChange={(e) => handleChange("language", e.target.value)}
              className={inputClass}
            >
              <option value="en">English</option>
              <option value="es">Español</option>
              <option value="fr">Français</option>
              <option value="de">Deutsch</option>
              <option value="ja">日本語</option>
              <option value="zh">中文</option>
            </select>
          </div>
        </div>
      </section>

      {/* Data & Storage */}
      <section className="bg-prism-surface border border-prism-border rounded-xl p-6 space-y-4">
        <h3 className="text-lg font-semibold text-prism-text flex items-center gap-2">
          <span className="text-prism-accent">💾</span> Data & Storage
        </h3>
        <p className="text-prism-text-muted text-sm">
          Settings are stored in <code className="bg-prism-darker px-1.5 py-0.5 rounded text-prism-accent">~/.prism/settings.json</code>
        </p>
        <div className="flex gap-3 pt-2">
          <button
            onClick={handleReset}
            className="px-4 py-2 bg-prism-border hover:bg-prism-border/80 text-prism-text rounded-lg transition-colors text-sm"
          >
            Reset to Defaults
          </button>
        </div>
      </section>

      {/* Save Button */}
      <div className="flex justify-end pt-4 border-t border-prism-border">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-2.5 bg-prism-accent hover:bg-prism-accent-hover text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? "Saving..." : "Save Settings"}
        </button>
      </div>

      {/* Status Message */}
      {message && (
        <div
          className={`fixed bottom-6 right-6 px-4 py-3 rounded-lg shadow-lg text-sm z-50 animate-slide-up ${
            message.type === "success" ? "bg-green-600/90" : "bg-red-600/90"
          }`}
        >
          {message.text}
        </div>
      )}
    </div>
  );
}