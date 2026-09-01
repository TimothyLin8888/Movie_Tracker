import { useState } from "react";
import "./Search.css";

function Search() {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState([]);
    const [mediaType, setMediaType] = useState("movie");
    const [loading, setLoading] = useState(false);

    async function handleSearch(e) {
        e.preventDefault();

        if (!query.trim()) return;

        setLoading(true);

        try {
            const response = await fetch(
                `http://localhost:8000/search/${mediaType}?query=${encodeURIComponent(query)}`
            );

            const data = await response.json();

            setResults(data);
        } catch (error) {
            console.error(error);
            setResults([]);
        }
        
        setLoading(false);
    }

    return (
        <div className="Search">

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

                <div className="movie-grid">

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

                                <h3>{movie.title}</h3>

                                <p>{movie.date}</p>

                                <p>{movie.description}</p>

                            </div>

                        </div>

                    ))}

                </div>

            </div>

        </div>
    );
}

export default Search;