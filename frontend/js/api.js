// The browser only calls Spring Boot; Flask stays behind the Java API.
const LOCAL_API_BASE = 'http://localhost:8080/api';
const RENDER_API_BASE = 'https://mailguard-api-q3o6.onrender.com/api';
const isRenderHost = location.hostname.toLowerCase().endsWith('.onrender.com');
const configuredApi = window.MAILGUARD_API;
const configuredIsLocal = configuredApi && /^https?:\/\/(localhost|127\.0\.0\.1|\[::1\])(?::|\/|$)/i.test(configuredApi);
const API_BASE = isRenderHost
  ? (configuredApi && !configuredIsLocal ? configuredApi : RENDER_API_BASE)
  : (configuredApi || LOCAL_API_BASE);
async function api(path, options = {}) {
  let response;
  try { response = await fetch(`${API_BASE}${path}`, { headers: { 'Content-Type': 'application/json', ...(options.headers || {}) }, ...options }); }
  catch { throw new Error('Could not reach the application backend. Check the service status and try again.'); }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `Request failed (${response.status}).`);
  return data;
}
