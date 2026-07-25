# Prism AI Agent — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Phases use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a cross-platform (Windows + macOS) Jarvis-like AI desktop assistant with voice, LLM reasoning via OpenRouter, modular skills, and full GUI automation.

**Architecture:** Tauri v2 (Rust) desktop shell + React/TypeScript frontend + Python sidecar (FastAPI HTTP server on localhost:8765). Python handles voice pipeline, LLM calls, automation, and skills. Frontend provides chat UI, model picker, settings. Tauri manages native features (tray, hotkeys, window).

**Tech Stack:** Tauri v2, React 18, TypeScript, Tailwind CSS, Python 3.11+, FastAPI, Uvicorn, OpenRouter API, Porcupine, Whisper.cpp, Piper TTS, Playwright, PyAutoGUI, pytesseract, python-docx, openpyxl, pandas.

## Global Constraints

- Cross-platform: Windows + macOS from day one — no platform-specific code without abstraction layer
- Python sidecar runs as a subprocess spawned by Tauri via sidecar API
- Config stored at `~/.prism/settings.json` (not ~/.jarvis/)
- All settings are read/written directly by the frontend via Tauri fs API
- Voice processing runs locally; LLM reasoning runs via OpenRouter
- Python dependency management via `uv`
- Python sidecar bundled via PyInstaller for distribution
- OAuth tokens stored at `~/.prism/tokens/` with AES-256 encryption
- Project name: **Prism** (capital P, lowercase rism)

## Prerequisites

Before any phase, ensure these are installed:
- **Rust** (via rustup) — `rustc` 1.75+ and `cargo`
- **Node.js** 18+ with npm
- **Python** 3.11+ (check: `python --version`)
- **uv** (Python package manager) — `pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Tauri v2 CLI** — `cargo install tauri-cli --version "^2"`

---

## Phase 1: Tauri v2 Project Scaffolding + Basic Desktop Shell

**Goal:** Initialize the Tauri v2 project with React/TypeScript, create the basic window with system tray, and verify the app builds and runs.

**Files:**
- Create: `src-tauri/Cargo.toml`
- Create: `src-tauri/tauri.conf.json`
- Create: `src-tauri/src/main.rs`
- Create: `src-tauri/src/lib.rs`
- Create: `src-tauri/src/commands.rs`
- Create: `src-tauri/capabilities/default.json`
- Create: `package.json`
- Create: `tsconfig.json`
- Create: `tsconfig.node.json`
- Create: `vite.config.ts`
- Create: `index.html`
- Create: `src/main.tsx`
- Create: `src/App.tsx`
- Create: `src/App.css`
- Create: `src/vite-env.d.ts`
- Create: `src/styles/index.css`
- Create: `src/components/ChatView.tsx`
- Create: `src/components/Sidebar.tsx`
- Modify: `.gitignore`

**Deliverable:** Tauri window opens with basic chat UI shell, system tray icon with menu, Ctrl+Alt+P hotkey toggles window.

---

- [ ] **Step 1: Initialize Tauri v2 project scaffold**

Run the Tauri v2 init to create the base project structure:

```bash
cd c:/Users/Asus/Documents/GitHub/Prism
npm create tauri-app@latest Prism -- --template react-ts --manager npm
cd Prism
```

If the CLI prompts, answer:
- App name: `Prism`
- Package name: `prism`
- Frontend: React + TypeScript
- Tauri v2

*Note: If the interactive CLI doesn't work, manually create files using the templates below.*

---

- [ ] **Step 2: Configure package.json**

```json
{
  "name": "prism",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "tauri": "tauri"
  },
  "dependencies": {
    "@tauri-apps/api": "^2.0.0",
    "@tauri-apps/plugin-shell": "^2.0.0",
    "@tauri-apps/plugin-dialog": "^2.0.0",
    "@tauri-apps/plugin-autostart": "^2.0.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-markdown": "^9.0.0"
  },
  "devDependencies": {
    "@tauri-apps/cli": "^2.0.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.4.0",
    "vite": "^5.4.0"
  }
}
```

---

- [ ] **Step 3: Create vite.config.ts**

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const host = process.env.TAURI_DEV_HOST;

export default defineConfig(async () => ({
  plugins: [react()],
  clearScreen: false,
  server: {
    port: 1420,
    strictPort: true,
    host: host || false,
    hmr: host
      ? { protocol: "ws", host, port: 1421 }
      : undefined,
    watch: { ignored: ["**/src-tauri/**", "**/sidecar/**"] },
  },
}));
```

