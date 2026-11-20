// The browser only calls Spring Boot; Flask stays behind the Java API.
const LOCAL_API_BASE = 'http://localhost:8080/api';
const RENDER_API_BASE = 'https://mailguard-api-q3o6.onrender.com/api';
const configuredApi = String(window.MAILGUARD_API || '').trim().replace(/\/$/, '');
const hostname = location.hostname.toLowerCase();
const isRenderHost = hostname.endsWith('.onrender.com');
const isLoopback = value => /^https?:\/\/(localhost|127\.0\.0\.1|\[::1\])(?::|\/|$)/i.test(value);
const API_BASE = isRenderHost
  ? (configuredApi && !isLoopback(configuredApi) ? configuredApi : RENDER_API_BASE)
  : (configuredApi || LOCAL_API_BASE);

async function api(path, options = {}) {
  if (location.protocol === 'file:') {
    throw new Error('Open Mailguard through its local web server at http://localhost:5500. Opening index.html directly blocks browser API requests.');
  }
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), options.timeoutMs || 180000);
  const requestOptions = { ...options, signal: options.signal || controller.signal, headers: { ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...(options.headers || {}) } };
  delete requestOptions.timeoutMs;
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, requestOptions);
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('The service is taking longer than expected to wake. Please retry in a moment.');
    throw new Error('Could not reach the Java API. Check that the backend is running and try again.');
  } finally {
    clearTimeout(timeout);
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `Request failed (${response.status}).`);
  return data;
}
