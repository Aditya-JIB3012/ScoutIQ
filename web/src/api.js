async function request(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    headers: { "content-type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || data.detail || `Request failed (${response.status})`);
  return data;
}

export const api = {
  health: () => request("/health"),
  metadata: () => request("/metadata"),
  players: (query = "") => request(`/players${query ? `?${query}` : ""}`),
  player: (id) => request(`/players/${encodeURIComponent(id)}`),
  compare: (first, second) => request(`/compare?first=${encodeURIComponent(first)}&second=${encodeURIComponent(second)}`),
  opportunities: (budget, under24) => request(`/opportunities?budget=${budget}&under_24=${under24}&limit=20`),
  simulate: (input) => request("/simulate", { method: "POST", body: JSON.stringify(input) }),
  analytics: () => request("/analytics"),
  getWatchlist: (visitorId) => request(`/watchlist/${visitorId}`),
  saveWatchlist: (visitorId, playerIds) => request(`/watchlist/${visitorId}`, {
    method: "PUT", body: JSON.stringify({ playerIds }),
  }),
};
