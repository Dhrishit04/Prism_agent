/// Frontend service for managing settings via Tauri commands

import { invoke } from "@tauri-apps/api/core";

export interface Settings {
  openrouter_api_key: string;
  default_model: string;
  voice_enabled: boolean;
  automation_enabled: boolean;
  theme: string;
  language: string;
}

export async function getSettings(): Promise<Settings> {
  return invoke<Settings>("get_settings");
}

export async function saveSettings(settings: Settings): Promise<void> {
  return invoke("save_settings", { settings });
}

export async function resetSettings(): Promise<Settings> {
  return invoke<Settings>("reset_settings");
}

export async function getConfigPath(): Promise<string> {
  return invoke<string>("get_config_path");
}