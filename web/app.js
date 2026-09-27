const get = (f) => fetch(`data/${f}.json`).then((r) => r.json());
const dark = window.matchMedia("(prefers-color-scheme: dark)").matches;
const layout = (extra) => Object.assign({
  margin: { t: 10, r: 50, b: 40, l: 60 }, paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
  font: { color: dark ? "#e8ebf1" : "#1d2330" }, legend: { orientation: "h", y: -0.15 },
}, extra);
const fmt = (x, d = 1) => (x === null || x === undefined ? "–" : x.toFixed(d));

Promise.all(["status", "pressure", "series", "shocks", "summary", "quality"].map(get)).then(
  ([status, pressure, series, shocks, summary, quality]) => {
    document.getElementById("status").textContent =
      `Data through ${status.last_date} · ${status.varieties} active varieties · updated ${status.updated_utc}`;

    Plotly.newPlot("pressure", [
      { x: pressure.dates, y: pressure.median, name: "Median 4-week change (%)", line: { width: 1.5 } },
      { x: pressure.dates, y: pressure.diffusion, name: "Diffusion: rising − falling >10% (pp)", yaxis: "y2",
        line: { width: 1 }, opacity: 0.7 },
    ], layout({ yaxis: { title: "%" }, yaxis2: { overlaying: "y", side: "right", title: "pp" } }),
    { responsive: true });

    const sel = document.getElementById("variety");
    Object.keys(series).sort().forEach((v) => sel.add(new Option(`${v} (${series[v].category})`, v)));
    const draw = (v) => Plotly.react("series", [{ x: series[v].dates, y: series[v].price, name: v }],
      layout({ yaxis: { title: "S/ per published unit (weekly average)" } }), { responsive: true });
    sel.addEventListener("change", () => draw(sel.value));
    draw(sel.value);

    Plotly.newPlot("shocks", [{ type: "heatmap", x: shocks.weeks, y: shocks.varieties, z: shocks.z,
      zmin: -4, zmax: 4, colorscale: "RdBu", reversescale: true }],
    layout({ margin: { t: 10, r: 20, b: 40, l: 190 }, yaxis: { autorange: "reversed" } }), { responsive: true });

    const cols = [["variety", "Variety"], ["category", "Category"], ["price", "Last price"],
      ["chg28", "4-week %"], ["yoy", "12-month %"], ["vol", "Volatility (28d, %)"]];
    const table = document.getElementById("summary");
    let sortKey = "chg28", asc = false;
    const render = () => {
      const rows = [...summary].sort((a, b) => {
        const x = a[sortKey] ?? -Infinity, y = b[sortKey] ?? -Infinity;
        return (x > y ? 1 : x < y ? -1 : 0) * (asc ? 1 : -1);
      });
      table.innerHTML = `<tr>${cols.map(([k, t]) => `<th data-k="${k}">${t}</th>`).join("")}</tr>` +
        rows.map((r) => `<tr><td>${r.variety}</td><td>${r.category}</td><td>${fmt(r.price, 2)}</td>` +
          `<td>${fmt(r.chg28)}</td><td>${fmt(r.yoy)}</td><td>${fmt(r.vol)}</td></tr>`).join("");
      table.querySelectorAll("th").forEach((th) => th.addEventListener("click", () => {
        asc = th.dataset.k === sortKey ? !asc : false; sortKey = th.dataset.k; render();
      }));
    };
    render();

    const q = quality;
    document.getElementById("quality").innerHTML = [
      `${q.rows_clean.toLocaleString()} clean observations, ${q.start} to ${q.end}; median coverage ${(100 * q.coverage_median).toFixed(0)}%`,
      `Removed: ${q.duplicates} duplicates, ${q.non_positive} non-positive prices, ${q.outliers} outliers (glitches more than ~2× the recent median)`,
      `Stale now (same price ≥30 observations): ${q.stale_now.join(", ") || "none"}`,
      `Discontinued (no data in the last 30 days): ${q.discontinued.join(", ") || "none"}`,
      `Uncategorised varieties: ${q.uncategorised.join(", ") || "none"}`,
    ].map((t) => `<li>${t}</li>`).join("");
  });
