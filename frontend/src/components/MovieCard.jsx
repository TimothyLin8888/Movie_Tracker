import "./MovieCard.css";

function MovieCard({ title, date, category, description }) {
  return (
    <article className="movie-card">
      <div className="movie-content">
        <div className="movie-main">
          <h3>{title}</h3>
          {description && <p className="movie-description">{description}</p>}
        </div>

        <div className="movie-meta">
          <span className="movie-category">{category}</span>
          <span className="movie-date">{date}</span>
        </div>
      </div>
    </article>
  );
}

export default MovieCard;