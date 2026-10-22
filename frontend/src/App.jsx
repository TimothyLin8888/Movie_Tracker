import "./App.css";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";
import Dashboard from "./pages/Dashboard";
import Search from "./pages/Search";
import Watchlists from "./pages/Watchlists";
import Analytics from "./pages/Analytics";
import Schedule from "./pages/Schedule";
import Import from "./pages/Import";
import Account from "./pages/Account";
import PublicProfile from "./pages/PublicProfile";
import Login from "./pages/Login";
import Register from "./pages/Register";

function AppRoutes() {
  const location = useLocation();
  const isAuthRoute = ["/login", "/register"].includes(location.pathname);
  const isPublicProfile = location.pathname.startsWith("/u/");
  const showNavbar = !isAuthRoute && !isPublicProfile;

  return (
    <div className={isAuthRoute ? "auth-shell" : isPublicProfile ? undefined : "app-shell"}>
      {showNavbar && <Navbar />}
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/u/:username" element={<PublicProfile />} />
        <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/search" element={<ProtectedRoute><Search /></ProtectedRoute>} />
        <Route path="/watchlist" element={<ProtectedRoute><Watchlists /></ProtectedRoute>} />
        <Route path="/schedule" element={<ProtectedRoute><Schedule /></ProtectedRoute>} />
        <Route path="/import" element={<ProtectedRoute><Import /></ProtectedRoute>} />
        <Route path="/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
        <Route path="/account" element={<ProtectedRoute><Account /></ProtectedRoute>} />
      </Routes>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}

export default App;
