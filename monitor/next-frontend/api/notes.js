let csrfToken = "";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`/api${path}`, {
      ...options,
      credentials: "same-origin",
      cache: "no-store",
      headers: {
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...(options.method && options.method !== "GET" ? { "X-CSRF-Token": csrfToken } : {}),
      },
    });
  } catch {
    throw new ApiError("API에 연결할 수 없습니다. Flask 서버와 연결 설정을 확인해 주세요.", 0);
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.error || "API 요청에 실패했습니다. Flask 서버를 확인해 주세요.", response.status);
  }
  if (!data) throw new ApiError("API 응답을 읽을 수 없습니다.", response.status);
  if (data.csrf_token) csrfToken = data.csrf_token;
  return data;
}

export const getSession = () => request("/auth/me");
export const login = (username, password) => request("/auth/login", { method: "POST", body: JSON.stringify({ username, password }) });
export const logout = () => request("/auth/logout", { method: "POST" });
export const listNotes = () => request("/notes");
export const getNote = (id) => request(`/notes/${id}`);
export const createNote = (values) => request("/notes", { method: "POST", body: JSON.stringify(values) });
export const updateNote = (id, values) => request(`/notes/${id}`, { method: "PUT", body: JSON.stringify(values) });
export const deleteNote = (id) => request(`/notes/${id}`, { method: "DELETE" });
