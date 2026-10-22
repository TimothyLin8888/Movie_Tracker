import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
// Navbar is handled externally via Navbar.jsx
import "./Dashboard.css";
import { API_URL } from "../api";


export default function Dashboard() {
  const [watches, setWatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const user = JSON.parse(localStorage.getItem("movie_tracker_user") || "null");

  useEffect(() => {
    async function fetchWatches() {
      try {
        const token = localStorage.getItem("movie_tracker_token");
        const response = await fetch(`${API_URL}/analytics`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        if (!response.ok) throw new Error(response.status === 401 ? "Sign in to see your dashboard." : "Unable to load your dashboard.");
        setWatches(await response.json());
      } catch (fetchError) {
        setError(fetchError.message);
      } finally {
        setLoading(false);
      }
    }
    fetchWatches();
  }, []);

  const summary = useMemo(() => {
    const rated = watches.filter((watch) => Number.isFinite(watch.personal_rating));
    const genres = {};
    watches.forEach((watch) => {
      (watch.genres || "").split(",").map((genre) => genre.trim()).filter(Boolean).forEach((genre) => {
        genres[genre] = (genres[genre] || 0) + 1;
      });
    });
    const topGenre = Object.entries(genres).sort(([, countA], [, countB]) => countB - countA)[0]?.[0] || "--";
    return {
      averageRating: rated.length ? (rated.reduce((sum, watch) => sum + watch.personal_rating, 0) / rated.length).toFixed(1) : "--",
      favoriteCount: watches.filter((watch) => watch.favorite).length,
      topGenre,
    };
  }, [watches]);

  const recentWatches = watches.slice(-3).reverse();

  return (
    <div className="sl-app">
      <main className="sl-main">
        <header className="sl-header">
          <p className="sl-eyebrow">WELCOME BACK</p>
          <h1 className="sl-title">{user?.username ? `${user.username}'s movie dashboard` : "Your movie dashboard"}</h1>
          <p className="sl-subtitle">A snapshot of your watch history and ratings</p>
        </header>

        <section className="sl-stats">
          {[
            { value: watches.length, label: "Movies watched", accent: false },
            { value: summary.averageRating, label: "Avg rating", accent: true },
            { value: summary.favoriteCount, label: "Favorites", accent: false },
            { value: summary.topGenre, label: "Top genre", accent: false },
          ].map(({ value, label, accent }) => (
            <div className="sl-stat-card" key={label}>
              <span className={`sl-stat-value${accent ? " sl-stat-accent" : ""}`}>{value}</span>
              <span className="sl-stat-label">{label}</span>
            </div>
          ))}
        </section>
        {loading && <p className="sl-message">Gathering your watch history...</p>}
        {error && <p className="sl-message sl-error" role="alert">{error}</p>}
        {!loading && !error && <section className="sl-section">
          <div className="sl-section-header">
            <h2 className="sl-section-title">Recently watched</h2>
          </div>
          {recentWatches.length ? <div className="sl-movies-grid">
            {recentWatches.map((movie) => (
              <article className="sl-movie-card" key={`${movie.id}-${movie.watch_date}`}>
                <div className="sl-movie-poster">
                  <span className="sl-poster-icon" aria-hidden="true">FILM</span>
                </div>
                <div className="sl-movie-info">
                  <p className="sl-movie-title">{movie.title}</p>
                  <p className="sl-movie-meta">
                    {movie.genres || "Genre unavailable"} · {movie.watch_date || "Date unavailable"}
                  </p>
                  {Number.isFinite(movie.personal_rating) && <p className="sl-movie-rating">Rated {movie.personal_rating}/10</p>}
                </div>
              </article>
            ))}
          </div> : <div className="sl-empty-state"><h2>No watched movies yet</h2><p>Add ratings to start building your dashboard, or <Link to="/import">import your Letterboxd or IMDb history</Link>.</p></div>}
        </section>}
      </main>
    </div>
  );
}