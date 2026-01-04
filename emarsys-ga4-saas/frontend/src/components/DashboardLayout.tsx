import { useState, type ReactNode } from "react";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";

type DashboardLayoutProps = {
  title: string;
  subtitle: string;
  label?: string;
  children: ReactNode;
};

function DashboardLayout({ title, subtitle, label, children }: DashboardLayoutProps) {
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  return (
    <div className={`dashboard-shell theme-${theme}`}>
      <Sidebar
        theme={theme}
        onToggleTheme={() =>
          setTheme((current) => (current === "dark" ? "light" : "dark"))
        }
      />
      <main className="dashboard-main">
        <TopBar title={title} subtitle={subtitle} label={label} />
        {children}
      </main>
    </div>
  );
}

export default DashboardLayout;
