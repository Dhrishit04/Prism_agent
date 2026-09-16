/// Frontend service for managing settings via Tauri commands

import { invoke } from "@tauri-apps/api/core";

export interface VoiceSettings {
  voice_enabled: boolean;
  wake_word: string;
  wake_word_enabled: boolean;
  porcupine_access_key: string;
  stt_model: string;
  stt_language: string;
  tts_engine: string;
  tts_voice: string;
  tts_speed: number;
  openrouter_tts_voice: string;
}

export interface GoogleAuthSettings {
  client_id: string;
  client_secret: string;
  connected: boolean;
  email: string;
}

export interface Settings {
  openrouter_api_key: string;
  default_model: string;
  voice: VoiceSettings;
  automation_enabled: boolean;
  theme: string;
  language: string;
  google: GoogleAuthSettings;
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