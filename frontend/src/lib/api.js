// Thin client for the PyroScope backend. In dev, Vite proxies /api -> http://127.0.0.1:8000.
// Override with VITE_API_BASE_URL (e.g. a deployed backend URL).
const BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

function qs(params = {}) {
  const p = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') p.append(k, v);
  });
  const s = p.toString();
  return s ? `?${s}` : '';
}

async function get(path, params) {
  const res = await fetch(`${BASE}/api/v1${path}${qs(params)}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export const api = {
  health: () => get('/health'),
  datasets: () => get('/datasets'),
  meta: (p) => get('/meta', p),
  summary: (filters) => get('/stats/summary', filters),
  events: (filters) => get('/events', filters), // GeoJSON FeatureCollection
  event: (id, p) => get(`/events/${encodeURIComponent(id)}`, p),
  detections: (filters) => get('/detections', filters),
  timeseries: (filters) => get('/stats/timeseries', filters),
  regions: (filters) => get('/stats/regions', filters),
  evaluation: (p) => get('/evaluation', p),
  exportUrl: (fmt, filters) => `${BASE}/api/v1/export/events.${fmt}${qs(filters)}`,
  refresh: async (days = 3) => {
    const res = await fetch(`${BASE}/api/v1/refresh?days=${days}`, { method: 'POST' });
    if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || 'Refresh failed');
    return res.json();
  },
  refreshStatus: () => get('/refresh/status'),
};
