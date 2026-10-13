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
  const [loaded, setLoaded] = useState(false);
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
      setEvents(data.events); setLoaded(true);
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
  const labels = { login_success: "로그인 성공", login_failure: "로그인 실패", http_request: "일반 요청" };
  return <section>
    <div className="page-heading"><div><p className="eyebrow">공간 살펴보기</p><h1>로그인 기록</h1><p className="intro">누가 접속했고 어떤 요청이 있었는지 확인해 보세요.</p></div></div>
    {error && <p role="alert">{error}</p>}
    {!ready ? <p role="status">로그인 상태 확인 중…</p> : !user ? <form className="login-panel" onSubmit={signIn}>
      <h2>운영자 로그인</h2><p className="intro">기록과 메모를 확인하려면 로그인해 주세요.</p>
      <label htmlFor="username">아이디</label><input id="username" autoComplete="username" required value={credentials.username} onChange={e => setCredentials({ ...credentials, username: e.target.value })} />
      <label htmlFor="password">비밀번호</label><input id="password" type="password" autoComplete="current-password" required value={credentials.password} onChange={e => setCredentials({ ...credentials, password: e.target.value })} />
      <button disabled={busy}>{busy ? "확인 중…" : "로그인"}</button>
      {error && <button className="connection-retry" type="button" onClick={retrySession} disabled={busy}>연결 다시 확인</button>}
    </form> : <>
      <div className="account-bar"><span><strong>{user.name}</strong>님 · 운영자</span><button className="button secondary compact" onClick={signOut} disabled={busy}>로그아웃</button></div>
      <div className="record-toolbar"><div className="filter-field"><label htmlFor="filter">기록 종류</label><select id="filter" value={filter} onChange={e => setFilter(e.target.value)}><option value="">전체 기록</option><option value="login_failure">로그인 실패</option><option value="login_success">로그인 성공</option></select></div><button onClick={loadEvents} disabled={busy}>{busy ? "불러오는 중…" : "기록 불러오기"}</button></div>
      {loaded && <p className="result-count" role="status">불러온 기록 <strong>{events.length}</strong>건 · 아래 목록에 표시됩니다.</p>}
      <div className="table-wrap"><table><caption className="sr-only">일반 게시판 요청 기록</caption><thead><tr><th scope="col">시각</th><th scope="col">종류</th><th scope="col">요청</th><th scope="col">경로</th><th scope="col">응답 코드</th></tr></thead><tbody>{events.map(item => <tr key={item.id}><td>{new Date(item.occurred_at).toLocaleString("ko-KR")}</td><td><span className={`event-badge ${item.event_type}`}>{labels[item.event_type] || item.event_type}</span></td><td><code>{item.method}</code></td><td><code>{item.path}</code></td><td><span className={item.status_code >= 400 ? "response-code response-error" : "response-code"}>{item.status_code}</span></td></tr>)}{!events.length && <tr><td colSpan={5} className="table-empty">{loaded ? "선택한 종류의 기록이 아직 없어요." : "기록 불러오기를 눌러 접속 내역을 확인해 주세요."}</td></tr>}</tbody></table></div>
      <p className="section-help">성공은 정상 로그인, 실패는 잘못된 계정 정보로 시도한 로그인입니다.</p>
    </>}
  </section>;
}
