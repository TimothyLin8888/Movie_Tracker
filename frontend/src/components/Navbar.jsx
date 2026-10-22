import { useEffect, useRef, useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import './Navbar.css'

const navLinks = [
  { label: "Dashboard", path: "/" },
  { label: "Search", path: "/search" },
  { label: "Watchlist", path: "/watchlist" },
  { label: "Schedule", path: "/schedule" },
  { label: "Rankings", path: "/rankings" },
  { label: "Analytics", path: "/analytics" },
];

const Navbar = () => {
  const navigate = useNavigate();
  const menuRef = useRef(null);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const storedUser = JSON.parse(localStorage.getItem("movie_tracker_user") || "null");
  const username = storedUser?.username || "Jordan Doe";
  const initials = username
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  useEffect(() => {
    const closeMenu = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsMenuOpen(false);
      }
    };

    document.addEventListener("mousedown", closeMenu);
    return () => document.removeEventListener("mousedown", closeMenu);
  }, []);

  const handleSignOut = () => {
    localStorage.removeItem("movie_tracker_token");
    localStorage.removeItem("movie_tracker_user");
    setIsMenuOpen(false);
    navigate("/login");
  };

  return (
    <nav className="sl-nav">
      <div className="sl-nav-left">
        <NavLink to={"/"}>
        <span className="sl-logo-icon" aria-hidden="true">☐</span>
        <span className="sl-logo-text">Name</span>
        </NavLink>
      </div>
      <ul className="sl-nav-links">
        {navLinks.map((link) => (
          <li key={link.path}>
            <NavLink to={link.path} className={({ isActive }) => `sl-nav-link${isActive ? " active" : ""}`}>
              {link.label}
            </NavLink>
          </li>
        ))}
      </ul>
      <div className="sl-profile" ref={menuRef}>
        <button
          className="sl-avatar"
          type="button"
          aria-expanded={isMenuOpen}
          aria-haspopup="menu"
          aria-label={`Open profile menu for ${username}`}
          onClick={() => setIsMenuOpen((open) => !open)}
        >
          {initials}
        </button>
        {isMenuOpen && (
          <div className="sl-profile-menu" role="menu">
            <div className="sl-profile-summary">
              <strong>{username}</strong>
              <span>{storedUser?.email || "Your movie profile"}</span>
            </div>
            <Link to="/import" role="menuitem" onClick={() => setIsMenuOpen(false)}>
              Import movies
            </Link>
            <Link to="/account" role="menuitem" onClick={() => setIsMenuOpen(false)}>
              Account settings
            </Link>
            <button type="button" role="menuitem" onClick={handleSignOut}>
              Sign out
            </button>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;