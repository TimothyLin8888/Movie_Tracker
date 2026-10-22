import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { API_URL, formatDay, posterUrl, todayISO } from "../api";
import StatsPanel from "../components/StatsPanel";
import "./PublicProfile.css";

function PosterGrid({ films }) {
  return (
    <ul className="pp-posters">
      {films.map((film, index) => (
        <li key={`${film.title}-${film.watch_date}-${index}`}>
          <div className="pp-poster">
            {posterUrl(film.poster_path) ? (
              <img src={posterUrl(film.poster_path)} alt={film.title} loading="lazy" />
            ) : (
              <span className="pp-poster-empty">{film.title}</span>
            )}
            {film.rating !== null && <span className="pp-badge">{film.rating}</span>}
          </div>
          <p className="pp-poster-title">{film.title}</p>
        </li>
      ))}
    </ul>
  );
}

function groupByDate(items) {
  const groups = [];
  items.forEach((item) => {
    const last = groups.at(-1);
    if (last && last.date === item.scheduled_date) last.items.push(item);
    else groups.push({ date: item.scheduled_date, items: [item] });
  });
  return groups;
}

export default function PublicProfile() {
  const { username } = useParams();
  const [result, setResult] = useState({ key: null, status: "loading", profile: null });

  useEffect(() => {
    let ignore = false;
    const finish = (status, profile = null) => !ignore && setResult({ key: username, status, profile });
    fetch(`${API_URL}/public/${encodeURIComponent(username)}`)
      .then(async (response) => {
        if (response.status === 404) return finish("missing");
        if (!response.ok) return finish("error");
        finish("ready", await response.json());
      })
      .catch(() => finish("error"));
    return () => { ignore = true; };
  }, [username]);

  const status = result.key === username ? result.status : "loading";
  const profile = result.profile;

  useEffect(() => {
    document.title = profile ? `${profile.username}'s movie profile` : "Movie profile";
  }, [profile]);

  if (status === "loading") return <main className="pp-page"><p className="pp-message">Loading profile...</p></main>;

  if (status !== "ready") {
    return (
      <main className="pp-page">
        <div className="pp-container pp-missing">
          <p className="pp-kicker">{status === "missing" ? "NOT FOUND" : "SOMETHING WENT WRONG"}</p>
          <h1>{status === "missing" ? "This profile is private or doesn't exist" : "Couldn't load this profile"}</h1>
          <p>{status === "missing" ? "Check the link, or ask the owner to make their profile public." : "Please try again in a moment."}</p>
          <Link className="pp-cta" to="/register">Start your own movie profile</Link>
        </div>
      </main>
    );
  }

  const memberSince = new Date(profile.member_since).toLocaleDateString(undefined, { month: "long", year: "numeric" });
  const today = todayISO();

  return (
    <main className="pp-page">
      <div className="pp-container">
        <header className="pp-header">
          <div className="pp-avatar" aria-hidden="true">{profile.username.slice(0, 2).toUpperCase()}</div>
          <div>
            <h1>@{profile.username}</h1>
            {profile.bio && <p className="pp-bio">{profile.bio}</p>}
            <p className="pp-since">Tracking movies since {memberSince}</p>
          </div>
        </header>

        <section className="pp-section" aria-labelledby="pp-upnext">
          <p className="pp-kicker">UP NEXT</p>
          <h2 id="pp-upnext">What I'm watching soon</h2>
          {profile.schedule.length ? (
            groupByDate(profile.schedule).map((group) => (
              <div className="pp-day" key={group.date}>
                <h3>{group.date === today ? "Today" : formatDay(group.date)}</h3>
                <ul>
                  {group.items.map((item, index) => (
                    <li className="pp-schedule-item" key={`${item.title}-${index}`}>
                      {posterUrl(item.poster_path) ? (
                        <img src={posterUrl(item.poster_path, "w154")} alt="" loading="lazy" />
                      ) : (
                        <div className="pp-schedule-empty" aria-hidden="true">FILM</div>
                      )}
                      <div>
                        <strong>{item.title}</strong>
                        {item.year && <span> ({item.year})</span>}
                        {item.note && <p>{item.note}</p>}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            ))
          ) : (
            <p className="pp-muted">Nothing scheduled right now. Check back soon.</p>
          )}
        </section>

        <section className="pp-section" aria-labelledby="pp-stats">
          <p className="pp-kicker">BY THE NUMBERS</p>
          <h2 id="pp-stats">Watching stats</h2>
          <StatsPanel stats={profile.stats} />
        </section>

        {profile.recent.length > 0 && (
          <section className="pp-section" aria-labelledby="pp-recent">
            <p className="pp-kicker">RECENTLY WATCHED</p>
            <h2 id="pp-recent">Latest films and my ratings</h2>
            <PosterGrid films={profile.recent} />
          </section>
        )}

        {profile.favorites.length > 0 && (
          <section className="pp-section" aria-labelledby="pp-favorites">
            <p className="pp-kicker">FAVORITES</p>
            <h2 id="pp-favorites">Films I keep coming back to</h2>
            <PosterGrid films={profile.favorites} />
          </section>
        )}

        {profile.lists && profile.lists.length > 0 && (
          <section className="pp-section" aria-labelledby="pp-lists">
            <p className="pp-kicker">COLLECTIONS</p>
            <h2 id="pp-lists">Movie lists</h2>
            <ul className="pp-lists">
              {profile.lists.map((list) => (
                <li key={list.name}>{list.name}<span>{list.count} {list.count === 1 ? "film" : "films"}</span></li>
              ))}
            </ul>
          </section>
        )}

        <footer className="pp-footer">
          <Link className="pp-cta" to="/register">Start your own movie profile</Link>
        </footer>
      </div>
    </main>
  );
}
