import { Navigate, Route, Routes } from "react-router-dom";
import AbandonedCarts from "./pages/AbandonedCarts";
import AiAdvisor from "./pages/AiAdvisor";
import Analytics from "./pages/Analytics";
import Campaigns from "./pages/Campaigns";
import Dashboard from "./pages/Dashboard";
import Home from "./pages/Home";
import Integrations from "./pages/Integrations";
import Playbooks from "./pages/Playbooks";
import Profile from "./pages/Profile";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import ProtectedRoute from "./components/ProtectedRoute";
import RecommendationsLayout from "./components/RecommendationsLayout";
import { Dashboard as RecDashboard } from "./pages/recommendations/Dashboard";
import { Catalog as RecCatalog } from "./pages/recommendations/Catalog";
import { Customers as RecCustomers } from "./pages/recommendations/Customers";
import { Orders as RecOrders } from "./pages/recommendations/Orders";
import { Offers as RecOffers } from "./pages/recommendations/Offers";
import { LifecycleDashboard as RecLifecycle } from "./pages/recommendations/LifecycleDashboard";
import { Cargas as RecCargas } from "./pages/recommendations/Cargas";
import { Config as RecConfig } from "./pages/recommendations/Config";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard/recommendations"
        element={
          <ProtectedRoute>
            <RecommendationsLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<RecDashboard />} />
        <Route path="catalog" element={<RecCatalog />} />
        <Route path="customers" element={<RecCustomers />} />
        <Route path="orders" element={<RecOrders />} />
        <Route path="offers" element={<RecOffers />} />
        <Route path="lifecycle" element={<RecLifecycle />} />
        <Route path="uploads" element={<RecCargas />} />
        <Route path="config" element={<RecConfig />} />
      </Route>
      <Route
        path="/dashboard/campaigns"
        element={
          <ProtectedRoute>
            <Campaigns />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard/abandoned-carts"
        element={
          <ProtectedRoute>
            <AbandonedCarts />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard/analytics"
        element={
          <ProtectedRoute>
            <Analytics />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard/ai-advisor"
        element={
          <ProtectedRoute>
            <AiAdvisor />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard/playbooks"
        element={
          <ProtectedRoute>
            <Playbooks />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard/integrations"
        element={
          <ProtectedRoute>
            <Integrations />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard/profile"
        element={
          <ProtectedRoute>
            <Profile />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
