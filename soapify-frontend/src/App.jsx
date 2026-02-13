import { useEffect, useMemo, useState } from 'react';
import {
  generateNote,
  getDashboardData,
  getMe,
  getNoteStatus,
  getPatientHistory,
  loginUser,
  registerUser,
  updateNote,
} from './api';

const tokenKey = 'soapify_token';

export default function App() {
  const [token, setToken] = useState(localStorage.getItem(tokenKey) || '');
  const [me, setMe] = useState(null);
  const [dashboard, setDashboard] = useState([]);
  const [history, setHistory] = useState([]);
  const [selected, setSelected] = useState(null);
  const [editor, setEditor] = useState('');
  const [loading, setLoading] = useState(false);
  const [pollingId, setPollingId] = useState(null);
  const [toast, setToast] = useState('');

  const [authMode, setAuthMode] = useState('login');
  const [authForm, setAuthForm] = useState({
    email: '',
    password: '',
    full_name: '',
    role: 'doctor',
    specialization: '',
  });

  const [noteForm, setNoteForm] = useState({
    patient_name: '',
    age: '',
    transcript_text: '',
  });

  const stats = useMemo(() => {
    const processing = dashboard.filter((n) => n.status === 'PROCESSING').length;
    const completed = dashboard.filter((n) => n.status === 'COMPLETED').length;
    const failed = dashboard.filter((n) => n.status === 'FAILED').length;
    return { total: dashboard.length, processing, completed, failed };
  }, [dashboard]);

  useEffect(() => {
    if (!token) return;
    getMe(token)
      .then(setMe)
      .catch(() => logout());
  }, [token]);

  useEffect(() => {
    if (!token) return;
    refreshDashboard();
  }, [token]);

  useEffect(() => {
    if (!token || !pollingId) return;
    const timer = setInterval(async () => {
      try {
        const data = await getNoteStatus(token, pollingId);
        if (selected && selected.note_id === pollingId) {
          setSelected((prev) => ({ ...prev, status: data.status }));
          setEditor(data.content || '');
        }
        if (data.status !== 'PROCESSING') {
          setPollingId(null);
          refreshDashboard();
        }
      } catch {
        setPollingId(null);
      }
    }, 3000);

    return () => clearInterval(timer);
  }, [token, pollingId, selected]);

  const logout = () => {
    localStorage.removeItem(tokenKey);
    setToken('');
    setMe(null);
    setDashboard([]);
    setSelected(null);
    setHistory([]);
    setEditor('');
  };

  const refreshDashboard = async () => {
    const data = await getDashboardData(token);
    setDashboard(data);
  };

  const onAuthSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setToast('');

    try {
      if (authMode === 'register') {
        await registerUser({
          email: authForm.email,
          password: authForm.password,
          full_name: authForm.full_name,
          role: authForm.role,
          specialization: authForm.specialization || null,
        });
        setToast('Registered. Now login.');
        setAuthMode('login');
      } else {
        const res = await loginUser(authForm.email, authForm.password);
        localStorage.setItem(tokenKey, res.access_token);
        setToken(res.access_token);
        setToast(`Welcome, ${res.name}`);
      }
    } catch (err) {
      setToast(err.message);
    } finally {
      setLoading(false);
    }
  };

  const onCreateNote = async (e) => {
    e.preventDefault();
    setLoading(true);
    setToast('');

    try {
      if (!noteForm.age) {
        throw new Error('Age is required by backend.');
      }

      const payload = {
        patient_name: noteForm.patient_name || 'Unknown Patient',
        age: Number(noteForm.age),
        transcript_text: noteForm.transcript_text,
      };

      const data = await generateNote(token, payload);
      setPollingId(data.id);
      setToast(`SOAP #${data.soap_number} started`);
      setNoteForm({ patient_name: '', age: '', transcript_text: '' });
      await refreshDashboard();
    } catch (err) {
      setToast(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadNote = async (note) => {
    setLoading(true);
    setSelected(note);
    setToast('');

    try {
      const [statusData, historyData] = await Promise.all([
        getNoteStatus(token, note.note_id),
        getPatientHistory(token, note.patient_id),
      ]);
      setEditor(statusData.content || '');
      setHistory(historyData);
      if (statusData.status === 'PROCESSING') {
        setPollingId(note.note_id);
      }
    } catch (err) {
      setToast(err.message);
    } finally {
      setLoading(false);
    }
  };

  const onSaveNote = async () => {
    if (!selected) return;
    setLoading(true);

    try {
      await updateNote(token, selected.note_id, editor);
      setToast('SOAP note updated');
      await refreshDashboard();
    } catch (err) {
      setToast(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!token || !me) {
    return (
      <main className="min-h-screen bg-base bg-aura text-slate-100 p-6">
        <div className="mx-auto max-w-xl rounded-2xl border border-slate-800 bg-panel/90 p-6 shadow-glow">
          <h1 className="text-3xl font-semibold">SOAPify Dashboard</h1>
          <p className="mt-2 text-slate-400">Login or register to manage notes.</p>

          <div className="mt-6 flex gap-3">
            <button
              className={`rounded-lg px-4 py-2 ${authMode === 'login' ? 'bg-accent text-slate-950' : 'bg-card'}`}
              onClick={() => setAuthMode('login')}
            >
              Login
            </button>
            <button
              className={`rounded-lg px-4 py-2 ${authMode === 'register' ? 'bg-accent text-slate-950' : 'bg-card'}`}
              onClick={() => setAuthMode('register')}
            >
              Register
            </button>
          </div>

          <form className="mt-6 space-y-4" onSubmit={onAuthSubmit}>
            <input
              className="w-full rounded-xl border border-slate-700 bg-card p-3"
              placeholder="Email"
              type="email"
              value={authForm.email}
              onChange={(e) => setAuthForm({ ...authForm, email: e.target.value })}
              required
            />
            <input
              className="w-full rounded-xl border border-slate-700 bg-card p-3"
              placeholder="Password"
              type="password"
              value={authForm.password}
              onChange={(e) => setAuthForm({ ...authForm, password: e.target.value })}
              required
            />

            {authMode === 'register' && (
              <>
                <input
                  className="w-full rounded-xl border border-slate-700 bg-card p-3"
                  placeholder="Full name"
                  value={authForm.full_name}
                  onChange={(e) => setAuthForm({ ...authForm, full_name: e.target.value })}
                  required
                />
                <input
                  className="w-full rounded-xl border border-slate-700 bg-card p-3"
                  placeholder="Specialization (optional)"
                  value={authForm.specialization}
                  onChange={(e) => setAuthForm({ ...authForm, specialization: e.target.value })}
                />
              </>
            )}

            <button
              className="w-full rounded-xl bg-mint px-4 py-3 font-semibold text-slate-900 disabled:opacity-60"
              disabled={loading}
            >
              {loading ? 'Please wait...' : authMode === 'register' ? 'Create account' : 'Login'}
            </button>
          </form>

          {toast && <p className="mt-4 text-sm text-sky-300">{toast}</p>}
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-base bg-aura text-slate-100 p-4 md:p-6">
      <div className="mx-auto grid max-w-7xl grid-cols-1 gap-4 lg:grid-cols-[280px_1fr]">
        <aside className="rounded-2xl border border-slate-800 bg-panel/95 p-4">
          <div className="mb-4 flex items-start justify-between">
            <div>
              <h2 className="text-lg font-semibold">{me.full_name}</h2>
              <p className="text-xs uppercase text-slate-400">{me.role}</p>
            </div>
            <button className="rounded bg-card px-3 py-1 text-sm" onClick={logout}>Logout</button>
          </div>

          <div className="space-y-2 text-sm">
            <p>Total Notes: {stats.total}</p>
            <p>Completed: {stats.completed}</p>
            <p>Processing: {stats.processing}</p>
            <p>Failed: {stats.failed}</p>
          </div>

          <div className="mt-4 max-h-[52vh] space-y-2 overflow-auto pr-1">
            {dashboard.map((note) => (
              <button
                key={note.note_id}
                onClick={() => loadNote(note)}
                className={`w-full rounded-xl border p-3 text-left text-sm transition ${selected?.note_id === note.note_id ? 'border-accent bg-card' : 'border-slate-700 bg-slate-900/40'}`}
              >
                <p className="font-semibold">SOAP #{note.soap_number}</p>
                <p className="text-slate-300">{note.patient_name}</p>
                <p className="text-xs text-slate-400">{note.status}</p>
              </button>
            ))}
          </div>
        </aside>

        <section className="space-y-4">
          <article className="rounded-2xl border border-slate-800 bg-panel/95 p-4">
            <h3 className="text-xl font-semibold">Generate SOAP Note</h3>
            <form className="mt-4 grid gap-3" onSubmit={onCreateNote}>
              <div className="grid gap-3 md:grid-cols-2">
                <input
                  className="rounded-xl border border-slate-700 bg-card p-3"
                  placeholder="Patient name"
                  value={noteForm.patient_name}
                  onChange={(e) => setNoteForm({ ...noteForm, patient_name: e.target.value })}
                />
                <input
                  className="rounded-xl border border-slate-700 bg-card p-3"
                  placeholder="Age"
                  type="number"
                  min="0"
                  value={noteForm.age}
                  onChange={(e) => setNoteForm({ ...noteForm, age: e.target.value })}
                  required
                />
              </div>
              <textarea
                className="min-h-36 rounded-xl border border-slate-700 bg-card p-3"
                placeholder="Paste doctor-patient transcript..."
                value={noteForm.transcript_text}
                onChange={(e) => setNoteForm({ ...noteForm, transcript_text: e.target.value })}
                required
              />
              <button className="rounded-xl bg-accent px-4 py-3 font-semibold text-slate-950 disabled:opacity-60" disabled={loading}>
                Submit for generation
              </button>
            </form>
          </article>

          <article className="rounded-2xl border border-slate-800 bg-panel/95 p-4">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-xl font-semibold">SOAP Editor</h3>
              <button
                className="rounded-xl bg-mint px-4 py-2 font-semibold text-slate-900 disabled:opacity-60"
                onClick={onSaveNote}
                disabled={!selected || loading}
              >
                Save Update
              </button>
            </div>
            <textarea
              className="min-h-64 w-full rounded-xl border border-slate-700 bg-card p-3"
              value={editor}
              onChange={(e) => setEditor(e.target.value)}
              placeholder="Select a note from the sidebar to view/edit"
            />
          </article>

          <article className="rounded-2xl border border-slate-800 bg-panel/95 p-4">
            <h3 className="text-xl font-semibold">Patient History</h3>
            <div className="mt-3 space-y-2">
              {history.length === 0 && <p className="text-slate-400">No history loaded.</p>}
              {history.map((item, idx) => (
                <div key={`${item.soap_number}-${idx}`} className="rounded-xl border border-slate-700 bg-card p-3">
                  <p className="text-sm font-semibold">SOAP #{item.soap_number}</p>
                  <p className="text-xs text-slate-400">{item.date}</p>
                  <p className="mt-2 whitespace-pre-wrap text-sm text-slate-200">{item.content}</p>
                </div>
              ))}
            </div>
          </article>

          {toast && <p className="text-sm text-sky-300">{toast}</p>}
        </section>
      </div>
    </main>
  );
}