---

- [ ] **Step 4: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

---

- [ ] **Step 5: Create tsconfig.node.json**

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

---

- [ ] **Step 6: Create index.html**

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Prism</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

---

- [ ] **Step 7: Create tailwind and postcss configs**

Create `postcss.config.js`:
```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

Create `tailwind.config.js`:
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{js,jsx,ts,tsx}", "./index.html"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        prism: {
          dark: "#0f0f1a",
          darker: "#0a0a14",
          accent: "#6366f1",
          "accent-hover": "#818cf8",
          surface: "#1a1a2e",
          border: "#2d2d44",
          text: "#e2e8f0",
          "text-muted": "#94a3b8",
        },
      },
    },
  },
  plugins: [],
};
```

---

- [ ] **Step 8: Create src/styles/index.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  color-scheme: dark;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background-color: #0f0f1a;
  color: #e2e8f0;
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #2d2d44;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #3d3d54;
}
```

---

- [ ] **Step 9: Create src/main.tsx**

```typescript
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles/index.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

---

- [ ] **Step 10: Create src/App.tsx (basic shell with sidebar + chat)**

```typescript
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
```

---

- [ ] **Step 11: Create src-tauri/Cargo.toml**

```toml
[package]
name = "prism"
version = "0.1.0"
description = "Prism AI Agent - A Jarvis-like AI desktop assistant"
authors = ["Prism"]
edition = "2021"

[lib]
name = "prism_lib"
crate-type = ["staticlib", "cdylib", "rlib"]

[build-dependencies]
tauri-build = { version = "2", features = [] }

[dependencies]
tauri = { version = "2", features = ["tray-icon"] }
tauri-plugin-shell = "2"
tauri-plugin-dialog = "2"
tauri-plugin-autostart = "2"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
```

---

- [ ] **Step 12: Create src-tauri/build.rs**

```rust
fn main() {
    tauri_build::build()
}
```

---

- [ ] **Step 13: Create src-tauri/src/main.rs**

```rust
// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    prism_lib::run()
}
```

---

- [ ] **Step 14: Create src-tauri/src/lib.rs (system tray + hotkey)**

```rust
use tauri::{
    menu::{Menu, MenuItem},
    tray::TrayIconBuilder,
    Manager,
};

mod commands;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_autostart::init(
            tauri_plugin_autostart::MacosLauncher::LaunchAgent,
            Some(vec![]),
        ))
        .setup(|app| {
            // Build tray menu
            let show = MenuItem::with_id(app, "show", "Show/Hide", true, None::<&str>)?;
            let settings = MenuItem::with_id(app, "settings", "Settings", true, None::<&str>)?;
            let quit = MenuItem::with_id(app, "quit", "Quit", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&show, &settings, &quit])?;

            // Create tray icon
            let _tray = TrayIconBuilder::new()
                .tooltip("Prism")
                .icon(app.default_window_icon().unwrap().clone())
                .menu(&menu)
                .on_menu_event(|app, event| {
                    match event.id.as_ref() {
                        "show" => {
                            if let Some(window) = app.get_webview_window("main") {
                                let _ = window.show();
                                let _ = window.set_focus();
                            }
                        }
                        "settings" => {
                            // TODO: emit event to frontend to open settings
                        }
                        "quit" => {
                            app.exit(0);
                        }
                        _ => {}
                    }
                })
                .build(app)?;

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::greet,
            commands::toggle_window,
        ])
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                // Minimize to tray instead of closing
                let _ = window.hide();
                api.prevent_close();
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

---

- [ ] **Step 15: Create src-tauri/src/commands.rs**

```rust
use tauri::Manager;

#[tauri::command]
pub fn greet(name: &str) -> String {
    format!("Hello, {}! Prism is ready.", name)
}

