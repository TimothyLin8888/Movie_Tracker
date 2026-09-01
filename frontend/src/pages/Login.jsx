import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import "./Login.css";

const API_URL = "http://localhost:8000";

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
    if (error) setError("");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to sign in");
      }

      localStorage.setItem("movie_tracker_token", data.access_token);
      localStorage.setItem("movie_tracker_user", JSON.stringify(data.user));
      navigate(location.state?.from || "/", { replace: true });
    } catch (submitError) {
      setError(submitError.message || "Unable to sign in. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="login-page">
      <section className="login-panel" aria-labelledby="login-title">
        <div className="login-brand">
          <span className="login-brand-mark" aria-hidden="true">☐</span>
          <span>Name</span>
        </div>

        <div className="login-heading">
          <p className="sl-eyebrow">WELCOME BACK</p>
          <h1 id="login-title">Sign in to your tracker</h1>
          <p>Keep your watch history, ratings, and next picks in one place.</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <label htmlFor="email">Email address</label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            value={form.email}
            onChange={handleChange}
            required
          />

          <div className="login-label-row">
            <label htmlFor="password">Password</label>
            <button type="button" className="login-help" disabled title="Password recovery is not configured yet">
              Forgot password?
            </button>
          </div>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            placeholder="Enter your password"
            value={form.password}
            onChange={handleChange}
            required
          />

          {error && <p className="login-error" role="alert">{error}</p>}

          <button className="login-submit" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <p className="login-footer">
          New here? <Link to="/register">Create an account</Link>
        </p>
      </section>

      <aside className="login-aside" aria-label="Movie tracker highlight">
        <span className="login-aside-label">YOUR CINEMA, ORGANIZED</span>
        <p className="login-quote">“Every film has a place in your story.”</p>
        <div className="login-film-strip" aria-hidden="true">
          <span>THE</span><span>GODFATHER</span><span>2049</span>
        </div>
      </aside>
    </main>
  );
}
