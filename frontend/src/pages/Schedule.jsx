import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiRequest, formatDay, posterUrl, todayISO } from "../api";
import "./Schedule.css";

function groupByDate(items) {
  const groups = [];
  items.forEach((item) => {
    const last = groups.at(-1);
    if (last && last.date === item.scheduled_date) last.items.push(item);
    else groups.push({ date: item.scheduled_date, items: [item] });
  });
  return groups;
}

function ScheduleItem({ item, onChanged, onRemoved, onError }) {
  const [note, setNote] = useState(item.note || "");
  const [rating, setRating] = useState("8");
  const [markingWatched, setMarkingWatched] = useState(false);

  async function update(changes) {
    try {
      onChanged(await apiRequest(`/schedule/${item.id}`, { method: "PATCH", body: changes }));
    } catch (error) {
      onError(error.message);
    }
  }

  async function remove() {
    try {
      await apiRequest(`/schedule/${item.id}`, { method: "DELETE" });
      onRemoved(item.id);
    } catch (error) {
      onError(error.message);
    }
  }

  async function markWatched() {
    const value = Number(rating);
    if (!Number.isInteger(value) || value < 0 || value > 10) {
      onError("Enter a whole-number rating from 0 to 10.");
      return;
    }
    try {
      await apiRequest(`/schedule/${item.id}/watched`, { method: "POST", body: { rating: value } });
      onRemoved(item.id, `${item.title} moved to your watched movies.`);
    } catch (error) {
      onError(error.message);
    }
  }

  return (
    <li className="schedule-item">
      {posterUrl(item.poster_path) ? (
        <img className="schedule-poster" src={posterUrl(item.poster_path, "w154")} alt="" loading="lazy" />
      ) : (
        <div className="schedule-poster schedule-poster-empty" aria-hidden="true">FILM</div>
      )}
      <div className="schedule-body">
        <h3>{item.title}{item.year ? <span> ({item.year})</span> : null}</h3>
        <div className="schedule-fields">
          <label>
            Day
            <input
              type="date"
              min={todayISO()}
              value={item.scheduled_date}
              onChange={(event) => event.target.value && update({ scheduled_date: event.target.value })}
            />
          </label>
          <label>
            Note
            <input
              value={note}
              maxLength="200"
              placeholder="Add a note"
              onChange={(event) => setNote(event.target.value)}
              onBlur={() => note !== (item.note || "") && update({ note })}
            />
          </label>
        </div>
        {markingWatched ? (
          <div className="schedule-watched">
            <label>
              Rating (0-10)
              <input type="number" min="0" max="10" step="1" value={rating} onChange={(event) => setRating(event.target.value)} />
            </label>
            <button type="button" className="schedule-primary" onClick={markWatched}>Save</button>
            <button type="button" onClick={() => setMarkingWatched(false)}>Cancel</button>
          </div>
        ) : (
          <div className="schedule-actions">
            <button type="button" className="schedule-primary" onClick={() => setMarkingWatched(true)}>Mark watched</button>
            <button type="button" onClick={remove}>Remove</button>
          </div>
        )}
      </div>
    </li>
  );
}

export default function Schedule() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    apiRequest("/schedule")
      .then(setItems)
      .catch((requestError) => setError(requestError.message))
      .finally(() => setLoading(false));
  }, []);

  function handleChanged(updated) {
    setError("");
    setItems((current) =>
      current
        .map((item) => (item.id === updated.id ? updated : item))
        .sort((a, b) => a.scheduled_date.localeCompare(b.scheduled_date) || a.id - b.id)
    );
  }

  function handleRemoved(id, successMessage = "") {
    setError("");
    setMessage(successMessage);
    setItems((current) => current.filter((item) => item.id !== id));
  }

  return (
    <main className="schedule-page">
      <div className="schedule-container">
        <header className="schedule-header">
          <div>
            <p className="schedule-kicker">UP NEXT</p>
            <h1>Your watch schedule</h1>
            <p>Plan which movie you will watch and on what day. It shows up on your public profile.</p>
          </div>
          <Link className="schedule-add" to="/search">Schedule a movie</Link>
        </header>

        {loading && <p className="schedule-message">Loading your schedule...</p>}
        {error && <p className="schedule-message schedule-error" role="alert">{error}</p>}
        {message && <p className="schedule-message schedule-success" role="status">{message}</p>}

        {!loading && !items.length && !error && (
          <section className="schedule-empty">
            <p className="schedule-kicker">NOTHING PLANNED</p>
            <h2>Your schedule is empty</h2>
            <p>Search for a movie and choose Schedule to pick a day for it.</p>
          </section>
        )}

        {groupByDate(items).map((group) => (
          <section className="schedule-day" key={group.date}>
            <h2>{group.date === todayISO() ? "Today" : formatDay(group.date)}</h2>
            <ul>
              {group.items.map((item) => (
                <ScheduleItem key={item.id} item={item} onChanged={handleChanged} onRemoved={handleRemoved} onError={setError} />
              ))}
            </ul>
          </section>
        ))}
      </div>
    </main>
  );
}