#[tauri::command]
pub fn toggle_window(app: tauri::AppHandle) {
    if let Some(window) = app.get_webview_window("main") {
        if window.is_visible().unwrap_or(false) {
            let _ = window.hide();
        } else {
            let _ = window.show();
            let _ = window.set_focus();
        }
    }
}
```

---

- [ ] **Step 16: Create src-tauri/tauri.conf.json**

```json
{
  "$schema": "https://raw.githubusercontent.com/nicegui/tauri-v2-schema/refs/heads/main/tauri.conf.json",
  "productName": "Prism",
  "version": "0.1.0",
  "identifier": "com.prism.agent",
  "build": {
    "beforeDevCommand": "npm run dev",
    "devUrl": "http://localhost:1420",
    "beforeBuildCommand": "npm run build",
    "frontendDist": "../dist"
  },
  "app": {
    "withGlobalTauri": true,
    "windows": [
      {
        "title": "Prism AI Agent",
        "width": 900,
        "height": 600,
        "minWidth": 600,
        "minHeight": 400,
        "center": true,
        "decorations": true
      }
    ],
    "security": {
      "csp": null
    }
  },
  "bundle": {
    "active": true,
    "targets": "all",
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ]
  }
}
```

---

- [ ] **Step 17: Create src-tauri/capabilities/default.json**

```json
{
  "identifier": "default",
  "description": "Capability for the main window",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "shell:allow-open",
    "dialog:default",
    "autostart:default"
  ]
}
```

---

- [ ] **Step 18: Install dependencies and build**

```bash
cd c:/Users/Asus/Documents/GitHub/Prism
npm install
cargo tauri build
```

If `cargo tauri build` encounters issues, try:
```bash
cargo tauri dev
```

---

- [ ] **Step 19: Verify**

- Window opens titled "Prism AI Agent"
- Sidebar with "Prism" branding and navigation items
- Chat input area with Send button
- System tray icon appears with menu (Show/Hide, Settings, Quit)
- Closing the window minimizes to tray (doesn't quit)
- Empty state shows "How can I help you today?"

---

- [ ] **Step 20: Commit**

```bash
cd c:/Users/Asus/Documents/GitHub/Prism
git init
git add .
git commit -m "feat: scaffold Tauri v2 project with desktop shell, tray, and chat UI"
```

---

## Phase 2: Python Sidecar Foundation

**Goal:** Set up the Python sidecar with FastAPI HTTP server, health check endpoint, and Tauri integration to spawn/manage the sidecar process.

**Builds on:** Phase 1 (Tauri shell)

**Files:**
- Create: `sidecar/main.py`
- Create: `sidecar/server.py`
- Create: `sidecar/requirements.txt`
- Create: `sidecar/pyproject.toml`
- Modify: `src-tauri/src/lib.rs` (add sidecar spawn)
- Modify: `src-tauri/src/commands.rs` (add health check command)
- Modify: `src-tauri/Cargo.toml` (add reqwest dependency)
- Modify: `src-tauri/tauri.conf.json` (configure sidecar)

**Deliverable:** Tauri launches Python sidecar on startup, frontend can query health status, sidecar responds on localhost:8765.

---

- [ ] **Step 1: Create sidecar/pyproject.toml**

```toml
[project]
name = "prism-sidecar"
version = "0.1.0"
description = "Prism AI Agent Python sidecar"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "pydantic>=2.0.0",
    "httpx>=0.27.0",
    "openai>=1.0.0",
]

[build-system]
requires = ["setuptools>=75.0"]
build-backend = "setuptools.backends._legacy:_Backend"
```

---

- [ ] **Step 2: Create sidecar/requirements.txt**

```
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
pydantic>=2.0.0
httpx>=0.27.0
openai>=1.0.0
```

---

- [ ] **Step 3: Create sidecar/server.py**

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Prism Sidecar", version="0.1.0")


class HealthResponse(BaseModel):
    status: str
    version: str


class MessageRequest(BaseModel):
    message: str
    model: str = "anthropic/claude-3.5-sonnet"


class MessageResponse(BaseModel):
    response: str


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version="0.1.0")


@app.post("/chat", response_model=MessageResponse)
async def chat(request: MessageRequest):
    # TODO: Phase 3 — integrate with OpenRouter
    return MessageResponse(response=f"Echo: {request.message}")


@app.get("/models")
async def list_models():
    # TODO: Phase 3 — fetch from OpenRouter API
    return {
        "models": [
            {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet"},
            {"id": "openai/gpt-4o", "name": "GPT-4o"},
        ]
    }
```

---

- [ ] **Step 4: Create sidecar/main.py**

```python
"""Prism sidecar entry point — runs the FastAPI server."""

import uvicorn
from server import app


def main():
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")


if __name__ == "__main__":
    main()
```

---

- [ ] **Step 5: Install Python dependencies**

```bash
cd c:/Users/Asus/Documents/GitHub/Prism
cd sidecar
uv venv
uv pip install -r requirements.txt
```

---

- [ ] **Step 6: Verify sidecar runs independently**

```bash
cd c:/Users/Asus/Documents/GitHub/Prism/sidecar
uv run python main.py &
# In another terminal:
curl http://localhost:8765/health
# Expected: {"status":"ok","version":"0.1.0"}
# Kill the server
kill %1
```

