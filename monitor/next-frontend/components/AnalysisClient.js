"use client";
import { useEffect, useState } from "react";
import { getSession, login, logout, startObservation, getAnalysis } from "../api/notes";

export default function AnalysisClient() {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [credentials, setCredentials] = useState({ username: "", password: "" });
  const [threshold, setThreshold] = useState("10");
  const [observation, setObservation] = useState(null);
  const [report, setReport] = useState(null);
  useEffect(() => {
    let active = true;
    getSession().then(data => { if (active) setUser(data.user); })
      .catch(err => { if (active) setError(err.message); })
      .finally(() => { if (active) setReady(true); });
    return () => { active = false; };
  }, []);
  async function run(action) {
    setBusy(true); setError("");
    try { await action(); }
    catch (err) {
      setError(err.message);
      if (err.status === 401) { setUser(null); setObservation(null); setReport(null); }
    }
    finally { setBusy(false); }
  }
  function signIn(event) {
    event.preventDefault();
    run(async () => { await getSession(); const data = await login(credentials.username, credentials.password); setUser(data.user); setCredentials({ username: "", password: "" }); });
  }
  function begin() {
    run(async () => { const data = await startObservation(); setObservation(data); setReport(null); });
  }
  function load(event) {
    event.preventDefault();
    run(async () => {
      const data = await getAnalysis(observation.after_id, threshold, observation.reference_time);
      setObservation({ after_id: data.after_id, reference_time: data.reference_time });
      setReport(data);
    });
  }
  const card = report?.cards[0];
  return <section>
    <div className="page-heading"><p className="eyebrow">실제 요청 살펴보기</p><h1>요청 분석</h1><p className="intro">조회 횟수와 그 숫자를 만든 기록을 함께 확인해요.</p></div>
    {error && <p role="alert">{error}</p>}
    {!ready ? <p role="status">로그인 상태 확인 중…</p> : !user ? <form className="login-panel" onSubmit={signIn}>
      <h2>운영자 로그인</h2><label htmlFor="username">아이디</label><input id="username" autoComplete="username" required value={credentials.username} onChange={e => setCredentials({ ...credentials, username: e.target.value })} />
      <label htmlFor="password">비밀번호</label><input id="password" autoComplete="current-password" type="password" required value={credentials.password} onChange={e => setCredentials({ ...credentials, password: e.target.value })} />
      <button type="submit" disabled={busy}>로그인</button>
    </form> : <>
      <div className="account-bar"><span><strong>{user.name}</strong>님 · 운영자</span><button disabled={busy} onClick={() => run(async () => { await logout(); setUser(null); setObservation(null); setReport(null); })}>로그아웃</button></div>
      <div className="panel observation-controls">
        <div><h2>1. 새 관찰 시작</h2><p className="section-help">현재 기록 이후의 요청을 살펴봐요. 시작한 뒤 일반 게시판에서 요청을 만들어 주세요.</p><button className="primary" disabled={busy} onClick={begin}>새 관찰 시작</button></div>
        <form onSubmit={load}><h2>2. 결과 불러오기</h2><label htmlFor="threshold">비교 기준 · 조회 횟수</label><input id="threshold" type="number" min="1" max="100000" step="1" required value={threshold} disabled={busy} onChange={e => setThreshold(e.target.value)} /><button className="primary" disabled={busy || !observation}>결과 불러오기</button></form>
      </div>
      <p className="section-help">첫 결과는 불러온 시각의 최근 60초 기록을 사용해요. 이후에는 같은 구간에서 기준만 비교해요. 새 요청을 살펴보려면 새 관찰을 시작해 주세요.</p>
      {observation && <p className="observation-meta">시작 ID: {observation.after_id} 이후 · 기준시각: {observation.reference_time || "첫 결과를 불러올 때 정해집니다"}</p>}
      {card && <article className="panel analysis-result" aria-label="HTTP 분석 결과">
        <div className="analysis-heading"><h2>{card.title}</h2><span className={`analysis-verdict ${card.matched ? "candidate" : "below"}`}>{card.verdict}</span></div>
        <div className="analysis-stats" role="status"><div><span>관찰값 · 목록 조회</span><strong>{card.observed}<small>회</small></strong></div><div><span>비교 기준</span><strong>{card.threshold}<small>회</small></strong></div><div><span>근거 기록</span><strong>{card.records.length}<small>행</small></strong></div></div>
        {String(card.threshold) !== threshold && <p className="status-message">기준을 바꿨어요. 결과 불러오기를 누르면 같은 기록으로 다시 비교합니다.</p>}
        <p>{card.reason}</p><p className="section-help">{report.limitations}</p>
        <details key={`${report.after_id}-${report.reference_time}`}><summary>근거 보기 · {card.records.length}행</summary><div className="table-wrap"><table><caption className="sr-only">관찰 구간의 실제 HTTP 근거</caption><thead><tr>{["ID", "수신시각", "방법", "경로", "상태", "종류", "역할"].map(label => <th key={label} scope="col">{label}</th>)}</tr></thead><tbody>
          {card.records.map(row => <tr key={row.id}><td>{row.id}</td><td>{row.occurred_at}</td><td>{row.method}</td><td>{row.path}</td><td>{row.status_code}</td><td>{row.kind}</td><td>{card.view_ids.includes(row.id) ? "조회 횟수" : "뒤따른 404 · 문맥"}</td></tr>)}
          {!card.records.length && <tr><td className="table-empty" colSpan="7">해당 근거 없음</td></tr>}
        </tbody></table></div></details>
      </article>}
    </>}
  </section>;
}
