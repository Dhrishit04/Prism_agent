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