---

- [ ] **Step 7: Add the sidecar binary to Tauri config**

Modify `src-tauri/tauri.conf.json` — add the `bundle.externalBin` and `shell.scope`:

```json
{
  // ... existing config ...
  "bundle": {
    "active": true,
    "targets": "all",
    "externalBin": ["sidecar/main.py"],
    "icon": [/* existing icons */]
  }
}
```

*Note: For development, we'll spawn the Python process directly. In production, the sidecar will be a PyInstaller binary. Update the path in Phase 12.*

---

- [ ] **Step 8: Add reqwest to Cargo.toml for HTTP calls to sidecar**

Modify `src-tauri/Cargo.toml`:

```toml
[dependencies]
# ... existing ...
reqwest = { version = "0.12", features = ["json"] }
tokio = { version = "1", features = ["full"] }
```

---

- [ ] **Step 9: Add sidecar spawn to lib.rs**

Modify `src-tauri/src/lib.rs` — add sidecar spawning in the `setup` closure:

```rust
use tauri_plugin_shell::ShellExt;

// Inside the setup closure, before Ok(())
// Spawn Python sidecar
let sidecar_status = std::sync::Arc::new(std::sync::Mutex::new(String::from("stopped")));
let status_clone = sidecar_status.clone();

// Spawn the Python sidecar process
let sidecar = app.shell()
    .command("python")
    .args(["sidecar/main.py"]);

// We use spawn() for the sidecar since it runs as a long-lived server
// For development, spawn directly. For production, use bundled binary.
std::thread::spawn(move || {
    let output = std::process::Command::new("python")
        .args(["sidecar/main.py"])
        .current_dir(std::env::current_dir().unwrap_or_default())
        .spawn();

    match output {
        Ok(mut child) => {
            *status_clone.lock().unwrap() = "running".to_string();
            let _ = child.wait();
            *status_clone.lock().unwrap() = "stopped".to_string();
        }
        Err(e) => {
            eprintln!("Failed to start sidecar: {}", e);
            *status_clone.lock().unwrap() = format!("error: {}", e);
        }
    }
});
```

---

- [ ] **Step 10: Add sidecar health check command**

Modify `src-tauri/src/commands.rs`:

```rust
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
pub struct HealthResponse {
    pub status: String,
    pub version: String,
}

#[tauri::command]
pub async fn check_sidecar_health() -> Result<HealthResponse, String> {
    let client = reqwest::Client::new();
    let resp = client
        .get("http://127.0.0.1:8765/health")
        .send()
        .await
        .map_err(|e| format!("Sidecar unreachable: {}", e))?;

    let health: HealthResponse = resp
        .json()
        .await
        .map_err(|e| format!("Invalid response: {}", e))?;

    Ok(health)
}
```

Register in lib.rs:
```rust
.invoke_handler(tauri::generate_handler![
    commands::greet,
    commands::toggle_window,
    commands::check_sidecar_health,
])
```

---

- [ ] **Step 11: Verify end-to-end**

1. Start the Python sidecar manually: `cd sidecar && uv run python main.py`
2. In another terminal: `curl http://localhost:8765/health` → `{"status":"ok","version":"0.1.0"}`
3. Start Tauri dev: `cargo tauri dev`
4. Sidecar should be reachable from the app

---

- [ ] **Step 12: Commit**

```bash
git add sidecar/ src-tauri/
git commit -m "feat: add Python sidecar with FastAPI, health check, and Tauri integration"
```

---

## Phase 3: OpenRouter LLM Integration + Streaming Chat

**Goal:** Connect the frontend chat to the Python sidecar, which calls OpenRouter API with streaming responses. Add a model picker dropdown.

**Builds on:** Phase 2 (sidecar running)

**Files:**
- Modify: `sidecar/server.py` (add streaming chat endpoint, OpenRouter models)
- Create: `sidecar/llm/openrouter.py`
- Create: `src/components/ModelPicker.tsx`
- Create: `src/services/api.ts`
- Create: `src/hooks/useChat.ts`
- Create: `src/services/settings.ts`
- Modify: `src/App.tsx` (wire up to sidecar, add model picker)

**Deliverable:** User types a message → Tauri IPC → Python sidecar → OpenRouter API → streaming response back to chat UI. Model picker dropdown works.

---

- [ ] **Step 1: Create sidecar/llm/openrouter.py**

