"use client";
import { useEffect, useState } from "react";
import { getSession, login, logout } from "../api/notes";

export default function Events() {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [credentials, setCredentials] = useState({ username: "", password: "" });
  const [events, setEvents] = useState([]);
  const [filter, setFilter] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    getSession().then(data => { if (active) setUser(data.user); })
      .catch(err => { if (active) setError(err.message); })
      .finally(() => { if (active) setReady(true); });
    return () => { active = false; };
  }, []);
  async function retrySession() {
    setBusy(true); setError("");
    try { const data = await getSession(); setUser(data.user); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }
  async function loadEvents() {
    setBusy(true); setError("");
    try {
      const response = await fetch(`/api/events${filter ? `?event_type=${filter}` : ""}`, { cache: "no-store" });
      const data = await response.json();
      if (!response.ok) { if (response.status === 401) setUser(null); throw new Error(data.error); }
      setEvents(data.events);
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }
  async function signIn(event) {
    event.preventDefault(); setBusy(true); setError("");
    try { await getSession(); const data = await login(credentials.username, credentials.password); setUser(data.user); setCredentials({ username: "", password: "" }); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }
  async function signOut() {
    setBusy(true); setError("");
    try { await logout(); setUser(null); setEvents([]); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }
  return <section><p className="eyebrow">MONITOR / REQUEST LOG</p><h1>로그인 기록</h1><p>일반 게시판의 로그인 성공과 실패를 확인합니다.</p>
    {error && <p role="alert">{error}</p>}
    {ready && !user && <button type="button" onClick={retrySession} disabled={busy}>연결 다시 확인</button>}
    {!ready ? <p>로그인 상태 확인 중…</p> : !user ? <form onSubmit={signIn}>
      <h2>운영자 로그인</h2><label htmlFor="username">아이디</label><input id="username" autoComplete="username" required value={credentials.username} onChange={e => setCredentials({ ...credentials, username: e.target.value })} />
      <label htmlFor="password">비밀번호</label><input id="password" type="password" autoComplete="current-password" required value={credentials.password} onChange={e => setCredentials({ ...credentials, password: e.target.value })} />
      <button disabled={busy}>로그인</button></form> : <><div className="toolbar"><span>{user.name}님</span><button onClick={signOut} disabled={busy}>로그아웃</button></div>
      <div className="toolbar"><label htmlFor="filter">기록 종류</label><select id="filter" value={filter} onChange={e => setFilter(e.target.value)}><option value="">전체</option><option value="login_failure">로그인 실패</option><option value="login_success">로그인 성공</option></select><button onClick={loadEvents} disabled={busy}>기록 불러오기</button></div>
      <div className="table-wrap"><table><thead><tr><th>시각</th><th>종류</th><th>요청</th><th>경로</th><th>상태</th></tr></thead><tbody>{events.map(item => <tr key={item.id}><td>{new Date(item.occurred_at).toLocaleString("ko-KR")}</td><td>{item.event_type}</td><td>{item.method}</td><td>{item.path}</td><td>{item.status_code}</td></tr>)}</tbody></table></div>{!events.length && <p>기록을 불러오거나 일반 서비스에서 로그인해 주세요.</p>}</>}
  </section>;
}
