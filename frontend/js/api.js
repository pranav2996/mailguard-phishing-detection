// The browser only calls Spring Boot; Flask stays behind the Java API.
const API_BASE = window.MAILGUARD_API || 'http://localhost:8080/api';
async function api(path, options = {}) {
  let response;
  try { response = await fetch(`${API_BASE}${path}`, { headers: { 'Content-Type': 'application/json', ...(options.headers || {}) }, ...options }); }
  catch { throw new Error('Could not reach the application backend. Start the Java service on port 8080.'); }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `Request failed (${response.status}).`);
  return data;
}
