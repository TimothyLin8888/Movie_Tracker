import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { authFetch } from "../api";
import "./Import.css";

const CHUNK_SIZE = 40;

const SOURCES = {
  letterboxd: {
    label: "Letterboxd",
    accept: ".zip,.csv,.txt",
    steps: [
      "On letterboxd.com, open Settings, then the Data tab, and choose Export your data.",
      "Upload the .zip file you download as is, without unzipping it. It brings in every film you marked watched, with your ratings and the dates from your diary.",
      "Films you liked and the favorites pinned on your profile become Favorites, and your lists come across too. Only films you marked watched can go into a list. Your watchlist, reviews and comments are not imported.",
      "You can also upload a single ratings.csv, diary.csv or watched.csv instead.",
    ],
  },
  imdb: {
    label: "IMDb",
    accept: ".csv,.txt",
    steps: [
      "On imdb.com, open Your Ratings (from your profile menu).",
      "Use the three-dot menu and choose Export, then upload the CSV file you download.",
      "TV shows are skipped. Only movies are imported.",
    ],
  },
};

const COUNT_KEYS = ["imported_movies", "duplicates", "not_found", "skipped_tv", "database_errors", "favorites_set", "list_entries_added", "lists_created", "lists_skipped_unwatched"];
const EMPTY_TOTALS = { notFoundTitles: [], ...Object.fromEntries(COUNT_KEYS.map((key) => [key, 0])) };

export default function Import() {
  const [source, setSource] = useState("letterboxd");
  const [file, setFile] = useState(null);
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState({ done: 0, total: 0 });
  const [totals, setTotals] = useState(EMPTY_TOTALS);
  const [finished, setFinished] = useState(false);
  const [error, setError] = useState("");
  const cancelRef = useRef(false);
  const config = SOURCES[source];

  function chooseSource(next) {
    if (running) return;
    setSource(next);
    setFile(null);
    setFinished(false);
    setError("");
    setTotals(EMPTY_TOTALS);
    setProgress({ done: 0, total: 0 });
  }

  async function runImport() {
    if (!file) return;
    cancelRef.current = false;
    setRunning(true);
    setFinished(false);
    setError("");
    setTotals(EMPTY_TOTALS);
    setProgress({ done: 0, total: 0 });

    const running_totals = { ...EMPTY_TOTALS, notFoundTitles: [] };
    let offset = 0;

    try {
      while (offset !== null && !cancelRef.current) {
        const form = new FormData();
        form.append("file", file);
        const response = await authFetch(`/library/import/${source}?offset=${offset}&limit=${CHUNK_SIZE}`, {
          method: "POST",
          body: form,
        });
        const data = await response.json().catch(() => null);
        if (!response.ok) {
          throw new Error(typeof data?.detail === "string" ? data.detail : "The import failed. Please try again.");
        }
        if (typeof data?.total !== "number") {
          throw new Error("The server sent an unexpected reply. Restart the backend so it picks up the latest code.");
        }

        for (const key of COUNT_KEYS) {
          running_totals[key] += data[key] || 0;
        }
        running_totals.notFoundTitles.push(...(data.not_found_titles || []));
        setTotals({ ...running_totals, notFoundTitles: [...running_totals.notFoundTitles] });

        offset = data.next_offset ?? null;
        setProgress({ done: offset === null ? data.total : Math.min(offset, data.total), total: data.total });
      }
      setFinished(true);
    } catch (importError) {
      setError(`${importError.message} Anything already imported was kept, and it's safe to run the import again.`);
    } finally {
      setRunning(false);
    }
  }

  const percent = progress.total ? Math.round((progress.done / progress.total) * 100) : 0;
  const showResults = running || finished || totals.imported_movies + totals.duplicates + totals.not_found > 0;

  return (
    <main className="import-page">
      <div className="import-container">
        <header className="import-header">
          <p className="import-kicker">BRING YOUR HISTORY</p>
          <h1>Import your movies</h1>
          <p>Add everything you have already watched from Letterboxd or IMDb. Movies you already have are skipped, so running it twice is safe.</p>
        </header>

        <div className="import-tabs" role="tablist" aria-label="Import source">
          {Object.entries(SOURCES).map(([key, value]) => (
            <button
              key={key}
              type="button"
              role="tab"
              aria-selected={source === key}
              className={source === key ? "active" : ""}
              disabled={running}
              onClick={() => chooseSource(key)}
            >
              {value.label}
            </button>
          ))}
        </div>

        <section className="import-card">
          <ol className="import-steps">
            {config.steps.map((step) => <li key={step}>{step}</li>)}
          </ol>

          <label className="import-file">
            <span>{config.label} file</span>
            <input
              key={source}
              type="file"
              accept={config.accept}
              disabled={running}
              onChange={(event) => {
                setFile(event.target.files[0] || null);
                setFinished(false);
                setError("");
              }}
            />
          </label>

          <div className="import-actions">
            <button type="button" className="import-primary" onClick={runImport} disabled={!file || running}>
              {running ? "Importing..." : `Import from ${config.label}`}
            </button>
            {running && <button type="button" onClick={() => { cancelRef.current = true; }}>Stop after this batch</button>}
          </div>
          {running && <p className="import-hint">Large libraries can take a few minutes. Keep this page open.</p>}
        </section>

        {error && <p className="import-error" role="alert">{error}</p>}

        {showResults && (
          <section className="import-card" aria-live="polite">
            <div className="import-progress" role="progressbar" aria-valuenow={percent} aria-valuemin="0" aria-valuemax="100">
              <div style={{ width: `${percent}%` }} />
            </div>
            <p className="import-progress-label">
              {progress.total ? `${progress.done} of ${progress.total} films checked (${percent}%)` : "Starting..."}
            </p>

            <dl className="import-totals">
              <div><dt>Added</dt><dd>{totals.imported_movies}</dd></div>
              <div><dt>Already in your library</dt><dd>{totals.duplicates}</dd></div>
              <div><dt>Not found</dt><dd>{totals.not_found}</dd></div>
              {source === "imdb" && <div><dt>TV shows skipped</dt><dd>{totals.skipped_tv}</dd></div>}
              {source === "letterboxd" && totals.favorites_set > 0 && <div><dt>Favorites set</dt><dd>{totals.favorites_set}</dd></div>}
              {source === "letterboxd" && totals.lists_created > 0 && <div><dt>Lists created</dt><dd>{totals.lists_created}</dd></div>}
              {source === "letterboxd" && totals.list_entries_added > 0 && <div><dt>Films added to lists</dt><dd>{totals.list_entries_added}</dd></div>}
              {totals.database_errors > 0 && <div><dt>Errors</dt><dd>{totals.database_errors}</dd></div>}
            </dl>

            {totals.lists_skipped_unwatched > 0 && (
              <p className="import-hint">
                {totals.lists_skipped_unwatched} films in your lists were left out because they aren't marked as watched.
              </p>
            )}

            {totals.notFoundTitles.length > 0 && (
              <details className="import-notfound">
                <summary>Films I couldn't match ({totals.not_found})</summary>
                <ul>{totals.notFoundTitles.map((title) => <li key={title}>{title}</li>)}</ul>
              </details>
            )}

            {finished && (
              <p className="import-done">
                Import finished. <Link to="/analytics">See your stats</Link> or <Link to="/">go to your dashboard</Link>.
              </p>
            )}
          </section>
        )}
      </div>
    </main>
  );
}
