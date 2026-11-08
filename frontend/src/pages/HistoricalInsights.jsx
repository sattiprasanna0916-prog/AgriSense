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
  Label,
} from "recharts";

import "./HistoricalInsights.css";
import API_URL from "../api";

const SEASONS = [
  "Kharif",
  "Rabi",
  "Whole Year",
  "Summer",
  "Winter",
  "Autumn",
];

const formatNumber = (value) =>
  Number(value).toLocaleString("en-IN", {
    maximumFractionDigits: 2,
  });

function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    const data = payload[0];

    return (
      <div className="custom-chart-tooltip">
        <p className="tooltip-label">
          <strong>{label}</strong>
        </p>

        <p className="tooltip-val">
          {data.name}:{" "}
          <span>{formatNumber(data.value)}</span>
        </p>
      </div>
    );
  }

  return null;
}

export default function HistoricalInsights() {
  const [states, setStates] = useState([]);
  const [districts, setDistricts] = useState([]);

  const [stateName, setStateName] = useState("");
  const [district, setDistrict] = useState("");
  const [season, setSeason] = useState("Kharif");
  const [crop, setCrop] = useState("Groundnut");

  const [locationsLoading, setLocationsLoading] = useState(true);
  const [ranking, setRanking] = useState(null);
  const [trend, setTrend] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchInsights = useCallback(
    async (state, dist, seas, crp) => {
      if (!state || !dist || !crp.trim()) return;

      setLoading(true);
      setError("");

      try {
        const rankingParams = new URLSearchParams({
          state,
          district: dist,
          season: seas,
          limit: "10",
        });

        const trendParams = new URLSearchParams({
          state,
          district: dist,
          crop: crp.trim(),
          season: seas,
        });

        const [rankRes, trendRes] = await Promise.all([
          fetch(
            `${API_URL}/historical/ranking?${rankingParams}`
          ),
          fetch(
            `${API_URL}/historical/trend?${trendParams}`
          ),
        ]);

        if (!rankRes.ok) {
          const err = await rankRes.json().catch(() => ({}));
          throw new Error(
            err.detail ||
              "Could not retrieve historical crop rankings."
          );
        }

        if (!trendRes.ok) {
          const err = await trendRes.json().catch(() => ({}));
          throw new Error(
            err.detail || "Could not retrieve production trend."
          );
        }

        const [rankData, trendData] = await Promise.all([
          rankRes.json(),
          trendRes.json(),
        ]);

        setRanking(rankData);
        setTrend(trendData);
      } catch (err) {
        setError(
          err.message || "Failed to load historical analytics."
        );
        setRanking(null);
        setTrend(null);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  // Load available states and default districts.
  useEffect(() => {
    async function loadLocations() {
      setLocationsLoading(true);

      try {
        const response = await fetch(
          `${API_URL}/historical/locations`
        );

        if (!response.ok) {
          throw new Error("Could not load states.");
        }

        const data = await response.json();
        const availableStates = data.states || [];

        setStates(availableStates);

        const defaultState = availableStates.includes(
          "Andhra Pradesh"
        )
          ? "Andhra Pradesh"
          : availableStates[0] || "";

        setStateName(defaultState);

        if (!defaultState) {
          throw new Error("No states are available.");
        }

        const districtResponse = await fetch(
          `${API_URL}/historical/locations?state=${encodeURIComponent(
            defaultState
          )}`
        );

        if (!districtResponse.ok) {
          throw new Error("Could not load districts.");
        }

        const districtData = await districtResponse.json();
        const availableDistricts = districtData.districts || [];

        setDistricts(availableDistricts);

        const defaultDistrict = availableDistricts.includes(
          "ANANTAPUR"
        )
          ? "ANANTAPUR"
          : availableDistricts[0] || "";

        setDistrict(defaultDistrict);

        if (defaultDistrict) {
          await fetchInsights(
            defaultState,
            defaultDistrict,
            "Kharif",
            "Groundnut"
          );
        }
      } catch (err) {
        setError(
          err.message || "Could not load location options."
        );
      } finally {
        setLocationsLoading(false);
      }
    }

    loadLocations();
  }, [fetchInsights]);

  // Load districts when the selected state changes.
  async function handleStateChange(e) {
    const selectedState = e.target.value;

    setStateName(selectedState);
    setDistrict("");
    setDistricts([]);
    setRanking(null);
    setTrend(null);
    setError("");

    if (!selectedState) return;

    try {
      const response = await fetch(
        `${API_URL}/historical/locations?state=${encodeURIComponent(
          selectedState
        )}`
      );

      if (!response.ok) {
        throw new Error("Could not load districts.");
      }

      const data = await response.json();
      setDistricts(data.districts || []);
    } catch (err) {
      setError(err.message || "Could not load districts.");
    }
  }

  function handleFilterSubmit(e) {
    e.preventDefault();

    fetchInsights(stateName, district, season, crop);
  }

  const cropOptions = ranking?.crops || [];
  const trendOptions = trend?.trend || [];

  return (
    <section className="historical-page">
      {/* Page Heading */}
      <header className="historical-heading">
        <span className="section-eyebrow">
          REGIONAL AGRICULTURAL ANALYTICS (1997–2014)
        </span>

        <h1>District Historical Insights</h1>

        <p>
          Investigate historical crop production totals,
          cultivated area, and longitudinal trends recorded
          across Indian districts between 1997 and 2014.
        </p>
      </header>

      {/* Methodological Notice */}
      <div className="historical-separation-notice">
        <span className="notice-pill">
          Methodological Separation
        </span>

        <p>
          <strong>
            Historical records are distinct from model predictions:
          </strong>{" "}
          These figures reflect historical agricultural reporting.
          High past production in a district does not prove that
          your specific field's soil chemistry or microclimate is
          suitable for that crop. Conversely, crops recommended
          by TabPFN may have low historical volume due to past
          seed access or market preference.
        </p>
      </div>

      {/* Filters */}
      <form
        className="historical-filters-form"
        onSubmit={handleFilterSubmit}
      >
        <div className="filter-inputs-grid">
          <label>
            <span>State</span>

            <select
              value={stateName}
              onChange={handleStateChange}
              disabled={locationsLoading}
              required
            >
              <option value="">Select State</option>

              {states.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>

          <label>
            <span>District</span>

            <select
              value={district}
              onChange={(e) => setDistrict(e.target.value)}
              disabled={!districts.length || locationsLoading}
              required
            >
              <option value="">Select District</option>

              {districts.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
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

        <button
          type="submit"
          className="historical-query-btn"
          disabled={
            loading ||
            locationsLoading ||
            !district ||
            !crop.trim()
          }
        >
          {loading ? (
            <span className="query-btn-inner">
              <span className="mini-spinner" />
              Querying Records...
            </span>
          ) : (
            "Query Regional Records →"
          )}
        </button>
      </form>

      {/* Error Message */}
      {error && (
        <div className="historical-error-box" role="alert">
          <strong>Query Notice:</strong> {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="historical-loading">
          Loading historical agricultural records...
        </div>
      )}

      {/* Ranking and Charts */}
      {ranking && (
        <>
          <div className="historical-content-grid">
            {/* Crop Ranking Chart */}
            <div className="historical-chart-card">
              <div className="card-top-meta">
                <div>
                  <h2>Recorded Production Rankings</h2>

                  <p>
                    {ranking.district}, {ranking.state} (
                    {ranking.season} season) ·{" "}
                    {ranking.years_covered?.length || 0} years
                    recorded
                  </p>
                </div>
              </div>

              {cropOptions.length > 0 ? (
                <div className="chart-container-box">
                  <ResponsiveContainer
                    width="100%"
                    height={360}
                  >
                    <BarChart
                      data={cropOptions}
                      margin={{
                        top: 20,
                        right: 20,
                        left: 25,
                        bottom: 75,
                      }}
                    >
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="#e5eee7"
                      />

                      <XAxis
                        dataKey="Crop"
                        angle={-35}
                        textAnchor="end"
                        interval={0}
                        height={85}
                        tick={{
                          fill: "#586e60",
                          fontSize: 11,
                        }}
                        axisLine={{ stroke: "#cbdccf" }}
                        tickLine={{ stroke: "#cbdccf" }}
                      >
                        <Label
                          value="Crop"
                          position="insideBottom"
                          offset={-65}
                          className="chart-axis-label"
                        />
                      </XAxis>

                      <YAxis
  tick={{
    fill: "#586e60",
    fontSize: 11,
  }}
  axisLine={{ stroke: "#cbdccf" }}
  tickLine={{ stroke: "#cbdccf" }}
  tickFormatter={(value) =>
    Number(value).toLocaleString("en-IN")
  }
  label={{
    value: "Recorded Production",
    angle: -90,
    position: "outside",
    offset: 0,
    fill: "#586e60",
    fontSize: 12,
    fontWeight: 600,
    textAnchor: "middle",
  }}
/>

                      <Tooltip
                        content={<CustomTooltip />}
                      />

                      <Bar
                        dataKey="total_production"
                        name="Total Production"
                        fill="#239b62"
                        radius={[6, 6, 0, 0]}
                        maxBarSize={55}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="empty-records-card">
                  <p>
                    No historical crop records match this selection.
                  </p>
                </div>
              )}
            </div>

            {/* Longitudinal Trend Chart */}
            {trend && (
              <div className="historical-chart-card">
                <div className="card-top-meta">
                  <div>
                    <h2>
                      {trend.crop} Longitudinal Trend
                    </h2>

                    <p>
                      Recorded yearly production for{" "}
                      {trend.crop} in {trend.district} (
                      {trend.season})
                    </p>
                  </div>
                </div>

                {trendOptions.length > 0 ? (
                  <div className="chart-container-box">
                    <ResponsiveContainer
                      width="100%"
                      height={360}
                    >
                      <LineChart
                        data={trendOptions}
                        margin={{
                          top: 20,
                          right: 25,
                          left: 45,
                          bottom: 45,
                        }}
                      >
                        <CartesianGrid
                          strokeDasharray="3 3"
                          stroke="#e5eee7"
                        />

                        <XAxis
  dataKey="year"
  tick={false}
  axisLine={{ stroke: "#cbdccf" }}
  tickLine={false}
/>

                        <YAxis
  tick={{
    fill: "#586e60",
    fontSize: 11,
  }}
  axisLine={{ stroke: "#cbdccf" }}
  tickLine={{ stroke: "#cbdccf" }}
  tickFormatter={(value) =>
    Number(value).toLocaleString("en-IN")
  }
  label={{
    value: "Recorded Production",
    angle: -90,
    position: "outside",
    offset: 0,
    fill: "#586e60",
    fontSize: 12,
    fontWeight: 600,
    textAnchor: "middle",
  }}
/>
                        <Tooltip
                          content={<CustomTooltip />}
                        />

                        <Line
                          type="monotone"
                          dataKey="total_production"
                          name="Yearly Production"
                          stroke="#239b62"
                          strokeWidth={3}
                          dot={{
                            fill: "#239b62",
                            stroke: "#ffffff",
                            strokeWidth: 2,
                            r: 4,
                          }}
                          activeDot={{
                            r: 7,
                            fill: "#187d4c",
                          }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="empty-records-card">
                    <p>
                      No yearly production trend records found
                      for {trend.crop}.
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Top Recorded Crops Table */}
          {cropOptions.length > 0 && (
            <div className="historical-table-card">
              <h3>
                Top Recorded Crops ({ranking.district})
              </h3>

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
                        <td>
                          <span className="table-rank-pill">
                            #{idx + 1}
                          </span>
                        </td>

                        <td>
                          <strong>{item.Crop}</strong>
                        </td>

                        <td>
                          {formatNumber(item.total_production)}
                        </td>

                        <td>
                          {formatNumber(item.total_area)}
                        </td>

                        <td>
                          {item.years_recorded} seasons
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </section>
  );
}