import assert from "node:assert/strict";
import test from "node:test";
import { GET, POST } from "../monitor/next-frontend/app/api/[...path]/route.js";
const context = (path) => ({ params: Promise.resolve({ path }) });

test("proxy rejects event ingestion and unsupported paths", async () => {
  assert.equal((await POST(new Request("http://web/api/events", { method:"POST" }), context(["events"]))).status,404);
  assert.equal((await GET(new Request("http://web/api/admin"), context(["admin"]))).status,404);
});
test("proxy reports missing configuration and network failure", async () => {
  delete process.env.MONITOR_API_URL;
  assert.equal((await GET(new Request("http://web/api/notes"),context(["notes"]))).status,503);
  process.env.MONITOR_API_URL = "http://api";
  const original = globalThis.fetch;
  globalThis.fetch = async () => { throw new Error("unavailable"); };
  try {
    const response = await GET(new Request("http://web/api/notes"),context(["notes"]));
    assert.equal(response.status,502);
    assert.match((await response.json()).error,/감시 API/);
  } finally { globalThis.fetch = original; }
});
test("proxy forwards cookies, csrf, body, query, status and multiple Set-Cookie headers", async () => {
  process.env.MONITOR_API_URL = "https://api.example";
  const original = globalThis.fetch;
  globalThis.fetch = async (url, options) => {
    assert.equal(url.href,"https://api.example/api/auth/login?check=1");
    assert.equal(options.headers.get("cookie"),"session=old");
    assert.equal(options.headers.get("x-csrf-token"),"csrf");
    assert.equal(new TextDecoder().decode(options.body),'{"username":"test"}');
    const headers = new Headers({ "Content-Type":"application/json" });
    headers.append("Set-Cookie","session=new; HttpOnly; Path=/");
    headers.append("Set-Cookie","extra=value; Path=/");
    return new Response('{"ok":true}',{status:201,headers});
  };
  try {
    const request = new Request("https://web/api/auth/login?check=1",{method:"POST",
      headers:{"cookie":"session=old","x-csrf-token":"csrf","content-type":"application/json"},
      body:'{"username":"test"}'});
    const response = await POST(request,context(["auth","login"]));
    assert.equal(response.status,201);
    assert.equal(response.headers.getSetCookie().length,2);
    assert.equal(response.headers.get("cache-control"),"no-store");
    assert.deepEqual(await response.json(),{ok:true});
  } finally { globalThis.fetch = original; }
});
