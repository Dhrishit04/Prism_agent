# Prism — Jarvis-like AI Agent: Design Specification

**Date:** 2025-07-25
**Status:** Approved Design
**Project:** Prism AI Agent

---

## 1. Overview

Prism is a cross-platform (Windows + macOS) AI desktop assistant inspired by Jarvis. It combines a native desktop shell with a Python AI/voice engine, providing full voice interaction, LLM-powered reasoning via OpenRouter, a modular skill system, and **full GUI automation capabilities** — the agent can control websites, desktop apps, and documents like a human would.

**Core philosophy:** Local-first for privacy and speed, cloud for intelligence. All voice processing runs locally; LLM reasoning runs via OpenRouter with user-selectable models.

---

## 2. Architecture

### 2.1 High-Level Layered Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                 Tauri v2 Desktop Shell (Rust)                 │
│  ┌────────────────────────────────────────────────────────┐  │
│  │            React / TypeScript Frontend                 │  │
│  │   (Chat UI, Model Picker, Settings, Voice Toggle)      │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Tauri Core (Rust)                                     │  │
│  │  - System tray + menu                                  │  │
│  │  - Global hotkeys (Ctrl+Alt+P to toggle)               │  │
│  │  - Platform-specific app launcher                      │  │
│  │  - Window management (show/hide/minimize to tray)      │  │
│  │  - Auto-updater (Tauri updater)                        │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────┬────────────────────────────────────┘
                          │ IPC (Tauri Commands)
                          ▼
┌──────────────────────────────────────────────────────────────┐
│               Python Sidecar (Local HTTP server)              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Voice Pipeline                                        │  │
│  │  - Porcupine (wake word detection)                     │  │
│  │  - Whisper.cpp (Speech-to-Text, local)                 │  │
│  │  - Piper / OpenRouter TTS (Text-to-Speech)             │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  OpenRouter LLM Client                                 │  │
│  │  - Streaming API calls + model switching               │  │
│  │  - System prompt + tool definitions for skills/automation│  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Skills Engine                                         │  │
│  │  - Gmail, Google Calendar, File System, App Launcher   │  │
│  │  - Auto-discover from skills/ directory                │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Automation Engine (NEW)                               │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │  Web Automation (Playwright)                     │  │  │
│  │  │  - Headed browser for complex sites              │  │  │
│  │  │  - Headless for simple API calls/ scraping       │  │  │
│  │  │  - LLM decides mode per task                     │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │  Desktop GUI Automation                          │  │  │
│  │  │  - OS accessibility APIs (primary)               │  │  │
│  │  │  - PyAutoGUI + OCR fallback (for any app)        │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │  Office Automation                               │  │  │
│  │  │  - python-docx (Word), openpyxl (Excel)          │  │  │
│  │  │  - win32com for Office app control (Windows)     │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Communication Model

- **Tauri ↔ Frontend:** Standard Tauri IPC (invoke/listen commands via `@tauri-apps/api`)
- **Tauri ↔ Python Sidecar:** Tauri's sidecar/Command API — spawns Python process as a child, communicates via stdio/HTTP. The Python sidecar runs a local HTTP server on `localhost:8765`.
- **Frontend ↔ Python Sidecar:** Frontend sends commands via Tauri IPC → Tauri forwards to Python sidecar via HTTP. Responses stream back through the same chain.
- **Startup flow:** Tauri launches → starts Python sidecar → sidecar health-check → UI ready

### 2.3 Cross-Platform Strategy

| Component | Windows | macOS |
|-----------|---------|-------|
| WebView | WebView2 (built-in Win10+) | WebKit (WKWebView) |
| Python sidecar | PyInstaller .exe | PyInstaller .app bundle |
| App launch | `CreateProcess` / ShellExecute | `NSWorkspace` |
| File system | Win32 API / `pathlib` | POSIX / `pathlib` |
| OAuth redirect | localhost server | localhost server |
| Desktop automation | `pywinauto` / `uiautomation` | Accessibility APIs (AX) |
| Installer | .msi / .exe | .dmg / .app |