```python
"""OpenRouter LLM client with streaming support."""

import json
from typing import AsyncGenerator

import httpx

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "anthropic/claude-3.5-sonnet"


class OpenRouterClient:
    def __init__(self, api_key: str, base_url: str = OPENROUTER_BASE):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://prism.ai",
            "X-Title": "Prism AI Agent",
        }

    async def chat_stream(
        self, messages: list[dict], model: str = DEFAULT_MODEL
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion from OpenRouter. Yields content deltas."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": model,
                    "messages": messages,
                    "stream": True,
                },
            ) as response:
                if response.status_code != 200:
                    error_body = await response.aread()
                    yield json.dumps({
                        "error": True,
                        "message": f"OpenRouter error {response.status_code}: {error_body.decode()}",
                    })
                    return

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield json.dumps({"content": content})
                        except json.JSONDecodeError:
                            continue

    async def list_models(self) -> list[dict]:
        """Fetch available models from OpenRouter."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.base_url}/models",
                headers=self.headers,
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
            return []

    async def chat(
        self, messages: list[dict], model: str = DEFAULT_MODEL
    ) -> dict:
        """Non-streaming chat completion."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                },
            )
            if response.status_code != 200:
                return {
                    "error": True,
                    "message": f"OpenRouter error {response.status_code}: {response.text}",
                }
            return response.json()
```

---

- [ ] **Step 2: Create sidecar/llm/__init__.py**

```python
from .openrouter import OpenRouterClient

__all__ = ["OpenRouterClient"]
```

---

- [ ] **Step 3: Update sidecar/server.py with streaming endpoint**

```python
import json
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from llm.openrouter import OpenRouterClient, DEFAULT_MODEL

app = FastAPI(title="Prism Sidecar", version="0.1.0")
_client: Optional[OpenRouterClient] = None


def get_client() -> OpenRouterClient:
    global _client
    if _client is None:
        # TODO: Phase 4 — read API key from settings
        api_key = ""
        _client = OpenRouterClient(api_key=api_key)
    return _client


class HealthResponse(BaseModel):
    status: str
    version: str


class MessageRequest(BaseModel):
    message: str
    model: str = DEFAULT_MODEL
    history: list[dict] = []


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version="0.1.0")


@app.post("/chat/stream")
async def chat_stream(request: MessageRequest):
    """Stream a chat response from OpenRouter."""
    client = get_client()
    if not client.api_key:
        # No API key configured — echo mode
        async def echo():
            yield f"data: {json.dumps({'content': 'Please configure your OpenRouter API key in Settings first.'})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(echo(), media_type="text/event-stream")

    messages = request.history + [{"role": "user", "content": request.message}]

    async def generate():
        async for chunk in client.chat_stream(messages, model=request.model):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/chat")
async def chat(request: MessageRequest):
    """Non-streaming chat (fallback)."""
    client = get_client()
    if not client.api_key:
        return {"response": "Please configure your OpenRouter API key in Settings first."}

    messages = request.history + [{"role": "user", "content": request.message}]
    result = await client.chat(messages, model=request.model)
    if result.get("error"):
        raise HTTPException(status_code=502, detail=result.get("message"))
    content = result["choices"][0]["message"]["content"]
    return {"response": content}


@app.get("/models")
async def list_models():
    """List available OpenRouter models."""
    client = get_client()
    if not client.api_key:
        return {"models": []}
    models = await client.list_models()
    return {"models": models}


@app.post("/configure")
async def configure(data: dict):
    """Set API key and reconfigure the client."""
    global _client
    api_key = data.get("api_key", "")
    _client = OpenRouterClient(api_key=api_key)
    return {"status": "ok"}
```

---

- [ ] **Step 4: Create src/services/api.ts**

```typescript
/// Tauri IPC wrapper for communicating with the Python sidecar

import { invoke } from "@tauri-apps/api/core";

export interface HealthStatus {
  status: string;
  version: string;
}

export async function checkHealth(): Promise<HealthStatus> {
  return invoke<HealthStatus>("check_sidecar_health");
}

export async function checkSidecarHealth(): Promise<HealthStatus> {
  try {
    const response = await fetch("http://127.0.0.1:8765/health");
    return await response.json();
  } catch {
    return { status: "unreachable", version: "0.0.0" };
  }
}

export async function sendChatMessage(
  message: string,
  model: string,
  history: { role: string; content: string }[] = []
): Promise<Response> {
  return fetch("http://127.0.0.1:8765/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, model, history }),
  });
}

export async function listModels(): Promise<{ id: string; name: string }[]> {
  try {
    const response = await fetch("http://127.0.0.1:8765/models");
    const data = await response.json();
    return data.models ?? [];
  } catch {
    return [];
  }
}

export async function configureApiKey(apiKey: string): Promise<void> {
  await fetch("http://127.0.0.1:8765/configure", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ api_key: apiKey }),
  });
}
```

