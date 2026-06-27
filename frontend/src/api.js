const BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  getCases: () => request("/api/cases"),
  getCase: (id) => request(`/api/cases/${id}`),
  getClue: (caseId, toolType) => request(`/api/cases/${caseId}/tools/${toolType}`),
  verifyGuess: (caseId, guess, username) =>
    request(`/api/cases/${caseId}/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ guess, username }),
    }),
  getLeaderboard: () => request("/api/leaderboard"),
  detectUpload: (file) => {
    const form = new FormData();
    form.append("file", file);
    return request("/api/detect-upload", { method: "POST", body: form });
  },
};
