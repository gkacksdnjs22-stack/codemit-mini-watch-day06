import Link from "next/link";
import "./globals.css";
export const metadata = { title: "Mini Watch | 감시 대시보드" };
export default function Layout({ children }) {
  return <html lang="ko"><body><header><Link href="/">Mini Watch</Link><nav><Link href="/">로그인 기록</Link><Link href="/notes">감시 메모</Link><a href="http://localhost:8081/">일반 게시판</a></nav></header><main>{children}</main><footer>일반 서비스의 요청을 확인하고 관찰 내용을 남겨 보세요.</footer></body></html>;
}
