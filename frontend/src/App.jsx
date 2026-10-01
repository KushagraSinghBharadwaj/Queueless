import { useState, useEffect, useRef } from "react";
import "./App.css";

/* ---- Demo data: replace with your backend / AI API later ---- */
const HOURLY = { 8: 10, 9: 25, 10: 35, 11: 50, 12: 90, 13: 80, 14: 45, 15: 40, 16: 55, 17: 30 };
const NOW_H = (() => { const h = new Date().getHours(); return h >= 8 && h <= 17 ? h : 12; })();
const rush = (h) => 0.8 + (HOURLY[Math.min(17, Math.max(8, h))] / 100) * 0.7;

const START = [
  { id: 1, name: "Main Canteen", icon: "🍽️", location: "Block A", queue: 18, svc: 1.2 },
  { id: 2, name: "Printing Shop", icon: "🖨️", location: "Block B", queue: 6, svc: 0.9 },
  { id: 3, name: "Central Library", icon: "📚", location: "Block C", queue: 9, svc: 0.9 },
  { id: 4, name: "Computer Lab", icon: "💻", location: "Block D", queue: 14, svc: 1.1 },
  { id: 5, name: "Admin Office", icon: "🏢", location: "Main Building", queue: 4, svc: 0.8 },
  { id: 6, name: "College Bus", icon: "🚌", location: "Main Gate", queue: 22, svc: 0.8 },
];
const NAMES = Object.fromEntries(START.map((f) => [f.id, f.name]));

/* Simple "AI": queue x service time x time-of-day rush factor */
const predict = (f) => {
  const wait = Math.round(f.queue * f.svc * rush(NOW_H));
  const soon = Math.round(f.queue * f.svc * ((rush(NOW_H) + rush(NOW_H + 1)) / 2) * 1.1);
  return { wait, soon, level: soon < 8 ? "Low" : soon < 18 ? "Medium" : "High", status: wait < 8 ? "available" : wait < 15 ? "moderate" : "busy" };
};
const LABEL = { available: "Available", moderate: "Moderate", busy: "Busy" };

