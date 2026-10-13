"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
export default function SiteNav() {
  const path = usePathname();
  return <header className="site-nav"><Link className="site-brand" href="/">✿ 모아<span className="brand-context">감시 공간</span></Link><nav className="site-links" aria-label="감시 메뉴"><Link aria-current={path === "/" ? "page" : undefined} href="/">로그인 기록</Link><Link aria-current={path === "/notes" ? "page" : undefined} href="/notes">관찰 메모</Link><a href="http://localhost:8081/">일반 게시판 ↗</a></nav></header>;
}