---

- [ ] **Step 5: Create src/hooks/useChat.ts**

```typescript
import { useState, useCallback, useRef } from "react";
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
  const abortRef = useRef<AbortController | null>(null);

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
```

---

- [ ] **Step 6: Create src/components/ModelPicker.tsx**

```typescript
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
        className="flex items-center gap-2 px-3 py-1.5 text-xs bg-prism-surface border border-prism-border rounded-md text-prism-text hover:border-prism-accent transition-colors"
        disabled={loading}
      >
        {loading ? "Loading..." : displayName({ id: currentModel })}
        <span className="text-prism-text-muted">▼</span>
      </button>

      {isOpen && (
        <div className="absolute top-full mt-1 right-0 w-64 bg-prism-surface border border-prism-border rounded-lg shadow-xl z-50 max-h-64 overflow-y-auto">
          {models.map((model) => (
            <button
              key={model.id}
              onClick={() => {
                onModelChange(model.id);
                setIsOpen(false);
              }}
              className={`w-full text-left px-4 py-2 text-sm hover:bg-prism-accent/20 transition-colors ${
                currentModel === model.id
                  ? "text-prism-accent bg-prism-accent/10"
                  : "text-prism-text"
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
```

---

- [ ] **Step 7: Update App.tsx to wire up chat + model picker**

Replace the existing `App.tsx` content with the full implementation (streamlined):

```typescript
import { useState } from "react";
import { useChat } from "./hooks/useChat";
import { ModelPicker } from "./components/ModelPicker";

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

  const handleSend = () => {
    if (!input.trim() || isLoading) return;
    sendMessage(input.trim());
    setInput("");
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
            <button className="w-full text-left px-3 py-2 rounded bg-prism-surface text-prism-text hover:bg-prism-accent/20 transition-colors">
              💬 Chat
            </button>
            <button className="w-full text-left px-3 py-2 rounded text-prism-text-muted hover:bg-prism-surface transition-colors">
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
          <span className="text-sm text-prism-text-muted flex-1">Prism AI</span>
          <ModelPicker currentModel={currentModel} onModelChange={setCurrentModel} />
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex items-center justify-center h-full text-prism-text-muted">
              <div className="text-center">
                <h2 className="text-2xl font-bold text-prism-accent mb-2">
                  Prism
                </h2>
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

        {/* Input */}
        <div className="border-t border-prism-border p-4">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
              placeholder={
                isLoading ? "Waiting for response..." : "Type a message..."
              }
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
      </main>
    </div>
  );
}

export default App;
```

---

- [ ] **Step 8: Verify streaming chat end-to-end**

1. Start sidecar: `cd sidecar && uv run python main.py`
2. Configure API key: `curl -X POST http://localhost:8765/configure -H "Content-Type: application/json" -d '{"api_key":"sk-or-v1-..."}'`
3. Test streaming: `curl -X POST http://localhost:8765/chat/stream -H "Content-Type: application/json" -d '{"message":"Hello!"}'`
4. Expected: SSE stream with content chunks
5. Start Tauri: `cargo tauri dev`
6. Type a message in the chat → see streaming response appear

---

- [ ] **Step 9: Commit**

```bash
git add sidecar/llm/ src/
git commit -m "feat: integrate OpenRouter LLM with streaming chat UI and model picker"
```

---

## Phase 4: Settings System (Config Read/Write)

**Goal:** Implement `~/.prism/settings.json` read/write, Settings UI panel, API key configuration flow, and sync with Python sidecar.

**Builds on:** Phase 3

**Files:**
- Create: `src-tauri/src/commands/settings.rs`
- Create: `src/components/SettingsPanel.tsx`
- Create: `src/services/settings.ts`
- Modify: `src-tauri/src/lib.rs`
- Modify: `src-tauri/src/commands.rs`
- Modify: `src/App.tsx`
- Modify: `sidecar/server.py` (read settings on startup)

**Deliverable:** User can open Settings, enter API key, select default model, toggle voice/automation settings — all persisted to disk and read by Python sidecar.

---

**Note:** Detailed steps for Phase 4+ will be expanded when this phase is reached in execution. The high-level steps below define what needs to be built.

