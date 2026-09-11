const BASE_URL = "";

async function parseError(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data?.detail === "string") return data.detail;
    if (typeof data?.detail === "object" && Array.isArray(data.detail)) {
      return JSON.stringify(data.detail);
    }
  } catch {
    /* not JSON */
  }
  return `Request failed (${response.status})`;
}

export async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(BASE_URL + path, init);
  if (!response.ok) {
    const message = await parseError(response);
    throw new Error(message);
  }
  return (await response.json()) as T;
}

export function postFormData<T>(path: string, form: FormData): Promise<T> {
  return request<T>(path, { method: "POST", body: form });
}