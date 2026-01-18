import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { NavBar } from "./components/NavBar";
import { LoginPage } from "./pages/LoginPage";
import { ClientsPage } from "./pages/ClientsPage";
import { PackagesPage } from "./pages/PackagesPage";
import { EventsPage } from "./pages/EventsPage";
import { PublicEventsPage } from "./pages/PublicEventsPage";
import { PublicPackagesPage } from "./pages/PublicPackagesPage";
import { ProtectedRoute } from "./router/ProtectedRoute";

export default function App() {
  return (
    <BrowserRouter>
      <NavBar />
      <Routes>
        <Route path="/" element={<Navigate to="/public/events" replace />} />

        <Route path="/public/events" element={<PublicEventsPage />} />
        <Route path="/public/packages" element={<PublicPackagesPage />} />

        <Route path="/login" element={<LoginPage />} />

        <Route
          path="/clients"
          element={
            <ProtectedRoute roles={["admin", "owner-event"]}>
              <ClientsPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/packages"
          element={
            <ProtectedRoute roles={["admin", "owner-event"]}>
              <PackagesPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/events"
          element={
            <ProtectedRoute roles={["admin", "owner-event"]}>
              <EventsPage />
            </ProtectedRoute>
          }
        />

        <Route path="*" element={<div>Not found</div>} />
      </Routes>
    </BrowserRouter>
  );
}
