use serde::{Deserialize, Serialize};
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