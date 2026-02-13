const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const buildHeaders = (token, extra = {}) => ({
  ...(token ? { Authorization: `Bearer ${token}` } : {}),
  ...extra,
});

function formatErrorDetail(detail, fallback = 'Request failed') {
  if (!detail) return fallback;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'string') return item;
        const field = Array.isArray(item?.loc) ? item.loc.slice(1).join('.') : '';
        const msg = item?.msg || JSON.stringify(item);
        return field ? `${field}: ${msg}` : msg;
      })
      .join(' | ');
  }
  if (typeof detail === 'object') {
    return detail.message || JSON.stringify(detail);
  }
  return fallback;
}

export async function registerUser(payload) {
  const res = await fetch(`${API_BASE}/api/v1/auth/register`, {
    method: 'POST',
    headers: buildHeaders(null, { 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(formatErrorDetail(err.detail, 'Registration failed'));
  }

  return res.json();
}

export async function loginUser(email, password) {
  const body = new URLSearchParams();
  body.set('username', email);
  body.set('password', password);

  const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(formatErrorDetail(err.detail, 'Login failed'));
  }

  return res.json();
}

export async function getMe(token) {
  return authedGet('/api/v1/users/me', token);
}

export async function generateNote(token, payload) {
  return authedPost('/api/v1/notes/Generate', token, payload);
}

export async function getDashboardData(token) {
  return authedGet('/api/v1/notes/DashboardData', token);
}

export async function getNoteStatus(token, noteId) {
  return authedGet(`/api/v1/notes/Status/${noteId}`, token);
}

export async function updateNote(token, noteId, updatedContent) {
  return authedPut(`/api/v1/notes/Update/${noteId}`, token, {
    updated_content: updatedContent,
  });
}

export async function getPatientHistory(token, patientId) {
  return authedGet(`/api/v1/notes/PatientHistory/${patientId}`, token);
}

async function authedGet(path, token) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: buildHeaders(token),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(formatErrorDetail(err.detail, 'Request failed'));
  }

  return res.json();
}

async function authedPost(path, token, payload) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: buildHeaders(token, { 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(formatErrorDetail(err.detail, 'Request failed'));
  }

  return res.json();
}

async function authedPut(path, token, payload) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'PUT',
    headers: buildHeaders(token, { 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(formatErrorDetail(err.detail, 'Request failed'));
  }

  return res.json();
}
