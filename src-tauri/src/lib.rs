// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Command;
use std::env;

use tauri::{
    menu::{Menu, MenuItem},
    tray::TrayIconBuilder,
    Manager,
    Emitter,
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
            // Spawn Python sidecar
            let sidecar_status = std::sync::Arc::new(std::sync::Mutex::new(String::from("stopped")));
            let status_clone = sidecar_status.clone();

            // Spawn the Python sidecar process
            std::thread::spawn(move || {
                let output = Command::new("python")
                    .args(["sidecar/main.py"])
                    .current_dir(env::current_dir().unwrap_or_default())
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

            // Build tray menu
            let show = MenuItem::with_id(app, "show", "Show/Hide", true, None::<&str>)?;
            let settings = MenuItem::with_id(app, "settings", "Settings", true, None::<&str>)?;
            let quit = MenuItem::with_id(app, "quit", "Quit", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&show, &settings, &quit])?;

            // Create tray icon
            let _tray = TrayIconBuilder::new()
                .tooltip("Tesseract")
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
                            if let Some(window) = app.get_webview_window("main") {
                                let _ = window.show();
                                let _ = window.set_focus();
                                // Emit event to open settings panel
                                let _ = app.emit("open-settings", ());
                            }
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
            commands::check_sidecar_health,
            commands::settings::get_settings,
            commands::settings::save_settings,
            commands::settings::reset_settings,
            commands::settings::get_config_path,
            commands::voice::get_voice_status,
            commands::voice::start_wake_word,
            commands::voice::stop_wake_word,
            commands::voice::start_stt_recording,
            commands::voice::stop_stt_recording,
            commands::voice::speak_text,
            commands::voice::stop_tts,
            commands::voice::start_voice_pipeline,
            commands::voice::stop_voice_pipeline,
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