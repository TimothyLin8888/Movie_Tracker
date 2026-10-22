import { useEffect, useState } from "react";
import { API_URL, apiRequest, todayISO } from "../api";
import "./Search.css";

function Search() {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState([]);
    const [mediaType, setMediaType] = useState("movie");
    const [loading, setLoading] = useState(false);
    const [lists, setLists] = useState([]);
    const [activeMovie, setActiveMovie] = useState(null);
    const [rating, setRating] = useState("8");
    const [panelMode, setPanelMode] = useState("add");
    const [watchDate, setWatchDate] = useState(todayISO());
    const [scheduledDate, setScheduledDate] = useState(todayISO());
    const [note, setNote] = useState("");
    const [selectedListIds, setSelectedListIds] = useState([]);
    const [newListName, setNewListName] = useState("");
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");

    useEffect(() => {
        apiRequest("/library/lists").then(setLists).catch(() => {});
    }, []);

    async function handleSearch(e) {
        e.preventDefault();

        if (!query.trim()) return;

        setLoading(true);

        try {
            const response = await fetch(
                `${API_URL}/search/${mediaType}?query=${encodeURIComponent(query)}`
            );

            const data = await response.json();

            setResults(data);
            setError("");
        } catch (error) {
            console.error(error);
            setResults([]);
            setError("Search is unavailable right now.");
        }
        
        setLoading(false);
    }

    function openPanel(movie, mode) {
        setActiveMovie(movie);
        setPanelMode(mode);
        setRating("8");
        setWatchDate(todayISO());
        setScheduledDate(todayISO());
        setNote("");
        setSelectedListIds([]);
        setMessage("");
        setError("");
    }

    async function createList(event) {
        event.preventDefault();
        if (!newListName.trim()) return;
        try {
            const data = await apiRequest("/library/lists", { method: "POST", body: { name: newListName } });
            setLists((current) => [...current, data].sort((first, second) => first.name.localeCompare(second.name)));
            setSelectedListIds((current) => [...current, data.id]);
            setNewListName("");
        } catch (requestError) {
            setError(requestError.message);
        }
    }

    function movieFields() {
        return {
            tmdb_id: activeMovie.id,
            title: activeMovie.title,
            poster: activeMovie.poster && activeMovie.poster.startsWith("/") ? activeMovie.poster : null,
            date: /^\d{4}-\d{2}-\d{2}$/.test(activeMovie.date) ? activeMovie.date : null,
            description: activeMovie.description,
        };
    }

    async function addMovie() {
        const numericRating = Number(rating);
        if (!Number.isInteger(numericRating) || numericRating < 0 || numericRating > 10) {
            setError("Enter a whole-number rating from 0 to 10.");
            return;
        }
        try {
            await apiRequest("/library/add", {
                method: "POST",
                body: { ...movieFields(), rating: numericRating, watch_date: watchDate || null, list_ids: selectedListIds },
            });
            setLists(await apiRequest("/library/lists"));
            setMessage(`${activeMovie.title} was added to your profile.`);
            setActiveMovie(null);
        } catch (requestError) {
            setError(requestError.message);
        }
    }

    async function scheduleMovie() {
        if (!scheduledDate) {
            setError("Pick the day you plan to watch it.");
            return;
        }
        try {
            await apiRequest("/schedule", {
                method: "POST",
                body: { ...movieFields(), scheduled_date: scheduledDate, note: note || null },
            });
            setMessage(`${activeMovie.title} is on your schedule.`);
            setActiveMovie(null);
        } catch (requestError) {
            setError(requestError.message);
        }
    }

    return (
        <div className="search-page">

            <div className="search-container">

                <h1>Search</h1>

                <div className="media-toggle">

                    <button
                        className={mediaType === "movie" ? "active" : ""}
                        onClick={() => setMediaType("movie")}
                    >
                        Movies
                    </button>

                    <button
                        className={mediaType === "tv" ? "active" : ""}
                        onClick={() => setMediaType("tv")}
                    >
                        TV Shows
                    </button>

                </div>

                <form
                    role="search"
                    id="movie-search-form"
                    className="search-form"
                    onSubmit={handleSearch}
                >

                    <label
                        htmlFor="movie-search"
                        className="sr-only"
                    >
                        Search
                    </label>

                    <input
                        type="search"
                        id="movie-search"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder={`Search ${mediaType}s...`}
                    />

                    <button type="submit">
                        Search
                    </button>

                </form>

                {loading && (
                    <p>Loading...</p>
                )}
                {message && <p className="success">{message}</p>}
                {error && <p className="error" role="alert">{error}</p>}

                <div className="results">

                    {results.map((movie) => (

                        <div
                            className="search-card"
                            key={movie.id}
                        >

                            {movie.poster && (
                                <img
                                    src={`https://image.tmdb.org/t/p/w500${movie.poster}`}
                                    alt={movie.title}
                                />
                            )}

                            <div className="movie-info">

                                <h2>{movie.title}</h2>

                                <p>{movie.date}</p>

                                <p>{movie.description}</p>

                                {mediaType === "movie" && <div className="movie-buttons">
                                    <button type="button" onClick={() => openPanel(movie, "add")}>Add to profile</button>
                                    <button type="button" onClick={() => openPanel(movie, "schedule")}>Schedule</button>
                                </div>}

                            </div>

                        </div>

                    ))}

                </div>

                {activeMovie && <section className="add-panel" aria-labelledby="add-movie-title">
                    <div className="add-panel-header">
                        <div><p className="search-kicker">{panelMode === "add" ? "ADD TO PROFILE" : "SCHEDULE A WATCH"}</p><h2 id="add-movie-title">{activeMovie.title}</h2></div>
                        <button type="button" className="close-button" onClick={() => setActiveMovie(null)} aria-label="Close">×</button>
                    </div>
                    {panelMode === "add" ? <>
                        <label htmlFor="movie-rating">Your rating <span>0–10</span></label>
                        <input id="movie-rating" type="number" min="0" max="10" step="1" value={rating} onChange={(event) => setRating(event.target.value)} />
                        <label htmlFor="movie-watch-date">Date watched</label>
                        <input id="movie-watch-date" type="date" max={todayISO()} value={watchDate} onChange={(event) => setWatchDate(event.target.value)} />
                        <fieldset>
                            <legend>Add to lists</legend>
                            {lists.length ? lists.map((list) => <label className="list-option" key={list.id}><input type="checkbox" checked={selectedListIds.includes(list.id)} onChange={() => setSelectedListIds((current) => current.includes(list.id) ? current.filter((id) => id !== list.id) : [...current, list.id])} /> {list.name}</label>) : <p>No lists yet. Create one below.</p>}
                        </fieldset>
                        <form className="new-list-form" onSubmit={createList}>
                            <input aria-label="New list name" value={newListName} onChange={(event) => setNewListName(event.target.value)} placeholder="New list name, e.g. Ghibli" />
                            <button type="submit">Create list</button>
                        </form>
                        <button type="button" className="save-movie-button" onClick={addMovie}>Save movie</button>
                    </> : <>
                        <label htmlFor="movie-scheduled-date">Day you will watch it</label>
                        <input id="movie-scheduled-date" type="date" min={todayISO()} value={scheduledDate} onChange={(event) => setScheduledDate(event.target.value)} />
                        <label htmlFor="movie-note">Note <span>optional</span></label>
                        <input id="movie-note" maxLength="200" value={note} onChange={(event) => setNote(event.target.value)} placeholder="e.g. with friends, 8pm" />
                        <button type="button" className="save-movie-button" onClick={scheduleMovie}>Add to schedule</button>
                    </>}
                </section>}

            </div>

        </div>
    );
}

export default Search;