import { useEffect, useState, useCallback } from "react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import "./HistoricalInsights.css";

const API_URL = "http://127.0.0.1:8000";

const SEASONS = [
  "Kharif",
  "Rabi",
  "Whole Year",
  "Summer",
  "Winter",
  "Autumn",
];

function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    const data = payload[0];
    return (
      <div className="custom-chart-tooltip">
        <p className="tooltip-label"><strong>{label}</strong></p>
        <p className="tooltip-val">
          {data.name}: <span>{Number(data.value).toLocaleString("en-IN")}</span>
        </p>
      </div>
    );
  }
  return null;
}

export default function HistoricalInsights() {
  const [stateName, setStateName] = useState("Andhra Pradesh");
  const [district, setDistrict] = useState("ANANTAPUR");
  const [season, setSeason] = useState("Kharif");
  const [crop, setCrop] = useState("Groundnut");

  const [ranking, setRanking] = useState(null);
  const [trend, setTrend] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchInsights = useCallback(async (state, dist, seas, crp) => {
    if (!state.trim() || !dist.trim()) return;

    setLoading(true);
    setError("");

    try {
      const rankingParams = new URLSearchParams({
        state: state.trim(),
        district: dist.trim(),
        season: seas,
        limit: "10",
      });

      const trendParams = new URLSearchParams({
        state: state.trim(),
        district: dist.trim(),
        crop: crp.trim(),
        season: seas,
      });

      const [rankRes, trendRes] = await Promise.all([
        fetch(`${API_URL}/historical/ranking?${rankingParams}`),
        fetch(`${API_URL}/historical/trend?${trendParams}`),
      ]);

      if (!rankRes.ok) {
        const err = await rankRes.json().catch(() => ({}));
        throw new Error(err.detail || "Could not retrieve historical crop rankings.");
      }

      if (!trendRes.ok) {
        const err = await trendRes.json().catch(() => ({}));
        throw new Error(err.detail || "Could not retrieve production trend.");
      }

      const rankData = await rankRes.json();
      const trendData = await trendRes.json();

      setRanking(rankData);
      setTrend(trendData);
    } catch (err) {
      setError(err.message || "Failed to load historical analytics.");
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchInsights("Andhra Pradesh", "ANANTAPUR", "Kharif", "Groundnut");
  }, [fetchInsights]);

  function handleFilterSubmit(e) {
    e.preventDefault();
    fetchInsights(stateName, district, season, crop);
  }

  const cropOptions = ranking?.crops || [];

  return (
    <section className="historical-page">
      <header className="historical-heading">
        <span className="section-eyebrow">REGIONAL AGRICULTURAL ANALYTICS (1997–2014)</span>
        <h1>District Historical Insights</h1>
        <p>
          Investigate historical crop production totals, cultivated area, and longitudinal
          trends recorded across Indian districts between 1997 and 2014.
        </p>
      </header>

      {/* Disclaimers & Separation Note */}
      <div className="historical-separation-notice">
        <span className="notice-pill">Methodological Separation</span>
        <p>
          <strong>Historical records are distinct from model predictions:</strong> These figures
          reflect historical agricultural reporting. High past production in a district does not
          prove that your specific field's soil chemistry or microclimate is suitable for that crop.
          Conversely, crops recommended by TabPFN may have low historical volume due to past seed access or market preference.
        </p>
      </div>

      {/* Query Form */}
      <form className="historical-filters-form" onSubmit={handleFilterSubmit}>
        <div className="filter-inputs-grid">
          <label>
            <span>State</span>
            <input
              value={stateName}
              onChange={(e) => setStateName(e.target.value)}
              placeholder="e.g. Andhra Pradesh"
              required
            />
          </label>

          <label>
            <span>District</span>
            <input
              value={district}
              onChange={(e) => setDistrict(e.target.value)}
              placeholder="e.g. ANANTAPUR"
              required
            />
          </label>

          <label>
            <span>Season</span>
            <select
              value={season}
              onChange={(e) => setSeason(e.target.value)}
            >
              {SEASONS.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>

          <label>
            <span>Crop for Trend Analysis</span>
            <input
              value={crop}
              onChange={(e) => setCrop(e.target.value)}
              placeholder="e.g. Groundnut"
              required
            />
          </label>
        </div>

        <button type="submit" className="historical-query-btn" disabled={loading}>
          {loading ? (
            <span className="query-btn-inner">
              <span className="mini-spinner" /> Querying Records...
            </span>
          ) : (
            "Query Regional Records →"
          )}
        </button>
      </form>

      {error && (
        <div className="historical-error-box" role="alert">
          <strong>Query Notice:</strong> {error}
        </div>
      )}

      {/* Ranking and Charts */}
      {ranking && (
        <div className="historical-content-grid">
          <div className="historical-chart-card">
            <div className="card-top-meta">
              <div>
                <h2>Recorded Production Rankings</h2>
                <p>
                  {ranking.district}, {ranking.state} ({ranking.season} season) ·{" "}
                  {ranking.years_covered?.length || 0} years recorded
                </p>
              </div>
            </div>

            {cropOptions.length > 0 ? (
              <div className="chart-container-box">
                <ResponsiveContainer width="100%" height={360}>
                  <BarChart
                    data={cropOptions}
                    margin={{ top: 20, right: 20, left: 20, bottom: 65 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#1d4233" />
                    <XAxis
                      dataKey="Crop"
                      angle={-35}
                      textAnchor="end"
                      interval={0}
                      height={75}
                      tick={{ fill: "#a7c4b4", fontSize: 12 }}
                    />
                    <YAxis tick={{ fill: "#a7c4b4", fontSize: 12 }} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar
                      dataKey="total_production"
                      name="Total Production"
                      fill="#35d07f"
                      radius={[6, 6, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="empty-records-card">
                <p>No historical crop records match this selection.</p>
              </div>
            )}
          </div>

          {/* Longitudinal Trend Chart */}
          {trend && (
            <div className="historical-chart-card">
              <div className="card-top-meta">
                <div>
                  <h2>{trend.crop} Longitudinal Trend</h2>
                  <p>
                    Recorded yearly production for {trend.crop} in {trend.district} ({trend.season})
                  </p>
                </div>
              </div>

              {trend.trend?.length > 0 ? (
                <div className="chart-container-box">
                  <ResponsiveContainer width="100%" height={360}>
                    <LineChart
                      data={trend.trend}
                      margin={{ top: 20, right: 20, left: 20, bottom: 20 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#1d4233" />
                      <XAxis
                        dataKey="year"
                        tick={{ fill: "#a7c4b4", fontSize: 12 }}
                      />
                      <YAxis tick={{ fill: "#a7c4b4", fontSize: 12 }} />
                      <Tooltip content={<CustomTooltip />} />
                      <Line
                        type="monotone"
                        dataKey="total_production"
                        name="Yearly Production"
                        stroke="#38bdf8"
                        strokeWidth={3}
                        dot={{ fill: "#38bdf8", r: 4 }}
                        activeDot={{ r: 6 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="empty-records-card">
                  <p>No yearly production trend records found for {trend.crop}.</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Top Recorded Crops Table */}
      {cropOptions.length > 0 && (
        <div className="historical-table-card">
          <h3>Top Recorded Crops ({ranking.district})</h3>
          <div className="table-responsive-wrapper">
            <table className="historical-data-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Crop</th>
                  <th>Recorded Production</th>
                  <th>Cultivated Area</th>
                  <th>Seasons Recorded</th>
                </tr>
              </thead>
              <tbody>
                {cropOptions.map((item, idx) => (
                  <tr key={item.Crop}>
                    <td><span className="table-rank-pill">#{idx + 1}</span></td>
                    <td><strong>{item.Crop}</strong></td>
                    <td>{Number(item.total_production).toLocaleString("en-IN")}</td>
                    <td>{Number(item.total_area).toLocaleString("en-IN")}</td>
                    <td>{item.years_recorded} seasons</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}
