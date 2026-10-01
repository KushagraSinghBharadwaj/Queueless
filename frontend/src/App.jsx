import { useEffect, useMemo, useState } from "react";
import "./App.css";

const API_BASE = "http://127.0.0.1:8000/api";

const FACILITY_META = {
  Canteen: { icon: "🍽️", label: "Main Canteen", location: "Block A" },
  Library: { icon: "📚", label: "Central Library", location: "Block C" },
  "Printing Shop": { icon: "🖨️", label: "Printing Shop", location: "Block B" },
  "Computer Lab": { icon: "💻", label: "Computer Lab", location: "Block D" },
  "Admin Office": { icon: "🏢", label: "Admin Office", location: "Main Building" },
  "Bus Stop": { icon: "🚌", label: "College Bus", location: "Main Gate" },
};

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });

  let body = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }

  if (!response.ok) {
    throw new Error(body?.detail || `Request failed (${response.status})`);
  }

  return body;
}

function normalizeFacility(f) {
  const meta = FACILITY_META[f.name] || {};
  return {
    ...f,
    icon: meta.icon || "🏫",
    displayName: meta.label || f.name,
    displayLocation: meta.location || f.location,
  };
}

export default function App() {
  const [page, setPage] = useState("home");
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("queueless_user")) || null;
    } catch {
      return null;
    }
  });
  const [view, setView] = useState("student");
  const [facilities, setFacilities] = useState([]);
  const [queues, setQueues] = useState({});
  const [tickets, setTickets] = useState([]);
  const [search, setSearch] = useState("");
  const [staffId, setStaffId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [toasts, setToasts] = useState([]);
  const [analytics, setAnalytics] = useState(null);

  const notify = (text) => {
    const id = Date.now() + Math.random();
    setToasts((items) => [...items, { id, text }]);
    window.setTimeout(
      () => setToasts((items) => items.filter((item) => item.id !== id)),
      5000
    );
  };

  const loadFacilities = async (silent = false) => {
    if (!silent) setLoading(true);
    else setRefreshing(true);

    try {
      setError("");
      const data = await api("/facilities");
      const normalized = data.map(normalizeFacility);
      setFacilities(normalized);
      if (!staffId && normalized.length) setStaffId(normalized[0].id);

      const queueResults = await Promise.all(
        normalized.map(async (facility) => {
          const queue = await api(`/queue/${facility.id}`);
          return [facility.id, queue];
        })
      );

      setQueues(Object.fromEntries(queueResults));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const loadAnalytics = async () => {
    try {
      const data = await api("/analytics/summary");
      setAnalytics(data);
    } catch {
      // Analytics is supplemental; the live queue remains usable.
    }
  };

  useEffect(() => {
    loadFacilities();
    loadAnalytics();

    const timer = window.setInterval(() => {
      loadFacilities(true);
      loadAnalytics();
    }, 5000);

    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (user) localStorage.setItem("queueless_user", JSON.stringify(user));
    else localStorage.removeItem("queueless_user");
  }, [user]);

  const ticketsForUser = useMemo(
    () =>
      tickets.filter((ticket) => ticket.user_id === user?.email),
    [tickets, user]
  );

  const shown = facilities.filter((f) =>
    f.displayName.toLowerCase().includes(search.toLowerCase()) ||
    f.name.toLowerCase().includes(search.toLowerCase())
  );

  const facilityCards = shown.map((facility) => {
    const queue = queues[facility.id];
    const wait = queue?.entries?.[0]?.estimated_wait_minutes ?? 0;
    const waiting = queue?.waiting_count ?? 0;
    return {
      ...facility,
      queue,
      waiting,
      wait: Math.max(0, Math.round(wait)),
      status: wait < 8 ? "available" : wait < 15 ? "moderate" : "busy",
    };
  });

  const board = [...facilityCards]
    .sort((a, b) => b.wait - a.wait)
    .slice(0, 4);

  const total = facilityCards.reduce((sum, f) => sum + f.waiting, 0);
  const averageWait = facilityCards.length
    ? Math.round(
        facilityCards.reduce((sum, f) => sum + f.wait, 0) /
          facilityCards.length
      )
    : 0;

  const tabs = ["student", ...(user?.role === "staff" || user?.role === "admin" ? ["staff"] : []), ...(user?.role === "admin" ? ["admin"] : [])];

  const join = async (facility) => {
    if (!user) {
      setPage("login");
      return;
    }

    try {
      const result = await api("/queue/join", {
        method: "POST",
        body: JSON.stringify({
          facility_id: facility.id,
          user_id: user.email,
        }),
      });

      setTickets((current) => {
        const withoutExisting = current.filter((item) => item.entry_id !== result.entry_id && item.facility_id !== facility.id);
        return [...withoutExisting, result];
      });

      await loadFacilities(true);
      notify(
        `Joined ${facility.displayName}. Position ${result.position}. AI predicted wait: ${Math.round(result.estimated_wait_minutes ?? 0)} min.`
      );
    } catch (err) {
      notify(err.message);
    }
  };

  const leave = async (ticket) => {
    try {
      await api("/queue/leave", {
        method: "POST",
        body: JSON.stringify({
          entry_id: ticket.entry_id,
          user_id: user.email,
        }),
      });

      setTickets((current) =>
        current.filter((item) => item.entry_id !== ticket.entry_id)
      );
      await loadFacilities(true);
      notify("You left the queue.");
    } catch (err) {
      notify(err.message);
    }
  };

  const advance = async () => {
    if (!staffId) return;
    try {
      const result = await api(`/queue/advance/${staffId}`, {
        method: "POST",
      });
      await loadFacilities(true);
      notify(
        result.now_serving_entry_id
          ? "Queue advanced. The next person is now being served."
          : "Queue advanced. Nobody is waiting."
      );
    } catch (err) {
      notify(err.message);
    }
  };

  const logout = () => {
    setUser(null);
    setTickets([]);
    setView("student");
    setPage("home");
  };

  const doneLogin = (u) => {
    setUser(u);
    setPage("home");
    setView("student");
  };

  if (page === "login") {
    return (
      <Login
        onBack={() => setPage("home")}
        onLogin={doneLogin}
        onSwitch={() => setPage("signup")}
      />
    );
  }

  if (page === "signup") {
    return (
      <Signup
        onBack={() => setPage("home")}
        onSignup={doneLogin}
        onSwitch={() => setPage("login")}
      />
    );
  }

  const staffFacility = facilities.find((f) => f.id === staffId);

  return (
    <div className="app">
      <nav className="navbar">
        <div className="logo">
          <span className="logo-icon">Q</span>QueueLess
        </div>

        {tabs.length > 1 && (
          <div className="tabs" role="tablist">
            {tabs.map((tab) => (
              <button
                key={tab}
                role="tab"
                aria-selected={view === tab}
                className={view === tab ? "on" : ""}
                onClick={() => setView(tab)}
              >
                {tab[0].toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
        )}

        {user ? (
          <div className="user">
            <span>{user.email}</span>
            <button className="btn ghost" onClick={logout}>Log out</button>
          </div>
        ) : (
          <div className="user">
            <button className="btn ghost" onClick={() => setPage("login")}>Log in</button>
            <button className="btn dark" onClick={() => setPage("signup")}>Sign up</button>
          </div>
        )}
      </nav>

      <div className="toasts" aria-live="polite">
        {toasts.map((toast) => (
          <div key={toast.id} className="toast">{toast.text}</div>
        ))}
      </div>

      {error && (
        <div className="panel" style={{ margin: "24px auto", maxWidth: 1200 }}>
          <h3>Backend connection problem</h3>
          <p>{error}</p>
          <button className="btn dark" onClick={() => loadFacilities()}>
            Retry
          </button>
        </div>
      )}

      {view === "student" && (
        <>
          <header className="hero">
            <div className="hero-text">
              <h1>Know the wait before you walk.</h1>
              <p>
                Live queue data from the QueueLess backend, with waiting-time
                predictions from the trained Random Forest model.
              </p>
              <a className="btn dark big" href="#facilities">See all facilities</a>
              <div className="hero-stats">
                <b>{total}</b> people waiting now <i />{" "}
                <b>{averageWait}</b> min average AI wait
              </div>
            </div>

            <div className="board" aria-label="Longest AI predicted waits">
              <div className="board-head">
                <span className="dot" />
                AI predicted waits
                <span style={{ marginLeft: "auto" }}>
                  {refreshing ? "Updating…" : "Live"}
                </span>
              </div>

              {loading ? (
                <div className="board-row">Loading live queue data…</div>
              ) : board.length ? (
                board.map((facility) => (
                  <div className="board-row" key={facility.id}>
                    <span>{facility.icon} {facility.displayName}</span>
                    <b className={facility.status}>
                      {facility.wait}<small> min</small>
                    </b>
                  </div>
                ))
              ) : (
                <div className="board-row">No facilities available.</div>
              )}
            </div>
          </header>

          {ticketsForUser.length > 0 && (
            <section className="mine">
              <h2>Your live queues</h2>
              <div className="mine-list">
                {ticketsForUser.map((ticket) => {
                  const facility = facilities.find((f) => f.id === ticket.facility_id);
                  if (!facility) return null;

                  return (
                    <div className="ticket" key={ticket.entry_id}>
                      <div className="ticket-no">#{ticket.position ?? "—"}</div>
                      <div className="ticket-body">
                        <b>{facility.displayName}</b>
                        <span>
                          {ticket.status === "serving"
                            ? "You're being served now"
                            : ticket.position === 1
                              ? "You're next"
                              : `${Math.max(0, (ticket.position ?? 1) - 1)} ahead · AI predicts about ${Math.round(ticket.estimated_wait_minutes ?? 0)} min`}
                        </span>
                      </div>
                      {ticket.status === "waiting" && (
                        <button className="btn ghost" onClick={() => leave(ticket)}>
                          Leave
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            </section>
          )}

          <section className="facilities" id="facilities">
            <div className="section-head">
              <div>
                <h2>Campus facilities</h2>
                <p>
                  Queue counts come from SQLite. Wait estimates come from the
                  trained AI model.
                </p>
              </div>
              <input
                className="search"
                type="search"
                aria-label="Search facilities"
                placeholder="Search facilities"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>

            {shown.length === 0 && !loading && (
              <p className="empty">No live facility matches "{search}".</p>
            )}

            <div className="grid">
              {facilityCards.map((facility) => {
                const alreadyJoined = ticketsForUser.some(
                  (ticket) => ticket.facility_id === facility.id
                );

                return (
                  <article
                    className={`card ${facility.status}`}
                    key={facility.id}
                  >
                    <div className="card-top">
                      <span className="card-icon">{facility.icon}</span>
                      <span className={`pill ${facility.status}`}>
                        {facility.status === "available"
                          ? "Available"
                          : facility.status === "moderate"
                            ? "Moderate"
                            : "Busy"}
                      </span>
                    </div>

                    <h3>{facility.displayName}</h3>
                    <p className="loc">{facility.displayLocation}</p>

                    <div className="wait">
                      <b>{facility.wait}</b> min AI wait
                    </div>

                    <div className="meta">
                      <span>{facility.waiting} waiting</span>
                      <span>
                        Avg service <b>{facility.average_service_minutes} min</b>
                      </span>
                    </div>

                    <button
                      className={`btn ${alreadyJoined ? "ghost" : "dark"} full`}
                      disabled={alreadyJoined || loading}
                      onClick={() => join(facility)}
                    >
                      {alreadyJoined
                        ? "You're in this queue"
                        : user
                          ? "Join queue"
                          : "Log in to join"}
                    </button>
                  </article>
                );
              })}
            </div>
          </section>

          <section className="how">
            <h2>How it works</h2>
            <ol>
              <li><b>Check live queues.</b> Counts come directly from the backend database.</li>
              <li><b>Join from anywhere.</b> Your queue entry is stored server-side.</li>
              <li><b>Get an AI estimate.</b> The trained model predicts your waiting time.</li>
            </ol>
          </section>
        </>
      )}

      {view === "staff" && (
        <section className="panel">
          <h2>Staff counter</h2>
          <p className="sub">Advance the real queue for the selected facility.</p>

          <label className="field">
            Facility
            <select value={staffId || ""} onChange={(e) => setStaffId(Number(e.target.value))}>
              {facilities.map((facility) => (
                <option key={facility.id} value={facility.id}>
                  {facility.displayName}
                </option>
              ))}
            </select>
          </label>

          {staffFacility && (
            <>
              <div className="counter">
                <button className="round" onClick={advance} aria-label="Advance queue">→</button>
                <div>
                  <b>{queues[staffFacility.id]?.waiting_count ?? 0}</b>
                  <span>people waiting</span>
                </div>
                <button className="round" onClick={advance} aria-label="Serve next person">✓</button>
              </div>

              <div className="svc">
                Average service time:{" "}
                <b>{staffFacility.average_service_minutes} min</b>
              </div>
              <p className="sub">
                Current AI wait:{" "}
                <b>{Math.round(queues[staffFacility.id]?.entries?.[0]?.estimated_wait_minutes ?? 0)} min</b>
              </p>
            </>
          )}
        </section>
      )}

      {view === "admin" && (
        <section className="panel wide">
          <h2>Live analytics</h2>
          <p className="sub">
            Historical model performance and live queue data from the backend.
          </p>

          {analytics ? (
            <>
              <div className="hero-stats">
                <b>{analytics.historical_records}</b> historical records
                <i />
                <b>{analytics.model?.r2 ?? "—"}</b> R²
                <i />
                <b>{analytics.model?.mae ?? "—"}</b> min MAE
              </div>

              <table>
                <thead>
                  <tr>
                    <th>Facility</th>
                    <th>Waiting now</th>
                    <th>AI wait</th>
                    <th>Historical avg</th>
                  </tr>
                </thead>
                <tbody>
                  {analytics.facilities?.map((item) => {
                    const live = facilities.find((f) => f.name === item.facility);
                    const q = live ? queues[live.id] : null;
                    const wait = q?.entries?.[0]?.estimated_wait_minutes ?? 0;

                    return (
                      <tr key={item.facility}>
                        <td>{FACILITY_META[item.facility]?.label || item.facility}</td>
                        <td>{q?.waiting_count ?? 0}</td>
                        <td><span className="pill moderate">{Math.round(wait)} min</span></td>
                        <td>{item.average_wait_minutes} min</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </>
          ) : (
            <p>Loading analytics…</p>
          )}
        </section>
      )}

      <footer>QueueLess · Live campus queue management · © 2026</footer>
    </div>
  );
}

function Login({ onBack, onLogin, onSwitch }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("student");
  const [error, setError] = useState("");

  const submit = (event) => {
    event.preventDefault();

    if (!email || !password) {
      setError("Enter your email and password.");
      return;
    }

    if (!/^\S+@\S+\.\S+$/.test(email)) {
      setError("Enter a valid email address.");
      return;
    }

    if (password.length < 6) {
      setError("Password needs at least 6 characters.");
      return;
    }

    // QueueLess currently has no authentication endpoint. Keep the UI session-only
    // until a real auth service is added; queue operations themselves are server-backed.
    onLogin({ email, role });
  };

  return (
    <div className="login">
      <aside className="login-side">
        <div className="logo"><span className="logo-icon">Q</span>QueueLess</div>
        <h1>Spend your break on your break.</h1>
      </aside>

      <main className="login-main">
        <form className="login-card" onSubmit={submit} noValidate>
          <button type="button" className="back" onClick={onBack}>← Back</button>
          <h2>Log in</h2>

          <label className="field">
            Email
            <input
              type="email"
              placeholder="you@college.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </label>

          <label className="field">
            Password
            <input
              type="password"
              placeholder="At least 6 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>

          <label className="field">
            Log in as
            <select value={role} onChange={(e) => setRole(e.target.value)}>
              <option value="student">Student</option>
              <option value="staff">Facility staff</option>
              <option value="admin">Admin</option>
            </select>
          </label>

          {error && <div className="error" role="alert">{error}</div>}
          <button className="btn dark full big" type="submit">Log in</button>
          <p className="switch">
            New to QueueLess?{" "}
            <button type="button" onClick={onSwitch}>Create an account</button>
          </p>
        </form>
      </main>
    </div>
  );
}

function Signup({ onBack, onSignup, onSwitch }) {
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirm: "",
    role: "student",
  });
  const [error, setError] = useState("");

  const set = (key) => (event) =>
    setForm((current) => ({ ...current, [key]: event.target.value }));

  const submit = (event) => {
    event.preventDefault();

    if (!form.name.trim()) return setError("Enter your full name.");
    if (!/^\S+@\S+\.\S+$/.test(form.email)) return setError("Enter a valid email address.");
    if (form.password.length < 6) return setError("Password needs at least 6 characters.");
    if (form.password !== form.confirm) return setError("Passwords don't match.");

    onSignup({
      email: form.email,
      role: form.role,
      name: form.name.trim(),
    });
  };

  return (
    <div className="login">
      <aside className="login-side">
        <div className="logo"><span className="logo-icon">Q</span>QueueLess</div>
        <h1>Join the line without standing in it.</h1>
      </aside>

      <main className="login-main">
        <form className="login-card" onSubmit={submit} noValidate>
          <button type="button" className="back" onClick={onBack}>← Back</button>
          <h2>Create your account</h2>

          <label className="field">
            Full name
            <input placeholder="Your name" value={form.name} onChange={set("name")} />
          </label>

          <label className="field">
            College email
            <input type="email" placeholder="you@college.edu" value={form.email} onChange={set("email")} />
          </label>

          <label className="field">
            Password
            <input type="password" placeholder="At least 6 characters" value={form.password} onChange={set("password")} />
          </label>

          <label className="field">
            Confirm password
            <input type="password" placeholder="Re-enter password" value={form.confirm} onChange={set("confirm")} />
          </label>

          <label className="field">
            I am a
            <select value={form.role} onChange={set("role")}>
              <option value="student">Student</option>
              <option value="staff">Facility staff</option>
              <option value="admin">Admin</option>
            </select>
          </label>

          {error && <div className="error" role="alert">{error}</div>}
          <button className="btn dark full big" type="submit">Create account</button>
          <p className="switch">
            Already registered?{" "}
            <button type="button" onClick={onSwitch}>Log in</button>
          </p>
        </form>
      </main>
    </div>
  );
}
