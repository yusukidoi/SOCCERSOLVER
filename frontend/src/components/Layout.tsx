import type { ReactNode } from "react";
import { Link } from "react-router-dom";

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="app">
      <header className="app__header">
        <Link to="/" className="app__brand">
          <span className="app__brand-mark">⚽</span> SoccerSolver
        </Link>
        <span className="app__tagline">Player intelligence for sporting directors</span>
      </header>
      <main className="app__main">{children}</main>
    </div>
  );
}
