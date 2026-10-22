import { useEffect, useState } from "react";
import "./Watchlists.css";
import { API_URL } from "../api";


function Watchlists() {
  const [lists, setLists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchWatchlists() {
      try {
        const token = localStorage.getItem("movie_tracker_token");
        const response = await fetch(`${API_URL}/library/lists`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });

        if (!response.ok) {
          throw new Error(response.status === 401 ? "Sign in to see your watchlists." : "Unable to load your watchlists.");
        }

        setLists(await response.json());
      } catch (fetchError) {
        setError(fetchError.message);
      } finally {
        setLoading(false);
      }
    }

    fetchWatchlists();
  }, []);

  return (
    <main className="watchlists-page">
      <div className="watchlists-container">
        <header className="watchlists-header">
          <div>
            <p className="watchlists-kicker">YOUR COLLECTIONS</p>
            <h1>Watchlists you created</h1>
            <p>Keep your films grouped by mood, project, or the next movie night.</p>
          </div>
          <span className="watchlists-count">{lists.length} {lists.length === 1 ? "list" : "lists"}</span>
        </header>

        {loading && <p className="watchlists-message">Loading your watchlists...</p>}
        {error && <p className="watchlists-message watchlists-error" role="alert">{error}</p>}
        {!loading && !error && (lists.length ? (
          <section className="watchlists-grid" aria-label="Your watchlists">
            {lists.map((list) => (
              <article className="watchlist-card" key={list.id}>
                <div className="watchlist-card-mark" aria-hidden="true">◎</div>
                <div>
                  <h2>{list.name}</h2>
                  <p>{list.count} {list.count === 1 ? "movie" : "movies"}</p>
                </div>
              </article>
            ))}
          </section>
        ) : (
          <section className="watchlists-empty">
            <p className="watchlists-kicker">A BLANK CANVAS</p>
            <h2>No watchlists yet</h2>
            <p>Create a list while adding a movie from Search, and it will appear here.</p>
          </section>
        ))}
      </div>
    </main>
  );
}

export default Watchlists;
