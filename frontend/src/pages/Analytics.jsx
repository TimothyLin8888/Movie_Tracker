import { useState, useEffect} from 'react';
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
} from "chart.js";
import "./Analytics.css";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend
);

function StatCard({ title, value }) {
  return (
    <div className="stat-card">
      <p className="stat-title">{title}</p>
      <h2 className="stat-value">{value}</h2>
    </div>
  );
}

export default function Analytics() {
  const [movies, setMovies] = useState([]);
const [loading, setLoading] = useState(true);

useEffect(() => {
    async function fetchMovies() {
        try {
            const response = await fetch("http://localhost:8000/library");

            const data = await response.json();

            setMovies(data);
        } catch (error) {
            console.error(error);
        }

        setLoading(false);
    }

    fetchMovies();
}, []);
  const data = {
    labels: ["2022", "2023", "2024", "2025"],
    datasets: [
      {
        label: "Movies Watched",
        data: [22, 34, 51, 35],
        backgroundColor: "#C0000A",
        borderRadius: 6,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: "#18181b",
        titleColor: "#fff",
        bodyColor: "#fff",
      },
    },
    scales: {
      x: {
        ticks: {
          color: "#d4d4d8",
        },
        grid: {
          display: false,
        },
      },
      y: {
        ticks: {
          color: "#d4d4d8",
        },
        grid: {
          color: "rgba(255,255,255,0.08)",
        },
      },
    },
  };


  const totalRuntime = movies.reduce(
    (sum, movie) => sum + movie.runtime,
    0
);

  const hours = (totalRuntime / 60).toFixed(1);

  const averageRating =
    movies.length > 0
        ? (
              movies.reduce(
                  (sum, movie) => sum + movie.personal_rating,
                  0
              ) / movies.length
          ).toFixed(1)
        : 0;
  return (
    <div className="analytics-page">
      <div className="analytics-container">

        <h1 className="analytics-title">Your Stats</h1>

        <div className="stats-grid">
          <StatCard title="Movies Watched" value={movies.length} />
          <StatCard title="Hours Watched" value={`${hours} h`} />
          <StatCard title="Average Rating" value={`${averageRating} ★`} />
          {/* <StatCard title="Current Streak" value="14 Days" /> */}
        </div>

        <div className="chart-card">
          <h2>Movies Watched Per Year</h2>

          <div className="chart-container">
            <Bar data={data} options={options} />
          </div>
        </div>

      </div>
    </div>
  );
}