- [ ] Create settings Tauri commands (read/write `~/.prism/settings.json`)
- [ ] Create `src/services/settings.ts` — read/write settings from frontend
- [ ] Create `src/components/SettingsPanel.tsx` — settings UI with all sections
- [ ] Update sidecar to read settings on startup
- [ ] Wire Settings panel into App.tsx navigation
- [ ] Verify: enter API key → restart → API key persists
- [ ] Commit

---

## Phase 5: Skill System Foundation

**Goal:** Create the SkillBase abstract class, auto-discovery from `skills/` directory, and tool-calling integration with OpenRouter.

**Builds on:** Phase 3 (LLM integration)

**Files:**
- Create: `sidecar/skills/__init__.py`
- Create: `sidecar/skills/skill_base.py`
- Create: `sidecar/skills/registry.py`
- Modify: `sidecar/server.py` (expose skills as tools to LLM)

**Deliverable:** Skills directory is scanned at startup, skill definitions exposed to LLM as tools.

---

- [ ] **Step 1:** Create `sidecar/skills/skill_base.py` — abstract base class
- [ ] **Step 2:** Create `sidecar/skills/registry.py` — auto-discovery + registry
- [ ] **Step 3:** Create `sidecar/skills/__init__.py` — package init
- [ ] **Step 4:** Update `sidecar/server.py` — expose skill tools to LLM chat
- [ ] **Step 5:** Verify: registry discovers skills, returns tool definitions
- [ ] **Step 6:** Commit

---

## Phase 6: MVP Skills — Gmail + Google Calendar

**Goal:** Implement Gmail (read/send) and Google Calendar (list/create) skills with OAuth 2.0.

**Builds on:** Phase 5 (skill system)

**Files:**
- Create: `sidecar/auth/__init__.py`
- Create: `sidecar/auth/google_oauth.py`
- Create: `sidecar/skills/gmail.py`
- Create: `sidecar/skills/calendar.py`
- Create: `sidecar/auth/`
- Modify: `sidecar/server.py` (register new skills)

**Deliverable:** LLM can read Gmail inbox, send emails, check calendar, create events.

---

- [ ] **Step 1:** Create `sidecar/auth/google_oauth.py` — OAuth flow with token storage
- [ ] **Step 2:** Create `sidecar/skills/gmail.py` — read inbox, send email, search
- [ ] **Step 3:** Create `sidecar/skills/calendar.py` — list events, create events
- [ ] **Step 4:** Register skills in server.py
- [ ] **Step 5:** Test: OAuth flow works → skills execute correctly
- [ ] **Step 6:** Commit

---

## Phase 7: File System + App Launcher Skills

**Goal:** Implement File System (browse, read, search) and App Launcher (launch apps, focus windows) skills.

**Builds on:** Phase 5 (skill system)

**Files:**
- Create: `sidecar/skills/filesystem.py`
- Create: `sidecar/skills/app_launcher.py`
- Modify: `sidecar/server.py`

**Deliverable:** LLM can list files, read/write text files, launch apps, and manage windows.

---

- [ ] **Step 1:** Create `sidecar/skills/filesystem.py`
- [ ] **Step 2:** Create `sidecar/skills/app_launcher.py`
- [ ] **Step 3:** Register skills and test
- [ ] **Step 4:** Commit

---

## Phase 8: Voice Pipeline

**Goal:** Implement wake word detection (Porcupine), speech-to-text (Whisper.cpp), and text-to-speech (Piper TTS). Full voice conversation loop.

**Builds on:** Phase 3 (LLM + chat) / Phase 4 (settings)

**Files:**
- Create: `sidecar/voice/__init__.py`
- Create: `sidecar/voice/wake_word.py`
- Create: `sidecar/voice/stt.py`
- Create: `sidecar/voice/tts.py`
- Create: `sidecar/voice/pipeline.py`
- Create: `src/components/VoiceIndicator.tsx`
- Modify: `src/App.tsx` (add voice button)
- Modify: `sidecar/server.py` (voice endpoints)

**Deliverable:** User says "Hey Prism" → audio records → transcribes → LLM processes → response spoken aloud.

---

- [ ] **Step 1:** Install voice dependencies in requirements.txt
- [ ] **Step 2:** Create `sidecar/voice/wake_word.py`
- [ ] **Step 3:** Create `sidecar/voice/stt.py`
- [ ] **Step 4:** Create `sidecar/voice/tts.py`
- [ ] **Step 5:** Create `sidecar/voice/pipeline.py` — orchestrate the voice loop
- [ ] **Step 6:** Add voice endpoints to server.py
- [ ] **Step 7:** Create `src/components/VoiceIndicator.tsx`
- [ ] **Step 8:** Wire voice toggle into App.tsx
- [ ] **Step 9:** Test full voice loop
- [ ] **Step 10:** Commit

