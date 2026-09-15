/// Frontend service for voice control via Tauri commands

import { invoke } from "@tauri-apps/api/core";

export interface VoiceStatus {
  wake_word: any;
  stt: any;
  tts: any;
  pipeline: any;
  enabled: boolean;
}

export interface VoiceCommandResponse {
  success: boolean;
  data?: any;
  error?: string;
}

export async function getVoiceStatus(): Promise<VoiceStatus> {
  return invoke<VoiceStatus>("get_voice_status");
}

export async function startWakeWord(): Promise<VoiceCommandResponse> {
  return invoke<VoiceCommandResponse>("start_wake_word");
}

export async function stopWakeWord(): Promise<VoiceCommandResponse> {
  return invoke<VoiceCommandResponse>("stop_wake_word");
}

export async function startSttRecording(): Promise<VoiceCommandResponse> {
  return invoke<VoiceCommandResponse>("start_stt_recording");
}

export async function stopSttRecording(): Promise<VoiceCommandResponse> {
  return invoke<VoiceCommandResponse>("stop_stt_recording");
}

export async function speakText(text: string): Promise<VoiceCommandResponse> {
  return invoke<VoiceCommandResponse>("speak_text", { text });
}

export async function stopTts(): Promise<VoiceCommandResponse> {
  return invoke<VoiceCommandResponse>("stop_tts");
}

export async function startVoicePipeline(): Promise<VoiceCommandResponse> {
  return invoke<VoiceCommandResponse>("start_voice_pipeline");
}

export async function stopVoicePipeline(): Promise<VoiceCommandResponse> {
  return invoke<VoiceCommandResponse>("stop_voice_pipeline");
}