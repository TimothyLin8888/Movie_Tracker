import { useState } from "react";
// Navbar is handled externally via Navbar.jsx
import "./Dashboard.css";
 
const movies = [
  { title: "The Godfather", genres: ["Crime", "Drama"], year: 1972, rating: 9.2, color: "#2a0a0a" },
  { title: "Blade Runner 2049", genres: ["Sci-fi"], year: 2017, rating: 8.0, color: "#0d1a2e" },
  { title: "Interstellar", genres: ["Sci-fi", "Drama"], year: 2014, rating: 8.7, color: "#0a1a0f" },
];
 
const chatHistory = [
  {
    role: "user",
    text: "I loved Parasite and gave Spirited Away a 9 — what should I watch next?",
  },
  {
    role: "bot",
    text: (
      <>
        Based on your ratings, I'd suggest <strong>Oldboy</strong> for the same layered tension as
        Parasite, or <strong>Princess Mononoke</strong> if you want more Miyazaki.
      </>
    ),
  },
];
 
export default function Dashboard() {
  const [message, setMessage] = useState("");
  const [chat, setChat] = useState(chatHistory);
 
  const handleSend = () => {
    if (!message.trim()) return;
    setChat((prev) => [...prev, { role: "user", text: message }]);
    setMessage("");
  };
 
  return (
    <div className="sl-app">
      <main className="sl-main">
        <header className="sl-header">
          <p className="sl-eyebrow">WELCOME BACK</p>
          <h1 className="sl-title">Your movie dashboard</h1>
          <p className="sl-subtitle">Track, rate, and discover films you'll love</p>
        </header>
 
        <section className="sl-stats">
          {[
            { value: "142", label: "Movies watched", accent: false },
            { value: "8.2", label: "Avg rating", accent: true },
            { value: "12", label: "Watchlist", accent: false },
            { value: "Thriller", label: "Top genre", accent: false },
          ].map(({ value, label, accent }) => (
            <div className="sl-stat-card" key={label}>
              <span className={`sl-stat-value${accent ? " sl-stat-accent" : ""}`}>{value}</span>
              <span className="sl-stat-label">{label}</span>
            </div>
          ))}
        </section>
 
        <section className="sl-section">
          <div className="sl-section-header">
            <h2 className="sl-section-title">Recommended for you</h2>
            <button className="sl-see-all">See all</button>
          </div>
          <div className="sl-movies-grid">
            {movies.map((m) => (
              <div className="sl-movie-card" key={m.title}>
                <div className="sl-movie-poster" style={{ backgroundColor: m.color }}>
                  <span className="sl-poster-icon" aria-hidden="true">☐</span>
                </div>
                <div className="sl-movie-info">
                  <p className="sl-movie-title">{m.title}</p>
                  <p className="sl-movie-meta">
                    {m.genres.join(" · ")} · {m.year}
                  </p>
                  <p className="sl-movie-rating">
                    <span className="sl-rating-icon" aria-hidden="true">☰</span> {m.rating.toFixed(1)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="sl-section sl-chat-section">
          <div className="sl-section-header">
            <h2 className="sl-section-title">AI chatbot</h2>
            <button className="sl-see-all">Open full chat</button>
          </div>
          <div className="sl-chat-box">
            <div className="sl-chat-messages">
              {chat.map((msg, i) => (
                <div key={i} className={`sl-chat-bubble sl-chat-${msg.role}`}>
                  {msg.text}
                </div>
              ))}
            </div>
            <div className="sl-chat-input-row">
              <input
                className="sl-chat-input"
                placeholder="Ask for a recommendation..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
              />
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}