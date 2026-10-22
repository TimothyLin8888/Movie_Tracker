import { Bar } from "react-chartjs-2";
import { BarElement, CategoryScale, Chart as ChartJS, LinearScale, Tooltip } from "chart.js";
import "./StatsPanel.css";

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip);

const ACCENT = "#d65a38";
const MUTED = "#8a8a8a";
const GRID = "#2e2e2e";

const tooltip = { backgroundColor: "#111111", titleColor: "#f0f0f0", bodyColor: "#f0f0f0", padding: 10 };

function barOptions(horizontal = false) {
  const valueAxis = { beginAtZero: true, ticks: { color: MUTED, precision: 0 }, grid: { color: GRID }, border: { display: false } };
  const labelAxis = { ticks: { color: MUTED }, grid: { display: false }, border: { display: false } };
  return {
    indexAxis: horizontal ? "y" : "x",
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip },
    scales: horizontal ? { x: valueAxis, y: labelAxis } : { x: labelAxis, y: valueAxis },
  };
}

function barData(labels, values) {
  return { labels, datasets: [{ data: values, backgroundColor: ACCENT, borderRadius: 4, maxBarThickness: 40 }] };
}

function shortMonth(isoMonth) {
  const [year, month] = isoMonth.split("-").map(Number);
  return new Date(year, month - 1, 1).toLocaleDateString(undefined, { month: "short" });
}

function languageName(code) {
  try {
    return new Intl.DisplayNames(undefined, { type: "language" }).of(code) || code;
  } catch {
    return code;
  }
}

function StatCard({ label, value, detail }) {
  return (
    <article className="sp-stat">
      <p className="sp-stat-label">{label}</p>
      <strong className="sp-stat-value">{value}</strong>
      {detail && <p className="sp-stat-detail">{detail}</p>}
    </article>
  );
}

function ChartCard({ kicker, title, note, children }) {
  return (
    <article className="sp-card">
      <div className="sp-card-head">
        <div>
          <p className="sp-kicker">{kicker}</p>
          <h2>{title}</h2>
        </div>
        {note && <span className="sp-note">{note}</span>}
      </div>
      {children}
    </article>
  );
}

export default function StatsPanel({ stats }) {
  const { totals } = stats;

  if (!totals.films) {
    return (
      <section className="sp-empty">
        <p className="sp-kicker">A QUIET SCREEN</p>
        <h2>No films logged yet</h2>
        <p>Stats appear here as soon as the first movie is added.</p>
      </section>
    );
  }

  const months = stats.films_per_month;
  const years = stats.films_per_year;
  const ratedCount = stats.rating_distribution.reduce((sum, item) => sum + item.count, 0);
  const hasRuntimeData = totals.hours > 0;

  return (
    <div className="sp-root">
      <section className="sp-stats" aria-label="Overview">
        <StatCard label="Films watched" value={totals.films.toLocaleString()} />
        <StatCard
          label="Time spent"
          value={hasRuntimeData ? `${Math.round(totals.hours).toLocaleString()} h` : "--"}
          detail={totals.avg_runtime ? `${totals.avg_runtime} min average` : undefined}
        />
        <StatCard
          label="Average rating"
          value={totals.avg_rating === null ? "--" : `${totals.avg_rating}/10`}
          detail={`${ratedCount} rated`}
        />
        <StatCard label="Favorites" value={totals.favorites} />
      </section>

      <section className="sp-grid">
        <ChartCard kicker="PACE" title="Last 12 months" note={`${months.reduce((sum, item) => sum + item.count, 0)} films`}>
          <div className="sp-chart">
            <Bar data={barData(months.map((item) => shortMonth(item.month)), months.map((item) => item.count))} options={barOptions()} />
          </div>
        </ChartCard>

        {stats.top_genres.length > 0 && (
          <ChartCard kicker="TASTE" title="Top genres">
            <div className="sp-chart">
              <Bar data={barData(stats.top_genres.map((item) => item.name), stats.top_genres.map((item) => item.count))} options={barOptions(true)} />
            </div>
          </ChartCard>
        )}

        <ChartCard kicker="SCORES" title="How I rate" note={`${ratedCount} rated`}>
          <div className="sp-chart">
            <Bar data={barData(stats.rating_distribution.map((item) => item.rating), stats.rating_distribution.map((item) => item.count))} options={barOptions()} />
          </div>
        </ChartCard>

        {stats.decades.length > 0 && (
          <ChartCard kicker="ERAS" title="Films by decade">
            <div className="sp-chart">
              <Bar data={barData(stats.decades.map((item) => item.decade), stats.decades.map((item) => item.count))} options={barOptions()} />
            </div>
          </ChartCard>
        )}

        {years.length > 1 && (
          <ChartCard kicker="HISTORY" title="Films by year watched">
            <div className="sp-chart">
              <Bar data={barData(years.map((item) => String(item.year)), years.map((item) => item.count))} options={barOptions()} />
            </div>
          </ChartCard>
        )}
      </section>

      {(stats.top_directors.length > 0 || stats.top_rated.length > 0) && (
        <section className="sp-grid">
          {stats.top_directors.length > 0 && (
            <ChartCard kicker="FAVOURITE VOICES" title="Most-watched directors">
              <ol className="sp-ranking">
                {stats.top_directors.map((director) => (
                  <li key={director.name}><span>{director.name}</span><strong>{director.count}</strong></li>
                ))}
              </ol>
              {stats.languages.length > 1 && (
                <p className="sp-footnote">
                  Languages: {stats.languages.map((item) => `${languageName(item.code)} (${item.count})`).join(", ")}
                </p>
              )}
            </ChartCard>
          )}
          {stats.top_rated.length > 0 && (
            <ChartCard kicker="HIGH MARKS" title="Highest rated">
              <ol className="sp-ranking">
                {stats.top_rated.map((film) => (
                  <li key={`${film.title}-${film.watch_date}`}><span>{film.title}</span><strong>{film.rating}/10</strong></li>
                ))}
              </ol>
            </ChartCard>
          )}
        </section>
      )}
    </div>
  );
}
