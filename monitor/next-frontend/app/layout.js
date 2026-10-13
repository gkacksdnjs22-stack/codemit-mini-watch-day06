import Link from "next/link";
import "./globals.css";
export const metadata = { title: "모아 | 감시 대시보드" };
export default function Layout({ children }) {
  return <html lang="ko"><body><main><header className="site-nav"><Link className="site-brand" href="/">✿ 모아</Link><nav className="site-links" aria-label="감시 메뉴"><Link href="/">로그인 기록</Link><Link href="/notes">관찰 메모</Link><a href="http://localhost:8081/">일반 게시판</a></nav></header>{children}<footer className="footnote">작은 기록을 모아, 더 안전한 공간을 만들어요.</footer></main></body></html>;
}
