import { Navigate, useLocation } from "react-router-dom";
import { TOKEN_KEY } from "../api";

export default function ProtectedRoute({ children }) {
  const location = useLocation();

  if (!localStorage.getItem(TOKEN_KEY)) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return children;
}