---

## 3. Voice Pipeline

### 3.1 Components

| Stage | Technology | Why | Platform |
|-------|-----------|-----|----------|
| Wake word | Porcupine (Picovoice) | Local, low-latency, cross-platform, free tier | Python binding |
| Speech-to-Text | Whisper.cpp via `whisper-cpp-python` | Local, fast (tiny/base models), 99+ languages | Python |
| Text-to-Speech | Piper TTS (primary) / OpenRouter TTS (fallback) | Local, fast, natural voices; cloud fallback for quality | Python |

### 3.2 Voice Flow

```
User speaks → Porcupine detects "Hey Prism" → Audio recording begins
→ Silence detection stops recording → Whisper transcribes audio to text
→ Text sent to LLM (OpenRouter) → LLM response received
→ Response streamed to UI + spoken via Piper TTS
→ Back to listening for wake word
```

### 3.3 Model Picker & OpenRouter Integration

- **Frontend:** Dropdown/select component that fetches available models from OpenRouter API (`/v1/models`)
- **Config persistence:** Selected model stored in `~/.prism/config.toml`
- **API calls:** Python sidecar calls OpenRouter's `/v1/chat/completions` with the selected model ID
- **Streaming:** SSE streaming from OpenRouter → Python sidecar → Tauri IPC → Frontend (real-time chat output)
- **Fallback:** If OpenRouter is unreachable, the agent shows a clear error and retries

---

## 4. Automation Engine (NEW)

This is the core differentiating capability of Prism — the ability to **see and interact with apps** like a human. The Automation Engine consists of three subsystems that the LLM orchestrates based on the user's request.

### 4.1 Web Automation

**Approach:** Playwright (Python) — the LLM decides per-task whether to use headed or headless mode.

| Mode | When Used | Example |
|------|-----------|---------|
| **Headed browser** | Complex multi-step tasks needing visual feedback | Raising a support ticket, filling a form, navigating a web app |
| **Headless browser** | Simple data extraction or API calls | Fetching a page, checking a status, scraping structured data |

**LLM-driven workflow:**
```
User: "Write an email to support about my game ban"

1. LLM determines: needs web browsing to find game company's support page
2. Automation Engine launches Playwright (headed) → navigates to game site
3. LLM receives page content/screenshot → decides next action (click "Support")
4. Repeats: observe → decide → act until the support contact form is found
5. Form is filled with user's details (email, account info, description)
6. Result reported back to user
```

**Key features:**
- LLM receives page snapshots (DOM text + optional screenshots) to decide actions
- Actions: `navigate(url)`, `click(element)`, `type(text)`, `select(option)`, `extract(selector)`, `screenshot()`
- Session persistence (cookies, localStorage) for logged-in sessions
- Timeout handling — if stuck, LLM can backtrack or try alternative paths

### 4.2 Desktop GUI Automation

**Approach:** Hybrid — OS accessibility APIs as primary, computer vision (PyAutoGUI + OCR) as fallback.

| Layer | Technology | Reliability | Speed |
|-------|-----------|-------------|-------|
| **Primary** | OS accessibility APIs (`pywinauto`/`UIA` on Windows, AX APIs on macOS) | High — reads actual UI elements | Fast |
| **Fallback** | PyAutoGUI + Tesseract OCR | Medium — works on any app | Slower |

**LLM-driven workflow:**
```
User: "Check WhatsApp for new messages"

1. LLM determines: needs to open WhatsApp Desktop and read messages
2. Automation Engine launches WhatsApp via App Launcher skill
3. Accessibility API scans the WhatsApp window for UI elements
4. If accessibility tree is available → parse message list directly
5. If no accessibility tree → take screenshot → OCR → analyze
6. New messages extracted and reported to user
```

**Key features:**
- `find_window(title)`, `get_ui_elements()`, `click(element)`, `type(text)`, `screenshot(region)`
- Automatic fallback: try accessibility first, then OCR
- Window management: focus, resize, minimize, restore
- Element identification via accessibility name, role, or screen coordinates