export default function App() {
  const [page, setPage] = useState("home");
  const [user, setUser] = useState(null); // { email, role }
  const [view, setView] = useState("student");
  const [facilities, setFacilities] = useState(START);
  const [tickets, setTickets] = useState([]); // { id, pos }
  const [toasts, setToasts] = useState([]);
  const [search, setSearch] = useState("");
  const [staffId, setStaffId] = useState(1);
  const ref = useRef([]);
  ref.current = tickets;

  const notify = (text) => {
    const id = Math.random();
    setToasts((t) => [...t, { id, text }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 5000);
  };

  // Live simulation: crowds drift, your place in line moves forward
  useEffect(() => {
    const t = setInterval(() => {
      setFacilities((fs) => fs.map((f) => ({ ...f, queue: Math.max(0, f.queue + [-2, -1, 0, 0, 1, 2][Math.floor(Math.random() * 6)]) })));
      const next = ref.current.flatMap((k) => {
        if (Math.random() > 0.55) return [k];
        if (k.pos <= 1) { notify(`It's your turn at ${NAMES[k.id]}. Head over now.`); return []; }
        if (k.pos === 2) notify(`You're next at ${NAMES[k.id]}.`);
        return [{ ...k, pos: k.pos - 1 }];
      });
      setTickets(next);
    }, 3500);
    return () => clearInterval(t);
  }, []);

  const bump = (id, d) => setFacilities((fs) => fs.map((f) => (f.id === id ? { ...f, queue: Math.max(0, f.queue + d) } : f)));
  const join = (f) => {
    if (!user) return setPage("login");
    if (tickets.some((k) => k.id === f.id)) return;
    setTickets([...tickets, { id: f.id, pos: f.queue + 1 }]);
    bump(f.id, 1);
    notify(`You joined the ${f.name} queue at position ${f.queue + 1}.`);
  };
  const leave = (id) => { setTickets(tickets.filter((k) => k.id !== id)); bump(id, -1); };

  const done = (u) => { setUser(u); setView("student"); setPage("home"); };
  if (page === "login") return <Login onBack={() => setPage("home")} onLogin={done} onSwitch={() => setPage("signup")} />;
  if (page === "signup") return <Signup onBack={() => setPage("home")} onSignup={done} onSwitch={() => setPage("login")} />;

  const shown = facilities.filter((f) => f.name.toLowerCase().includes(search.toLowerCase()));
  const board = [...facilities].sort((a, b) => predict(b).wait - predict(a).wait).slice(0, 4);
  const total = facilities.reduce((s, f) => s + f.queue, 0);
  const tabs = ["student", ...(user && user.role !== "student" ? ["staff"] : []), ...(user?.role === "admin" ? ["admin"] : [])];
  const staffF = facilities.find((f) => f.id === staffId);

  return (
    <div className="app">
      <nav className="navbar">
        <div className="logo"><span className="logo-icon">Q</span>QueueLess</div>
        {tabs.length > 1 && (
          <div className="tabs" role="tablist">
            {tabs.map((t) => <button key={t} role="tab" aria-selected={view === t} className={view === t ? "on" : ""} onClick={() => setView(t)}>{t[0].toUpperCase() + t.slice(1)}</button>)}
          </div>
        )}
        {user ? (
          <div className="user"><span>{user.email}</span><button className="btn ghost" onClick={() => { setUser(null); setView("student"); setTickets([]); }}>Log out</button></div>
        ) : (
          <div className="user">
            <button className="btn ghost" onClick={() => setPage("login")}>Log in</button>
            <button className="btn dark" onClick={() => setPage("signup")}>Sign up</button>
          </div>
        )}
      </nav>

      <div className="toasts" aria-live="polite">{toasts.map((t) => <div key={t.id} className="toast">{t.text}</div>)}</div>

      {view === "student" && (
        <>
          <header className="hero">
            <div className="hero-text">
              <h1>Know the wait before you walk.</h1>
              <p>See how busy every campus facility is, get a predicted wait, and join the line from your phone. We'll tell you when you're next.</p>
              <a className="btn dark big" href="#facilities">See all facilities</a>
              <div className="hero-stats"><b>{total}</b> people in queues right now <i /> <b>{Math.round(total ? facilities.reduce((s, f) => s + predict(f).wait, 0) / facilities.length : 0)} min</b> average wait</div>
            </div>
            <div className="board" aria-label="Longest waits right now">
              <div className="board-head"><span className="dot" />Longest waits right now</div>
              {board.map((f) => (
                <div className="board-row" key={f.id}>
                  <span>{f.icon} {f.name}</span>
                  <b className={predict(f).status}>{predict(f).wait}<small> min</small></b>
                </div>
              ))}
            </div>
          </header>

          {tickets.length > 0 && (
            <section className="mine">
              <h2>Your queues</h2>
              <div className="mine-list">
                {tickets.map((k) => {
                  const f = facilities.find((x) => x.id === k.id);
                  return (
                    <div className="ticket" key={k.id}>
                      <div className="ticket-no">#{k.pos}</div>
                      <div className="ticket-body">
                        <b>{f.name}</b>
                        <span>{k.pos === 1 ? "You're up next" : `${k.pos - 1} ahead of you · about ${Math.round((k.pos - 1) * f.svc * rush(NOW_H))} min`}</span>
                      </div>
                      <button className="btn ghost" onClick={() => leave(k.id)}>Leave</button>
                    </div>
                  );
                })}
              </div>
            </section>
          )}

          <section className="facilities" id="facilities">
            <div className="section-head">
              <div><h2>Campus facilities</h2><p>Predicted wait uses queue size, service speed and the time of day.</p></div>
              <input className="search" type="search" aria-label="Search facilities" placeholder="Search facilities" value={search} onChange={(e) => setSearch(e.target.value)} />
            </div>
            {shown.length === 0 && <p className="empty">No facility matches "{search}". Try "canteen" or "library".</p>}
            <div className="grid">
              {shown.map((f) => {
                const p = predict(f);
                const joined = tickets.some((k) => k.id === f.id);
                return (
                  <article className={`card ${p.status}`} key={f.id}>
                    <div className="card-top">
                      <span className="card-icon">{f.icon}</span>
                      <span className={`pill ${p.status}`}>{LABEL[p.status]}</span>
                    </div>
                    <h3>{f.name}</h3>
                    <p className="loc">{f.location}</p>
                    <div className="wait"><b>{p.wait}</b> min wait</div>
                    <div className="meta">
                      <span>{f.queue} waiting</span>
                      <span>In 30 min: <b className={p.level.toLowerCase()}>{p.level}</b></span>
                    </div>
                    <button className={`btn ${joined ? "ghost" : "dark"} full`} disabled={joined} onClick={() => join(f)}>{joined ? "You're in this queue" : user ? "Join queue" : "Log in to join"}</button>
                  </article>
                );
              })}
            </div>
          </section>

          <section className="how">
            <h2>How it works</h2>
            <ol>
              <li><b>Check the crowd.</b> Live queue sizes and predicted waits for each facility.</li>
              <li><b>Join from anywhere.</b> Hold your place in line without standing in it.</li>
              <li><b>Get a heads-up.</b> We alert you when you're next, so you arrive just in time.</li>
            </ol>
          </section>
        </>
      )}

      {view === "staff" && (
        <section className="panel">
          <h2>Staff counter</h2>
          <p className="sub">Keep the count accurate for people who haven't joined online.</p>
          <label className="field">Facility
            <select value={staffId} onChange={(e) => setStaffId(+e.target.value)}>{facilities.map((f) => <option key={f.id} value={f.id}>{f.name}</option>)}</select>
          </label>
          <div className="counter">
            <button className="round" aria-label="Mark one person served" onClick={() => bump(staffId, -1)}>−</button>
            <div><b>{staffF.queue}</b><span>people waiting</span></div>
            <button className="round" aria-label="Add one walk-in" onClick={() => bump(staffId, 1)}>+</button>
          </div>
          <div className="svc">Average service time: <b>{staffF.svc.toFixed(1)} min</b>
            <button className="btn ghost" onClick={() => setFacilities(facilities.map((f) => f.id === staffId ? { ...f, svc: Math.max(0.3, +(f.svc - 0.1).toFixed(1)) } : f))}>Faster</button>
            <button className="btn ghost" onClick={() => setFacilities(facilities.map((f) => f.id === staffId ? { ...f, svc: +(f.svc + 0.1).toFixed(1) } : f))}>Slower</button>
          </div>
          <p className="sub">Students currently see a {predict(staffF).wait} min wait.</p>
        </section>
      )}

      {view === "admin" && (
        <section className="panel wide">
          <h2>Crowd analytics</h2>
          <p className="sub">Typical campus load by hour. The peak is highlighted; the current hour has a dot.</p>
          <div className="bars">
            {Object.entries(HOURLY).map(([h, v]) => (
              <div className="bar-col" key={h}>
                <div className={`bar ${v === Math.max(...Object.values(HOURLY)) ? "peak" : ""}`} style={{ height: `${v}%` }} title={`${v}% load`}><em>{v}</em></div>
                <span>{h > 12 ? h - 12 : h}{h >= 12 ? "p" : "a"}{+h === NOW_H ? " •" : ""}</span>
              </div>
            ))}
          </div>
          <table>
            <thead><tr><th>Facility</th><th>Waiting</th><th>Wait now</th><th>In 30 min</th></tr></thead>
            <tbody>{facilities.map((f) => { const p = predict(f); return <tr key={f.id}><td>{f.icon} {f.name}</td><td>{f.queue}</td><td><span className={`pill ${p.status}`}>{p.wait} min</span></td><td>{p.level}</td></tr>; })}</tbody>
          </table>
        </section>
      )}

      <footer>QueueLess · Campus queue management · © 2026</footer>
    </div>
  );
}

function Login({ onBack, onLogin, onSwitch }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("student");
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const submit = (e) => {
    e.preventDefault();
    if (!email || !password) return setError("Enter your email and password.");
    if (!/^\S+@\S+\.\S+$/.test(email)) return setError("Enter a valid email address, like you@college.edu.");
    if (password.length < 6) return setError("Password needs at least 6 characters.");
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
          <label className="field">Email<input type="email" placeholder="you@college.edu" value={email} onChange={(e) => setEmail(e.target.value)} /></label>
          <label className="field">Password
            <span className="pw"><input type={show ? "text" : "password"} placeholder="At least 6 characters" value={password} onChange={(e) => setPassword(e.target.value)} />
              <button type="button" onClick={() => setShow(!show)}>{show ? "Hide" : "Show"}</button></span>
          </label>
          <label className="field">Log in as
            <select value={role} onChange={(e) => setRole(e.target.value)}><option value="student">Student</option><option value="staff">Facility staff</option><option value="admin">Admin</option></select>
          </label>
          {error && <div className="error" role="alert">{error}</div>}
          <button className="btn dark full big" type="submit">Log in</button>
          <p className="note">Demo only: any valid email and a 6+ character password works.</p>
          <p className="switch">New to QueueLess? <button type="button" onClick={onSwitch}>Create an account</button></p>
        </form>
      </main>
    </div>
  );
}

function Signup({ onBack, onSignup, onSwitch }) {
  const [f, setF] = useState({ name: "", email: "", password: "", confirm: "", role: "student" });
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const submit = (e) => {
    e.preventDefault();
    if (!f.name.trim()) return setError("Enter your full name.");
    if (!/^\S+@\S+\.\S+$/.test(f.email)) return setError("Enter a valid email address, like you@college.edu.");
    if (f.password.length < 6) return setError("Password needs at least 6 characters.");
    if (f.password !== f.confirm) return setError("Passwords don't match. Check both fields.");
    onSignup({ email: f.email, role: f.role, name: f.name.trim() });
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
          <label className="field">Full name<input placeholder="Your name" value={f.name} onChange={set("name")} /></label>
          <label className="field">College email<input type="email" placeholder="you@college.edu" value={f.email} onChange={set("email")} /></label>
          <label className="field">Password
            <span className="pw"><input type={show ? "text" : "password"} placeholder="At least 6 characters" value={f.password} onChange={set("password")} />
              <button type="button" onClick={() => setShow(!show)}>{show ? "Hide" : "Show"}</button></span>
          </label>
          <label className="field">Confirm password<input type={show ? "text" : "password"} placeholder="Re-enter password" value={f.confirm} onChange={set("confirm")} /></label>
          <label className="field">I am a
            <select value={f.role} onChange={set("role")}><option value="student">Student</option><option value="staff">Facility staff</option><option value="admin">Admin</option></select>
          </label>
          {error && <div className="error" role="alert">{error}</div>}
          <button className="btn dark full big" type="submit">Create account</button>
          <p className="switch">Already registered? <button type="button" onClick={onSwitch}>Log in</button></p>
        </form>
      </main>
    </div>
  );
}