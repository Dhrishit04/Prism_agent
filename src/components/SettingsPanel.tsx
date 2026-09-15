import { useState, useEffect } from "react";
import { getSettings, saveSettings, resetSettings, Settings } from "../services/settings";

export function SettingsPanel() {
  const [settings, setSettings] = useState<Settings>({
    openrouter_api_key: "",
    default_model: "anthropic/claude-3.5-sonnet",
    voice: {
      voice_enabled: false,
      wake_word: "jarvis",
      wake_word_enabled: false,
      porcupine_access_key: "",
      stt_model: "tiny",
      stt_language: "en",
      tts_engine: "piper",
      tts_voice: "en_US-lessac-medium",
      tts_speed: 1.0,
      openrouter_tts_voice: "alloy",
    },
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
        // Also update voice settings in sidecar
        await fetch("http://127.0.0.1:8765/voice/settings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ settings: settings.voice }),
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

  const handleChange = (key: string, value: string | boolean | number) => {
    setSettings((prev) => {
      const next = { ...prev };
      // Handle nested voice settings (e.g., "voice_enabled" -> "voice.voice_enabled")
      const voiceKeys = [
        "voice_enabled",
        "wake_word",
        "wake_word_enabled",
        "porcupine_access_key",
        "stt_model",
        "stt_language",
        "tts_engine",
        "tts_voice",
        "tts_speed",
        "openrouter_tts_voice",
      ];
      if (key.startsWith("voice.") || voiceKeys.includes(key)) {
        next.voice = { ...prev.voice, [key.replace("voice.", "")]: value };
      } else {
        // Type-safe assignment for top-level settings keys (excluding 'voice' which is handled above)
        const topLevelKeys = [
          "openrouter_api_key",
          "default_model",
          "automation_enabled",
          "theme",
          "language",
        ] as const;
        if (topLevelKeys.includes(key as typeof topLevelKeys[number])) {
          // Use type assertion to avoid index signature issues
          const typedNext = next as unknown as Record<string, string | boolean | number>;
          typedNext[key] = value;
        }
      }
      return next;
    });
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
      <section className="bg-prism-surface border border-prism-border rounded-xl p-6 space-y-6">
        <h3 className="text-lg font-semibold text-prism-text flex items-center gap-2">
          <span className="text-prism-accent">🎤</span> Voice
        </h3>

        {/* Voice Enabled Toggle */}
        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={settings.voice.voice_enabled}
            onChange={(e) => handleChange("voice_enabled", e.target.checked)}
            className="w-5 h-5 accent-prism-accent border-prism-border bg-prism-darker rounded"
          />
          <span className="text-prism-text">Enable voice input (wake word + STT + TTS)</span>
        </label>

        {/* Porcupine Access Key */}
        <div>
          <label className="block text-sm text-prism-text-muted mb-2">
            Porcupine Access Key <span className="text-prism-text-muted/70">(required for wake word)</span>
          </label>
          <input
            type="password"
            value={settings.voice.porcupine_access_key}
            onChange={(e) => handleChange("porcupine_access_key", e.target.value)}
            placeholder="Get key from console.picovoice.ai"
            className={inputClass}
          />
          <p className="text-prism-text-muted text-sm mt-1">
            Get your free access key from <a href="https://console.picovoice.ai/" target="_blank" rel="noopener noreferrer" className="text-prism-accent hover:underline">Picovoice Console</a>
          </p>
        </div>

        {/* Wake Word Settings */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-prism-text-muted mb-2">Wake Word</label>
            <select
              value={settings.voice.wake_word}
              onChange={(e) => handleChange("wake_word", e.target.value)}
              className={inputClass}
            >
              <option value="jarvis">Jarvis</option>
              <option value="alexa">Alexa</option>
              <option value="hey google">Hey Google</option>
              <option value="hey siri">Hey Siri</option>
              <option value="computer">Computer</option>
              <option value="bumblebee">Bumblebee</option>
              <option value="picovoice">Picovoice</option>
              <option value="porcupine">Porcupine</option>
              <option value="terminator">Terminator</option>
            </select>
          </div>
          <div>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.voice.wake_word_enabled}
                onChange={(e) => handleChange("wake_word_enabled", e.target.checked)}
                className="w-4 h-4 accent-prism-accent border-prism-border bg-prism-darker rounded"
              />
              <span className="text-prism-text">Enable wake word detection</span>
            </label>
          </div>
        </div>

        {/* STT Settings */}
        <div className="pt-4 border-t border-prism-border">
          <h4 className="text-md font-medium text-prism-text mb-3">Speech-to-Text (Whisper.cpp)</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-prism-text-muted mb-2">Model</label>
              <select
                value={settings.voice.stt_model}
                onChange={(e) => handleChange("stt_model", e.target.value)}
                className={inputClass}
              >
                <option value="tiny">Tiny (fastest, ~39 MB)</option>
                <option value="base">Base (~74 MB)</option>
                <option value="small">Small (~244 MB)</option>
                <option value="medium">Medium (~769 MB)</option>
                <option value="large-v3">Large v3 (~1.5 GB)</option>
              </select>
              <p className="text-prism-text-muted text-sm mt-1">Larger models = better accuracy, slower & more memory</p>
            </div>
            <div>
              <label className="block text-sm text-prism-text-muted mb-2">Language</label>
              <select
                value={settings.voice.stt_language}
                onChange={(e) => handleChange("stt_language", e.target.value)}
                className={inputClass}
              >
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
                <option value="it">Italian</option>
                <option value="pt">Portuguese</option>
                <option value="ru">Russian</option>
                <option value="ja">Japanese</option>
                <option value="ko">Korean</option>
                <option value="zh">Chinese</option>
                <option value="auto">Auto-detect</option>
              </select>
            </div>
          </div>
        </div>

        {/* TTS Settings */}
        <div className="pt-4 border-t border-prism-border">
          <h4 className="text-md font-medium text-prism-text mb-3">Text-to-Speech</h4>

          {/* TTS Engine Selection */}
          <div className="mb-4">
            <label className="block text-sm text-prism-text-muted mb-2">TTS Engine</label>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  value="piper"
                  checked={settings.voice.tts_engine === "piper"}
                  onChange={(e) => handleChange("tts_engine", e.target.value)}
                  className="w-4 h-4 accent-prism-accent border-prism-border bg-prism-darker rounded"
                />
                <span className="text-prism-text">Piper (local, offline)</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  value="openrouter"
                  checked={settings.voice.tts_engine === "openrouter"}
                  onChange={(e) => handleChange("tts_engine", e.target.value)}
                  className="w-4 h-4 accent-prism-accent border-prism-border bg-prism-darker rounded"
                />
                <span className="text-prism-text">OpenRouter (cloud, higher quality)</span>
              </label>
            </div>
          </div>

          {/* Piper Voice Settings */}
          {settings.voice.tts_engine === "piper" && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pl-4 border-l-2 border-prism-border">
              <div>
                <label className="block text-sm text-prism-text-muted mb-2">Piper Voice</label>
                <select
                  value={settings.voice.tts_voice}
                  onChange={(e) => handleChange("tts_voice", e.target.value)}
                  className={inputClass}
                >
                  <option value="en_US-lessac-medium">en_US-lessac-medium (Male, clear)</option>
                  <option value="en_US-amy-low">en_US-amy-low (Female, soft)</option>
                  <option value="en_US-ryan-high">en_US-ryan-high (Male, energetic)</option>
                  <option value="en_US-kristin-medium">en_US-kristin-medium (Female, natural)</option>
                  <option value="en_GB-alan-low">en_GB-alan-low (British Male)</option>
                  <option value="en_GB-semaine-medium">en_GB-semaine-medium (British Female)</option>
                </select>
                <p className="text-prism-text-muted text-sm mt-1">Models auto-download to ~/.local/share/piper/voices/</p>
              </div>
            </div>
          )}

          {/* OpenRouter TTS Voice Settings */}
          {settings.voice.tts_engine === "openrouter" && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pl-4 border-l-2 border-prism-border">
              <div>
                <label className="block text-sm text-prism-text-muted mb-2">OpenRouter Voice</label>
                <select
                  value={settings.voice.openrouter_tts_voice}
                  onChange={(e) => handleChange("openrouter_tts_voice", e.target.value)}
                  className={inputClass}
                >
                  <option value="alloy">Alloy (neutral)</option>
                  <option value="echo">Echo (male, conversational)</option>
                  <option value="fable">Fable (expressive, storytelling)</option>
                  <option value="onyx">Onyx (deep, authoritative)</option>
                  <option value="nova">Nova (female, warm)</option>
                  <option value="shimmer">Shimmer (female, gentle)</option>
                </select>
              </div>
            </div>
          )}

          {/* TTS Speed (common to both) */}
          <div className="mt-4">
            <label className="block text-sm text-prism-text-muted mb-2">Speech Speed: <span className="text-prism-accent">{settings.voice.tts_speed.toFixed(1)}x</span></label>
            <input
              type="range"
              min="0.5"
              max="2.0"
              step="0.1"
              value={settings.voice.tts_speed}
              onChange={(e) => handleChange("tts_speed", parseFloat(e.target.value))}
              className="w-full h-2 bg-prism-darker rounded-lg appearance-none accent-prism-accent"
            />
            <div className="flex justify-between text-xs text-prism-text-muted mt-1">
              <span>0.5x (slow)</span>
              <span>1.0x (normal)</span>
              <span>2.0x (fast)</span>
            </div>
          </div>
        </div>
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