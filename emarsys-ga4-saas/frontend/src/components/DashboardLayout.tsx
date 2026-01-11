import { useEffect, useState, type ReactNode } from "react";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";

type DashboardLayoutProps = {
  title: string;
  subtitle: string;
  label?: string;
  children: ReactNode;
};

const themeStorageKey = "keepais:dashboard-theme";

function DashboardLayout({ title, subtitle, label, children }: DashboardLayoutProps) {
  const [theme, setTheme] = useState<"dark" | "light">(() => {
    const stored = localStorage.getItem(themeStorageKey);
    return stored === "light" ? "light" : "dark";
  });
  const themeClass = theme === "light" ? "theme-light" : "";

  useEffect(() => {
    localStorage.setItem(themeStorageKey, theme);
  }, [theme]);

  return (
    <div
      className={`dashboard-shell ${themeClass} min-h-screen bg-[color:var(--bg)] text-[color:var(--ink)]`}
    >
      <div className="mx-auto flex min-h-screen w-full max-w-none flex-col lg:flex-row">
        <Sidebar
          theme={theme}
          onToggleTheme={() =>
            setTheme((current) => (current === "dark" ? "light" : "dark"))
          }
        />
        <main className="flex-1 px-6 pb-10 pt-6 lg:px-12">
          <TopBar title={title} subtitle={subtitle} label={label} />
          <div className="mt-6 space-y-6 lg:space-y-8">{children}</div>
        </main>
      </div>
    </div>
  );
}

export default DashboardLayout;
