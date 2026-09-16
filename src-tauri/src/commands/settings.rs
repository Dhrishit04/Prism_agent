use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

#[derive(Debug, Serialize, Deserialize, Clone, Default)]
pub struct VoiceSettings {
    pub voice_enabled: bool,
    pub wake_word: String,
    pub wake_word_enabled: bool,
    pub porcupine_access_key: String,
    pub stt_model: String,
    pub stt_language: String,
    pub tts_engine: String,
    pub tts_voice: String,
    pub tts_speed: f32,
    pub openrouter_tts_voice: String,
}

#[derive(Debug, Serialize, Deserialize, Clone, Default)]
pub struct AutomationSettings {
    pub automation_enabled: bool,
    pub browser_timeout: u32,
    pub headless_default: bool,
    pub ocr_enabled: bool,
    pub office_use_com: bool,
}

impl Default for AutomationSettings {
    fn default() -> Self {
        Self {
            automation_enabled: false,
            browser_timeout: 30000,
            headless_default: true,
            ocr_enabled: false,
            office_use_com: false,
        }
    }
}

impl Default for VoiceSettings {
    fn default() -> Self {
        Self {
            voice_enabled: false,
            wake_word: "jarvis".to_string(),
            wake_word_enabled: false,
            porcupine_access_key: "".to_string(),
            stt_model: "tiny".to_string(),
            stt_language: "en".to_string(),
            tts_engine: "piper".to_string(),
            tts_voice: "en_US-lessac-medium".to_string(),
            tts_speed: 1.0,
            openrouter_tts_voice: "alloy".to_string(),
        }
    }
}

#[derive(Debug, Serialize, Deserialize, Clone, Default)]
pub struct GoogleAuthSettings {
    pub client_id: String,
    pub client_secret: String,
    pub connected: bool,
    pub email: String,
}

#[derive(Debug, Serialize, Deserialize, Clone, Default)]
pub struct Settings {
    pub openrouter_api_key: String,
    pub default_model: String,
    pub voice: VoiceSettings,
    pub automation: AutomationSettings,
    pub theme: String,
    pub language: String,
    pub google: GoogleAuthSettings,
}

impl Settings {
    fn settings_path() -> PathBuf {
        let mut path = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
        path.push(".prism");
        path.push("settings.json");
        path
    }

    pub fn load() -> Result<Self, String> {
        let path = Self::settings_path();
        if path.exists() {
            let content = fs::read_to_string(&path).map_err(|e| format!("Failed to read settings: {}", e))?;
            let settings: Settings = serde_json::from_str(&content).map_err(|e| format!("Failed to parse settings: {}", e))?;
            Ok(settings)
        } else {
            // Return defaults
            Ok(Settings {
                default_model: "anthropic/claude-3.5-sonnet".to_string(),
                theme: "dark".to_string(),
                language: "en".to_string(),
                ..Default::default()
            })
        }
    }

    pub fn save(&self) -> Result<(), String> {
        let path = Self::settings_path();
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).map_err(|e| format!("Failed to create settings directory: {}", e))?;
        }
        let content = serde_json::to_string_pretty(self).map_err(|e| format!("Failed to serialize settings: {}", e))?;
        fs::write(&path, content).map_err(|e| format!("Failed to write settings: {}", e))?;
        Ok(())
    }
}

#[tauri::command]
pub async fn get_settings() -> Result<Settings, String> {
    Settings::load()
}

#[tauri::command]
pub async fn save_settings(settings: Settings) -> Result<(), String> {
    settings.save()
}

#[tauri::command]
pub async fn reset_settings() -> Result<Settings, String> {
    let defaults = Settings {
        default_model: "anthropic/claude-3.5-sonnet".to_string(),
        theme: "dark".to_string(),
        language: "en".to_string(),
        ..Default::default()
    };
    defaults.save()?;
    Ok(defaults)
}

#[tauri::command]
pub async fn get_config_path() -> Result<String, String> {
    let path = Settings::settings_path();
    Ok(path.to_string_lossy().to_string())
}