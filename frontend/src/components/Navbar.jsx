import { NavLink } from "react-router-dom";
import './Navbar.css'

const navLinks = [
  { label: "Dashboard", path: "/" },
  { label: "Search", path: "/search" },
  { label: "Watchlist", path: "/watchlist" },
  { label: "Rankings", path: "/rankings" },
  { label: "Analytics", path: "/analytics" },
];

const Navbar = () => {
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
      <div className="sl-avatar">JD</div>
    </nav>
  );
};

export default Navbar;