### 4.3 Office Automation

**Approach:** Programmatic libraries as primary, app control as fallback.

| Task | Primary Method | Fallback Method |
|------|---------------|-----------------|
| **Word editing** | `python-docx` (fast, reliable, no Word needed) | `win32com` (control Word app for complex formatting) |
| **Excel pivot tables** | `openpyxl` + `pandas` (read CSV → create pivot → save as .xlsx) | `win32com` (control Excel app for complex operations) |
| **PowerPoint** | `python-pptx` | `win32com` |

**Example workflows:**
```
User: "Create a pivot table from the CSV in Downloads"

1. File System skill locates the CSV in Downloads folder
2. pandas reads the CSV into a DataFrame
3. openpyxl creates a new Excel workbook
4. Pivot table is built from the DataFrame
5. File saved to Desktop (or user-specified location)
6. User notified: "Pivot table created at Desktop/sales_report.xlsx"
```

```
User: "Edit my essay in the Word file on Desktop"

1. File System skill locates the .docx file
2. python-docx reads the document
3. LLM analyzes the essay content
4. Modifications made (grammar, structure, wording)
5. File saved with changes tracked (optional)
6. Summary of changes reported to user
```

### 4.4 Automation Orchestration

The LLM receives a unified set of automation tools and decides which to use:

```
Tools available to LLM:
├── web_navigate(url)          # Launch browser and go to URL
├── web_click(selector)        # Click element on page
├── web_type(selector, text)   # Type into form field
├── web_extract(selector)      # Get text from element
├── web_screenshot()           # Take page screenshot
├── desktop_find_window(title) # Find/activate app window
├── desktop_get_elements()     # Get accessibility tree
├── desktop_click(element)     # Click UI element
├── desktop_type(text)         # Type into focused element
├── desktop_screenshot()       # Take screen region shot
├── desktop_ocr(region)        # Extract text from image
├── office_read_doc(path)      # Read Word document
├── office_edit_doc(path, edits) # Edit Word document
├── excel_create_pivot(csv, config) # Create pivot table
└── file_system.*              # File operations
```

---

## 5. Skill/Plugin System

### 5.1 Architecture

Each skill is a Python class in `skills/` directory, auto-discovered at startup:

```python
class SkillBase(ABC):
    name: str                    # "gmail"
    description: str             # "Send and read Gmail messages"
    schemas: List[ToolSchema]    # JSON schemas for LLM tool calling
    
    @abstractmethod
    async def execute(self, intent: str, params: dict) -> SkillResult:
        ...
```

### 5.2 Skill Discovery

- `skills/` directory is scanned at startup
- Each `.py` file exporting a class that inherits from `SkillBase` is registered
- LLM receives skill registry as tool definitions (OpenRouter tool-calling format)
- LLM decides which skill(s) to invoke based on user intent

### 5.3 MVP Skills

| Skill | Capabilities | Auth |
|-------|-------------|------|
| **Gmail** | Read inbox, send email, search, draft replies | OAuth 2.0 (Google) |
| **Google Calendar** | List events, create events, check schedule | OAuth 2.0 (Google) |
| **File System** | List files, read/write text, search, get file info | Local (sandboxed path) |
| **App Launcher** | Launch apps by name, list running apps, focus window | Platform-specific |

### 5.4 OAuth Flow

- Google OAuth 2.0 handled in Python sidecar
- Opens browser for user login → redirects to `localhost:8765/oauth/callback`
- Tokens stored securely in `~/.prism/tokens/` (encrypted)
- Refresh token flow for long-lived access

---

## 6. Configuration & Data

### 6.1 Settings File (`~/.prism/settings.json`)

