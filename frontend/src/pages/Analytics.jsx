import { useEffect, useState } from "react";
import { apiRequest } from "../api";
import StatsPanel from "../components/StatsPanel";
import "./Analytics.css";

export default function Analytics() {
  const [lists, setLists] = useState([]);
  const [selectedListId, setSelectedListId] = useState("all");
  const [result, setResult] = useState({ key: null, stats: null, error: "" });

  useEffect(() => {
    apiRequest("/library/lists").then(setLists).catch(() => {});
  }, []);

  useEffect(() => {
    let ignore = false;
    const query = selectedListId === "all" ? "" : `?list_id=${selectedListId}`;
    apiRequest(`/analytics/summary${query}`)
      .then((stats) => { if (!ignore) setResult({ key: selectedListId, stats, error: "" }); })
      .catch((requestError) => { if (!ignore) setResult({ key: selectedListId, stats: null, error: requestError.message }); });
    return () => { ignore = true; };
  }, [selectedListId]);

  const loading = result.key !== selectedListId;
  const { stats, error } = result;

  return (
    <main className="analytics-page">
      <div className="analytics-container">
        <header className="analytics-header">
          <div>
            <p className="analytics-kicker">THE REEL REPORT</p>
            <h1 className="analytics-title">Your viewing story</h1>
            <p className="analytics-intro">A clear read on what you have watched, rated, and returned to.</p>
          </div>
          <div className="analytics-filters">
            <label className="scope-control">
              <span>List</span>
              <select value={selectedListId} onChange={(event) => setSelectedListId(event.target.value)}>
                <option value="all">All watched</option>
                {lists.map((list) => <option value={list.id} key={list.id}>{list.name}</option>)}
              </select>
            </label>
          </div>
        </header>
        {loading && <p className="analytics-message">Gathering your watch history...</p>}
        {error && <p className="analytics-message analytics-error" role="alert">{error}</p>}
        {!loading && !error && stats && <StatsPanel stats={stats} />}
      </div>
    </main>
  );
}
