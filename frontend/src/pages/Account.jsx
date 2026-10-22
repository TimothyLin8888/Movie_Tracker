import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { API_URL, apiRequest } from "../api";
import "./Account.css";

const streamingServices = [
  { id: "netflix", name: "Netflix", mark: "N" },
  { id: "disney-plus", name: "Disney+", mark: "D+" },
  { id: "max", name: "Max", mark: "M" },
  { id: "prime-video", name: "Prime Video", mark: "P" },
  { id: "apple-tv", name: "Apple TV+", mark: "A" },
  { id: "hulu", name: "Hulu", mark: "H" },
  { id: "paramount-plus", name: "Paramount+", mark: "P+" },
  { id: "peacock", name: "Peacock", mark: "P" },
];

function Account() {
  const storedUser = JSON.parse(localStorage.getItem("movie_tracker_user") || "null");
  const savedPreferences = JSON.parse(localStorage.getItem("movie_tracker_preferences") || "null");
  const [form, setForm] = useState({
    username: storedUser?.username || "",
    email: storedUser?.email || "",
  });
  const [preferences, setPreferences] = useState({
    weeklyDigest: savedPreferences?.weeklyDigest ?? true,
    defaultView: savedPreferences?.defaultView || "recent",
    streamingServices: savedPreferences?.streamingServices || [],
  });
  const [sharing, setSharing] = useState({ bio: "", is_public: false, show_lists: true });
  const [sharedUsername, setSharedUsername] = useState(storedUser?.username || "");
  const [copied, setCopied] = useState(false);
  const [status, setStatus] = useState({ type: "", message: "" });
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    apiRequest("/profile/me")
      .then((data) => {
        setSharing({ bio: data.bio || "", is_public: data.is_public, show_lists: data.show_lists });
        setSharedUsername(data.username);
      })
      .catch(() => {});
  }, []);

  const shareUrl = `${window.location.origin}/u/${sharedUsername}`;

  const copyShareUrl = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setStatus({ type: "error", message: "Couldn't copy automatically. Select the link and copy it." });
    }
  };

  const handleProfileChange = (event) => {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
    setStatus({ type: "", message: "" });
  };

  const toggleStreamingService = (serviceId) => {
    setPreferences((current) => ({
      ...current,
      streamingServices: current.streamingServices.includes(serviceId)
        ? current.streamingServices.filter((id) => id !== serviceId)
        : [...current.streamingServices, serviceId],
    }));
  };

  const handleSave = async (event) => {
    event.preventDefault();
    setIsSaving(true);
    setStatus({ type: "", message: "" });

    try {
      const token = localStorage.getItem("movie_tracker_token");
      const response = await fetch(`${API_URL}/auth/me`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(form),
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to save your profile");
      }

      localStorage.setItem("movie_tracker_user", JSON.stringify(data));
      localStorage.setItem("movie_tracker_preferences", JSON.stringify(preferences));
      const savedSharing = await apiRequest("/profile/me", { method: "PATCH", body: sharing });
      setSharedUsername(savedSharing.username);
      setStatus({ type: "success", message: "Your settings are saved." });
    } catch (saveError) {
      setStatus({ type: "error", message: saveError.message });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <main className="account-page">
      <div className="account-container">
        <header className="account-header">
          <div>
            <p className="account-kicker">YOUR PROFILE</p>
            <h1>Account settings</h1>
            <p>Shape how Name feels every time you come back to your collection.</p>
          </div>
          <Link className="account-back" to="/">Back to dashboard</Link>
        </header>

        <form className="account-settings" onSubmit={handleSave}>
          <section className="account-section" aria-labelledby="profile-heading">
            <div className="account-section-heading">
              <h2 id="profile-heading">Profile</h2>
              <p>This information appears in your profile menu.</p>
            </div>
            <div className="account-fields">
              <label>
                Display name
                <input name="username" value={form.username} onChange={handleProfileChange} minLength="3" required />
              </label>
              <label>
                Email address
                <input name="email" type="email" value={form.email} onChange={handleProfileChange} required />
              </label>
            </div>
          </section>

          <section className="account-section" aria-labelledby="sharing-heading">
            <div className="account-section-heading">
              <h2 id="sharing-heading">Share your profile</h2>
              <p>A public page with your stats, watch schedule, recent ratings and favorites. Private until you turn it on.</p>
            </div>
            <label className="account-toggle">
              <span><strong>Public profile</strong><small>Anyone with the link can view it. Your email is never shown.</small></span>
              <input type="checkbox" checked={sharing.is_public} onChange={(event) => setSharing({ ...sharing, is_public: event.target.checked })} />
            </label>
            <label className="account-toggle">
              <span><strong>Show my movie lists</strong><small>Only list names and film counts appear, never the films inside.</small></span>
              <input type="checkbox" checked={sharing.show_lists} onChange={(event) => setSharing({ ...sharing, show_lists: event.target.checked })} />
            </label>
            <label className="account-bio">
              Bio
              <textarea rows="3" maxLength="280" value={sharing.bio} placeholder="A line about your taste in movies" onChange={(event) => setSharing({ ...sharing, bio: event.target.value })} />
            </label>
            <div className="account-share">
              <input readOnly value={shareUrl} aria-label="Your profile link" onFocus={(event) => event.target.select()} />
              <button type="button" onClick={copyShareUrl} disabled={!sharing.is_public}>{copied ? "Copied" : "Copy link"}</button>
            </div>
            {!sharing.is_public && <p className="account-share-hint">Turn on Public profile and save to start sharing this link.</p>}
          </section>

          <section className="account-section" aria-labelledby="preferences-heading">
            <div className="account-section-heading">
              <h2 id="preferences-heading">Preferences</h2>
              <p>These choices are remembered on this device.</p>
            </div>
            <label className="account-toggle">
              <span><strong>Weekly digest</strong><small>Get a weekly reminder of what is waiting in your lists.</small></span>
              <input type="checkbox" checked={preferences.weeklyDigest} onChange={(event) => setPreferences({ ...preferences, weeklyDigest: event.target.checked })} />
            </label>
            <label className="account-select">
              Default dashboard view
              <select value={preferences.defaultView} onChange={(event) => setPreferences({ ...preferences, defaultView: event.target.value })}>
                <option value="recent">Recently watched</option>
                <option value="favorites">Favorite movies</option>
                <option value="watchlist">My watchlist</option>
              </select>
            </label>
            <div className="account-services">
              <div className="account-services-heading">
                <strong>Streaming services</strong>
                <small>Choose the services you currently use or have access to.</small>
              </div>
              <div className="account-service-grid" aria-label="Streaming services">
                {streamingServices.map((service) => {
                  const isSelected = preferences.streamingServices.includes(service.id);
                  return (
                    <button
                      className={`account-service${isSelected ? " selected" : ""}`}
                      type="button"
                      key={service.id}
                      aria-pressed={isSelected}
                      onClick={() => toggleStreamingService(service.id)}
                    >
                      <span className={`account-service-mark service-${service.id}`} aria-hidden="true">{service.mark}</span>
                      <span>{service.name}</span>
                      <span className="account-service-check" aria-hidden="true">{isSelected ? "✓" : ""}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          </section>

          <div className="account-actions">
            {status.message && <p className={`account-status ${status.type}`} role={status.type === "error" ? "alert" : "status"}>{status.message}</p>}
            <button className="account-save" type="submit" disabled={isSaving}>{isSaving ? "Saving..." : "Save settings"}</button>
          </div>
        </form>
      </div>
    </main>
  );
}

export default Account;
