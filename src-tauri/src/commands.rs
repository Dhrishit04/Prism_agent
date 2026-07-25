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