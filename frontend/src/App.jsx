import "./App.css";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import Navbar from "./components/Navbar";
import Dashboard from "./pages/Dashboard";
import Search from "./pages/Search";
import Watchlists from "./pages/Watchlists";
import Analytics from "./pages/Analytics";
import Login from "./pages/Login";
import Register from "./pages/Register";

function AppRoutes() {
  const location = useLocation();
  const isAuthRoute = ["/login", "/register"].includes(location.pathname);

  return (
    <div className={isAuthRoute ? "auth-shell" : "app-shell"}>
      {!isAuthRoute && <Navbar />}
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/" element={<Dashboard />} />
        <Route path="/search" element={<Search />} />
        <Route path="/watchlist" element={<Watchlists />} />
        <Route path="/analytics" element={<Analytics />} />
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