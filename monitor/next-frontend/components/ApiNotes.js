"use client";

import { useEffect, useRef, useState } from "react";
import * as api from "../api/notes";

const emptyForm = { title: "", body: "", status: "pending" };
const statuses = { pending: "확인 전", in_progress: "확인 중", completed: "완료" };

export default function ApiNotes() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [credentials, setCredentials] = useState({ username: "", password: "" });
  const [notes, setNotes] = useState([]);
  const [selected, setSelected] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [lookupId, setLookupId] = useState("");
  const [deleting, setDeleting] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const dialogRef = useRef(null);

  function report(error) {
    setError(`${error.message}${error.status ? ` (${error.status})` : ""}`);
    if (error.status === 401) setUser(null);
  }

  useEffect(() => {
    let active = true;
    async function initialize() {
      try {
        const session = await api.getSession();
        if (!active) return;
        setUser(session.user);
        if (session.user) {
          const data = await api.listNotes();
          if (active) setNotes(data.notes);
        }
      } catch (error) {
        if (active) setError(`${error.message}${error.status ? ` (${error.status})` : ""}`);
      } finally {
        if (active) setLoading(false);
      }
    }
    initialize();
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (deleting) dialogRef.current?.showModal();
  }, [deleting]);

  function resetForm() {
    setEditingId(null);
    setForm(emptyForm);
  }

  async function refreshNotes() {
    const data = await api.listNotes();
    setNotes(data.notes);
  }

  async function signIn(event) {
    event.preventDefault();
    setBusy(true); setError(""); setMessage("");
    try {
      await api.getSession();
      const data = await api.login(credentials.username, credentials.password);
      setUser(data.user);
      setCredentials({ username: "", password: "" });
      await refreshNotes();
    } catch (error) { report(error); }
    finally { setBusy(false); }
  }

  async function signOut() {
    setBusy(true); setError(""); setMessage("");
    try {
      await api.logout();
      setUser(null); setSelected(null); setNotes([]); resetForm();
    } catch (error) { report(error); }
    finally { setBusy(false); }
  }

  async function selectNote(id) {
    setBusy(true); setError(""); setMessage("");
    try {
      const data = await api.getNote(id);
      setSelected(data.note);
      resetForm();
    } catch (error) { report(error); }
    finally { setBusy(false); }
  }

  async function refresh() {
    setBusy(true); setError(""); setMessage("");
    try {
      await refreshNotes();
      if (selected) {
        try {
          const data = await api.getNote(selected.id);
          setSelected(data.note);
        } catch (error) {
          if (error.status === 404) { setSelected(null); resetForm(); }
          throw error;
        }
      }
      setMessage("최신 메모를 다시 불러왔어요.");
    } catch (error) { report(error); }
    finally { setBusy(false); }
  }

  async function save(event) {
    event.preventDefault();
    setBusy(true); setError(""); setMessage("");
    try {
      // 서버의 trim/400 검증을 그대로 받아 오류를 표시하며 원본 state는 성공 뒤 갱신합니다.
      const data = editingId !== null ? await api.updateNote(editingId, form) : await api.createNote(form);
      setSelected(data.note); resetForm();
      setMessage("메모를 DB에 저장했어요.");
      await refreshNotes();
    } catch (error) { report(error); }
    finally { setBusy(false); }
  }

  function startEdit() {
    setEditingId(selected.id);
    setForm({ title: selected.title, body: selected.body, status: selected.status });
    setError(""); setMessage("");
  }

  function closeDelete() {
    dialogRef.current?.close();
    setDeleting(null);
  }

  async function confirmDelete() {
    setBusy(true); setError(""); setMessage("");
    try {
      await api.deleteNote(deleting.id);
      if (editingId === deleting.id) resetForm();
      if (selected?.id === deleting.id) setSelected(null);
      closeDelete();
      setMessage("메모를 DB에서 삭제했어요.");
      await refreshNotes();
    } catch (error) { closeDelete(); report(error); }
    finally { setBusy(false); }
  }

  if (loading) return <p role="status">로그인 상태를 확인하고 있어요…</p>;

  return (
    <div className="api-notes">
      {error && <p className="error api-error" role="alert">{error}</p>}
      <p className="status-message" role="status">{message}</p>
      {!user ? (
        <section className="panel api-login" aria-labelledby="api-login-title">
          <p className="eyebrow">OPERATOR LOGIN</p><h2 id="api-login-title">DB 메모 로그인</h2>
          <p>기존 감시 서비스의 운영자 계정으로 로그인해 주세요.</p>
          <form onSubmit={signIn} noValidate>
            <label htmlFor="api-username">아이디</label><input id="api-username" autoComplete="username" value={credentials.username} onChange={(e) => setCredentials({ ...credentials, username: e.target.value })} />
            <label htmlFor="api-password">비밀번호</label><input id="api-password" type="password" autoComplete="current-password" value={credentials.password} onChange={(e) => setCredentials({ ...credentials, password: e.target.value })} />
            <button className="button primary" type="submit" disabled={busy}>로그인</button>
          </form>
        </section>
      ) : (
        <>
          <div className="api-toolbar"><p><strong>{user.name}</strong> 님의 DB 메모</p><div className="button-row"><button className="button secondary" disabled={busy} onClick={refresh}>DB 목록 새로고침</button><button className="button secondary" disabled={busy} onClick={signOut}>로그아웃</button></div></div>
          <div className="notes-workspace">
            <section className="panel editor" aria-labelledby="api-editor-title">
              <span className="card-index">{editingId !== null ? `EDIT #${editingId}` : "NEW DB NOTE"}</span><h2 id="api-editor-title">{editingId !== null ? "DB 메모 수정" : "새 DB 메모"}</h2>
              <form onSubmit={save} noValidate>
                <fieldset disabled={busy}>
                  <label htmlFor="api-title">제목</label><input id="api-title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
                  <label htmlFor="api-body">내용</label><textarea id="api-body" value={form.body} rows={6} onChange={(e) => setForm({ ...form, body: e.target.value })} />
                  <label htmlFor="api-status">처리 상태</label><select id="api-status" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>{Object.entries(statuses).map(([value, text]) => <option value={value} key={value}>{text}</option>)}</select>
                  <div className="button-row"><button className="button primary" type="submit">{editingId !== null ? "DB 수정 저장" : "DB 메모 등록"}</button>{editingId !== null && <button className="button secondary" type="button" onClick={() => { resetForm(); setError(""); setMessage("수정을 취소했어요. DB의 원본은 유지됩니다."); }}>DB 수정 취소</button>}</div>
                </fieldset>
              </form><p className="session-hint">이 화면의 메모는 PostgreSQL에 저장됩니다.<br />새로고침하고 다시 조회해도 남아 있어요.</p>
            </section>
            <section className="notes-collection" aria-labelledby="api-collection-title">
              <div className="collection-header"><h2 id="api-collection-title">저장된 DB 메모 <span className="count-badge">{notes.length}</span></h2></div>
              <form className="lookup-form" onSubmit={(e) => { e.preventDefault(); if (/^[1-9]\d*$/.test(lookupId)) selectNote(lookupId); else setError("메모 번호는 양의 정수로 입력해 주세요."); }}>
                <label htmlFor="lookup-id">메모 번호</label><input id="lookup-id" inputMode="numeric" value={lookupId} onChange={(e) => setLookupId(e.target.value)} /><button className="button secondary" disabled={busy}>번호로 조회</button>
              </form>
              {notes.length === 0 ? <div className="empty-state"><h3>저장된 DB 메모가 없어요.</h3><p>첫 기록을 작성해 보세요.</p></div> : <ul className="notes-list api-note-list">{notes.map((note) => <li className="note-card" key={note.id} data-db-note-id={note.id}><button className="note-title-button" disabled={busy} onClick={() => selectNote(note.id)}>{note.title}</button><div className="note-meta"><span>#{note.id} · {statuses[note.status]}</span></div></li>)}</ul>}
              {selected && <article className="panel api-detail" aria-labelledby="detail-title" data-selected-note-id={selected.id}>
                <span className="card-index">DB NOTE #{selected.id} · {statuses[selected.status]}</span><h2 id="detail-title">{selected.title}</h2><p className="note-content">{selected.body}</p>
                <div className="button-row"><button className="button secondary" disabled={busy} onClick={startEdit}>선택한 DB 메모 수정</button><button className="button secondary" disabled={busy} onClick={() => { setDeleting(selected); setMessage(""); setError(""); }}>선택한 DB 메모 삭제</button></div>
              </article>}
            </section>
          </div>
        </>
      )}
      {deleting && <dialog ref={dialogRef} className="delete-dialog" aria-labelledby="api-delete-title" onCancel={(e) => { e.preventDefault(); if (!busy) closeDelete(); }}>
        <p className="eyebrow">DELETE DB NOTE #{deleting.id}</p><h2 id="api-delete-title">DB에서 이 메모를 삭제할까요?</h2><blockquote>{deleting.title}</blockquote>
        <div className="button-row"><button className="button secondary" disabled={busy} autoFocus onClick={closeDelete}>DB 삭제 취소</button><button className="button danger" disabled={busy} onClick={confirmDelete}>DB 삭제 확정</button></div>
      </dialog>}
    </div>
  );
}
