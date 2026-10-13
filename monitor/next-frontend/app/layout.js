import SiteNav from "../components/SiteNav";
import "./globals.css";
export const metadata = { title: "모아 | 감시 대시보드" };
export default function Layout({ children }) {
  return <html lang="ko"><body><main><SiteNav />{children}<footer className="footnote">작은 기록을 모아, 더 안전한 공간을 만들어요.</footer></main></body></html>;
}