---

## Phase 9: Web Automation (Playwright)

**Goal:** LLM-driven web browser automation using Playwright. Headed and headless modes.

**Builds on:** Phase 3 (LLM tool calling)

**Files:**
- Create: `sidecar/automation/__init__.py`
- Create: `sidecar/automation/browser.py`
- Modify: `sidecar/server.py` (automation endpoints)
- Modify: `sidecar/llm/openrouter.py` (system prompt with automation tools)

**Deliverable:** LLM can navigate websites, click elements, type text, extract data, take screenshots.

---

- [ ] **Step 1:** Install Playwright in requirements.txt
- [ ] **Step 2:** Create `sidecar/automation/browser.py`
- [ ] **Step 3:** Add browser automation endpoints to server.py
- [ ] **Step 4:** Integrate automation tools into LLM system prompt
- [ ] **Step 5:** Test: LLM navigates to a URL and extracts information
- [ ] **Step 6:** Commit

---

## Phase 10: Desktop GUI Automation

**Goal:** Desktop GUI automation via accessibility APIs (primary) and OCR/PyAutoGUI (fallback).

**Builds on:** Phase 9 (automation engine)

**Files:**
- Create: `sidecar/automation/desktop.py`
- Create: `sidecar/automation/ocr.py`
- Modify: `sidecar/server.py`
- Modify: `sidecar/automation/__init__.py`

**Deliverable:** LLM can find windows, read UI elements, click buttons, type text — with automatic fallback to OCR when accessibility APIs aren't available.

---

- [ ] **Step 1:** Install desktop automation dependencies (pywinauto for Windows)
- [ ] **Step 2:** Create `sidecar/automation/desktop.py`
- [ ] **Step 3:** Create `sidecar/automation/ocr.py`
- [ ] **Step 4:** Add desktop automation to server.py
- [ ] **Step 5:** Test on Windows: find Notepad, type text
- [ ] **Step 6:** Commit

---

## Phase 11: Office Automation

**Goal:** Word document editing (python-docx) and Excel pivot table creation (openpyxl + pandas).

**Builds on:** Phase 9 (automation engine)

**Files:**
- Create: `sidecar/automation/office.py`
- Modify: `sidecar/server.py`

**Deliverable:** LLM can read/edit .docx files and create Excel pivot tables from CSV data.

---

- [ ] **Step 1:** Install office automation dependencies
- [ ] **Step 2:** Create `sidecar/automation/office.py`
- [ ] **Step 3:** Add office endpoints to server.py
- [ ] **Step 4:** Test: create pivot table from CSV
- [ ] **Step 5:** Commit

---

## Phase 12: Automation Orchestration + Polish

**Goal:** Unified automation engine where LLM chooses between web/desktop/office automation. Cross-platform testing, error handling improvements, polish.

**Builds on:** Phases 9-11

**Files:**
- Create: `sidecar/automation/orchestrator.py`
- Modify: `sidecar/server.py`
- Modify: `sidecar/llm/openrouter.py` (unified tool definitions)
- Various polish tasks

**Deliverable:** Full end-to-end: "Check my email and create a summary in a Word doc" works via a single voice command.

---

- [ ] **Step 1:** Create `sidecar/automation/orchestrator.py`
- [ ] **Step 2:** Update LLM system prompt with unified tools
- [ ] **Step 3:** Cross-platform testing
- [ ] **Step 4:** Error handling and edge cases
- [ ] **Step 5:** UI polish, loading states, error messages
- [ ] **Step 6:** Final commit

---

## Execution Plan

Each phase builds on the previous one. Start with Phase 1, get it working, then proceed.

**Recommended order:**
1. **Phase 1** → Tauri desktop shell (this session)
2. **Phase 2** → Python sidecar foundation
3. **Phase 3** → OpenRouter + streaming chat (first real functionality)
4. **Phase 4** → Settings system
5. **Phase 5** → Skill system foundation
6. **Phase 6** → Gmail + Calendar (first real skills)
7. **Phase 7** → File System + App Launcher
8. **Phase 8** → Voice pipeline (significant milestone)
9. **Phase 9** → Web automation
10. **Phase 10** → Desktop automation
11. **Phase 11** → Office automation
12. **Phase 12** → Orchestration + polish

**Each phase takes 1-2 sessions. After each phase, take a break to avoid context exhaustion.**