Following the Claude Code pattern, all agent configuration is stored in a single `settings.json` file that the **UI reads and writes directly** (via Tauri's file system API). No backend API needed for settings — the frontend reads/writes the JSON file, and the Python sidecar reads it on startup.

```json
{
  "env": {
    "OPENROUTER_API_KEY": "sk-or-v1-...",
    "OPENROUTER_BASE_URL": "https://openrouter.ai/api"
  },
  "model": "anthropic/claude-3.5-sonnet",
  "models": {
    "enabled": ["anthropic/claude-3.5-sonnet", "openai/gpt-4o", "meta-llama/llama-3.1-70b-instruct"],
    "favorites": ["anthropic/claude-3.5-sonnet"]
  },
  "voice": {
    "wake_word": "hey prism",
    "wake_word_enabled": true,
    "stt_model": "tiny",
    "tts_voice": "default",
    "tts_speed": 1.0
  },
  "automation": {
    "browser_timeout": 30,
    "headless_default": false,
    "ocr_enabled": true,
    "office_use_com": false
  },
  "skills": {
    "enabled": ["gmail", "calendar", "filesystem", "app_launcher"],
    "mcp_servers": {
      "filesystem": {
        "command": "python",
        "args": ["-m", "mcp_filesystem"],
        "env": {
          "ALLOWED_PATHS": "/home/user,/workspace"
        }
      }
    }
  },
  "plugins": {
    "enabled": ["automation", "voice", "browser"],
    "mcp_servers": {
      "browser": {
        "command": "npx",
        "args": ["@anthropic-ai/mcp-playwright"],
        "env": {}
      }
    }
  },
  "theme": "dark",
  "start_on_boot": true,
  "minimize_to_tray": true,
  "global_hotkey": "Ctrl+Alt+P",
  "effort_level": "high",
  "auto_updates": true
}
```

### 6.2 Settings UI

The **Settings panel** in the frontend directly reads/writes `~/.prism/settings.json` via Tauri's file system commands:

| UI Section | Maps to settings.json key |
|------------|--------------------------|
| **API Key** | `env.OPENROUTER_API_KEY` |
| **Model Selection** | `model` + `models.enabled` |
| **Voice Settings** | `voice.*` |
| **Automation Settings** | `automation.*` |
| **Skills & Plugins** | `skills.enabled` + `plugins.enabled` |
| **MCP Servers** | `skills.mcp_servers` + `plugins.mcp_servers` |
| **Theme** | `theme` |
| **Hotkey** | `global_hotkey` |
| **Startup Behavior** | `start_on_boot`, `minimize_to_tray` |

### 6.3 Token Storage

- OAuth tokens stored at `~/.prism/tokens/` with AES-256 encryption
- API keys in settings.json (flagged in `.gitignore`)

---

## 7. User Interface

### 7.1 Frontend Screens

| Screen | Purpose |
|--------|---------|
| **Chat View** | Main conversation — text input + streaming LLM responses + voice toggle |
| **Model Picker** | Dropdown to switch OpenRouter models |
| **Settings** | Direct JSON editor for `~/.prism/settings.json` + structured UI for API keys, models, voice, automation, MCP servers, plugins |
| **Voice Status** | Visual indicator: listening / speaking / idle |
| **Automation Feed** (optional) | Real-time view of what the agent is doing (browser tabs, app actions, screenshots) |

### 7.2 System Tray

- Icon in system tray (Windows/macOS)
- Right-click menu: Show/Hide, Settings, Quit
- Left-click: Toggle window visibility

### 7.3 Global Hotkey

- `Ctrl+Alt+P` (Windows) / `Cmd+Opt+P` (macOS) to toggle window
- Configurable in settings

---

## 8. Project Structure

```
Prism/
├── src-tauri/              # Tauri Rust backend
│   ├── src/
│   │   ├── main.rs         # App entry, tray, hotkeys
│   │   ├── commands.rs     # Tauri IPC commands
│   │   ├── sidecar.rs      # Python sidecar lifecycle
│   │   └── platform/       # Windows/macOS platform specifics
│   ├── Cargo.toml
│   └── tauri.conf.json
├── src/                    # React/TypeScript frontend
│   ├── App.tsx
│   ├── components/
│   │   ├── ChatView.tsx
│   │   ├── ModelPicker.tsx
│   │   ├── SettingsPanel.tsx
│   │   └── VoiceIndicator.tsx
│   ├── hooks/
│   ├── services/
│   │   └── api.ts          # Tauri IPC wrapper
│   └── styles/
├── sidecar/                # Python sidecar
│   ├── main.py             # Entry point, HTTP server
│   ├── server.py           # FastAPI/Flask server
│   ├── voice/
│   │   ├── wake_word.py    # Porcupine
│   │   ├── stt.py          # Whisper
│   │   └── tts.py          # Piper TTS
│   ├── llm/
│   │   └── openrouter.py   # OpenRouter client
│   ├── automation/
│   │   ├── browser.py      # Playwright web automation
│   │   ├── desktop.py      # Desktop GUI automation (accessibility + OCR)
│   │   ├── office.py       # Word/Excel/PowerPoint automation
│   │   └── orchestrator.py # LLM-controlled action loop
│   ├── skills/
│   │   ├── __init__.py
│   │   ├── skill_base.py   # Abstract base class
│   │   ├── gmail.py
│   │   ├── calendar.py
│   │   ├── filesystem.py
│   │   └── app_launcher.py
│   ├── auth/
│   │   └── google_oauth.py
│   └── requirements.txt
├── docs/
│   └── superpowers/specs/
├── package.json
├── tsconfig.json
└── README.md
```

---

## 9. Build & Distribution

### 9.1 Development Workflow

```bash
# 1. Python sidecar
cd sidecar
uv venv
uv pip install -r requirements.txt
python main.py

# 2. Tauri + frontend (separate terminal)
cd Prism
npm install
npm run tauri dev
```

### 9.2 Production Build

- `uv` for Python dependency management (fast, deterministic)
- PyInstaller bundles Python sidecar into single binary
- `cargo tauri build` produces platform installers
- CI/CD pipeline for automated cross-platform builds

### 9.3 Dependencies

**Rust (Tauri):**
- tauri v2
- tauri-plugin-shell (sidecar management)
- tauri-plugin-dialog
- tauri-plugin-autostart

**Python:**
- fastapi + uvicorn (HTTP server)
- openai (OpenRouter-compatible SDK)
- pvporcupine (wake word)
- whisper-cpp-python (STT)
- piper-tts (TTS)
- google-auth, google-api-python-client (Google APIs)
- pydantic (config/schemas)
- cryptography (token encryption)
- **playwright** (web automation — NEW)
- **pywinauto** (Windows accessibility — NEW)
- **pyautogui** (screen automation — NEW)
- **pytesseract** (OCR — NEW)
- **pillow** (image processing — NEW)
- **python-docx** (Word automation — NEW)
- **openpyxl** (Excel automation — NEW)
- **pandas** (data processing — NEW)
- **pywin32** (COM automation, Windows only — NEW)

**Frontend:**
- React 18
- TypeScript
- @tauri-apps/api v2
- Tailwind CSS
- react-markdown (LLM response rendering)

---

## 10. Success Criteria (MVP)

- [ ] User can type a message and get an LLM response via OpenRouter
- [ ] User can switch between OpenRouter models
- [ ] Voice: wake word detection → STT → LLM → TTS loop works
- [ ] Gmail: read inbox, send email
- [ ] Calendar: check schedule, create events
- [ ] File System: browse, read, search files
- [ ] App Launcher: open applications by voice/text command
- [ ] **Web Automation: LLM can navigate a website, find info, fill forms, submit data**
- [ ] **Desktop GUI: LLM can interact with desktop apps via accessibility APIs**
- [ ] **Office: LLM can create Excel pivot tables from CSV, edit Word documents**
- [ ] **WhatsApp: LLM can read messages from WhatsApp Desktop**
- [ ] Cross-platform: works on both Windows and macOS
- [ ] System tray: minimize to tray, right-click menu
- [ ] Global hotkey: toggle window visibility

---

## 11. Out of Scope (MVP)

- Camera access (future)
- Microphone always-listening when disabled
- Phone integration
- Third-party app integrations beyond listed skills
- Custom wake word training
- Multi-user support
- Mobile app companion