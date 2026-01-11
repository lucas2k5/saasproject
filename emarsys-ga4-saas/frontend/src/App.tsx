import { Navigate, Route, Routes } from "react-router-dom";
import AbandonedCarts from "./pages/AbandonedCarts";
import AiAdvisor from "./pages/AiAdvisor";
import Analytics from "./pages/Analytics";
import Campaigns from "./pages/Campaigns";
import Dashboard from "./pages/Dashboard";
import Home from "./pages/Home";
import Playbooks from "./pages/Playbooks";
import Profile from "./pages/Profile";
import Recommendations from "./pages/Recommendations";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import ProtectedRoute from "./components/ProtectedRoute";

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
            <Recommendations />
          </ProtectedRoute>
        }
      />
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
