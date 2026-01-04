import { Navigate, Route, Routes } from "react-router-dom";
import AbandonedCarts from "./pages/AbandonedCarts";
import AiAdvisor from "./pages/AiAdvisor";
import Analytics from "./pages/Analytics";
import Campaigns from "./pages/Campaigns";
import Dashboard from "./pages/Dashboard";
import Home from "./pages/Home";
import Playbooks from "./pages/Playbooks";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/dashboard/campaigns" element={<Campaigns />} />
      <Route path="/dashboard/abandoned-carts" element={<AbandonedCarts />} />
      <Route path="/dashboard/analytics" element={<Analytics />} />
      <Route path="/dashboard/ai-advisor" element={<AiAdvisor />} />
      <Route path="/dashboard/playbooks" element={<Playbooks />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
