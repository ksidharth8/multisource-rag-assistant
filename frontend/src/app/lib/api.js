import { API_BASE } from "./constants";

export async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, options);
  let data = null;

  try {
    data = await res.json();
  } catch {
    data = null;
  }

  if (!res.ok) {
    const detail = data?.detail || data?.message || `Request failed with ${res.status}`;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }

  return data;
}