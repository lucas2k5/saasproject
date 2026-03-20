import { Outlet } from "react-router-dom";
import DashboardLayout from "./DashboardLayout";
import { useRecApiAuth } from "../hooks/useRecApiAuth";

export default function RecommendationsLayout() {
  useRecApiAuth();

  return (
    <DashboardLayout
      title="Recomendação de Produtos"
      subtitle="Motor de IA para recomendações inteligentes"
      label="AI ENGINE"
    >
      <div className="rec-zone">
        <Outlet />
      </div>
    </DashboardLayout>
  );
}
