import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { NavBar } from "./components/NavBar";
import { LoginPage } from "./pages/LoginPage";
import { ClientsPage } from "./pages/ClientsPage";
import { PackagesPage } from "./pages/PackagesPage";
import { EventsPage } from "./pages/EventsPage";
import { PublicEventsPage } from "./pages/PublicEventsPage";
import { PublicPackagesPage } from "./pages/PublicPackagesPage";
import { UsersPage } from "./pages/UsersPage";
import { BuyersPage } from "./pages/BuyersPage";
import { MyTicketsPage } from "./pages/MyTicketsPage";
import { ProtectedRoute } from "./router/ProtectedRoute";
import { useAuth } from "./auth/AuthContext";

// every API route needs a token (Lab 4), so the landing page depends on the role
function Home() {
  const { state } = useAuth();
  if (state.status === "loading") return <div>Loading...</div>;
  if (state.status !== "authenticated") return <Navigate to="/login" replace />;
  if (state.role === "admin") return <Navigate to="/users" replace />;
  if (state.role === "owner-event") return <Navigate to="/events" replace />;
  return <Navigate to="/browse/events" replace />;
}

const OWNER = ["owner-event"];
const ADMIN = ["admin"];
const VIEWERS = ["client", "owner-event"];

export default function App() {
  return (
    <BrowserRouter>
      <NavBar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<LoginPage />} />

        {/* admin: users and their data only */}
        <Route path="/users" element={<ProtectedRoute roles={ADMIN}><UsersPage /></ProtectedRoute>} />
        <Route path="/clients" element={<ProtectedRoute roles={ADMIN}><ClientsPage /></ProtectedRoute>} />

        {/* owner-event */}
        <Route path="/events" element={<ProtectedRoute roles={OWNER}><EventsPage /></ProtectedRoute>} />
        <Route path="/packages" element={<ProtectedRoute roles={OWNER}><PackagesPage /></ProtectedRoute>} />
        <Route path="/buyers" element={<ProtectedRoute roles={OWNER}><BuyersPage /></ProtectedRoute>} />

        {/* client (owner-event may browse too) */}
        <Route path="/browse/events" element={<ProtectedRoute roles={VIEWERS}><PublicEventsPage /></ProtectedRoute>} />
        <Route path="/browse/packages" element={<ProtectedRoute roles={VIEWERS}><PublicPackagesPage /></ProtectedRoute>} />
        <Route path="/my-tickets" element={<ProtectedRoute roles={["client"]}><MyTicketsPage /></ProtectedRoute>} />

        <Route path="/public/*" element={<Navigate to="/" replace />} />
        <Route path="*" element={<div>Not found</div>} />
      </Routes>
    </BrowserRouter>
  );
}
