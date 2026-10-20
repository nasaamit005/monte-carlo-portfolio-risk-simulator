
from pathlib import Path
import csv
import html
import json
import shutil

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
DOWNLOADS = DOCS / "downloads"
DATA = DOWNLOADS / "data"
REPORTS = DOWNLOADS / "reports"

DATA.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)


def read_csv_rows(path):
    """Read a CSV file into dictionaries; return an empty list if unavailable."""
    if not path.exists() or path.stat().st_size == 0:
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            return list(csv.DictReader(file))
    except (OSError, csv.Error, UnicodeError) as error:
        print(f"Could not read {path}: {error}")
        return []


def number(value):
    """Convert a value to a finite float, or return None."""
    try:
        result = float(value)
        return result if result == result and abs(result) != float("inf") else None
    except (TypeError, ValueError):
        return None


def read_json_safe(value):
    """Serialize data for safe embedding in the generated JavaScript."""
    return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c")


# Copy processed CSV datasets, including any subfolders.
source_data = ROOT / "data" / "processed"
if source_data.exists():
    for file in source_data.rglob("*.csv"):
        target = DATA / file.relative_to(source_data)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, target)
        print("Copied dataset:", file.relative_to(source_data))
else:
    print("Warning: data/processed folder not found.")

# Copy available reports, results, charts, and related files.
for folder_name in ("reports", "outputs", "results"):
    source = ROOT / folder_name
    if source.exists():
        for file in source.rglob("*"):
            if file.is_file() and file.suffix.lower() in {
                ".html", ".csv", ".md", ".json",
                ".png", ".jpg", ".jpeg", ".svg", ".pdf"
            }:
                target = REPORTS / folder_name / file.relative_to(source)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file, target)

# Discover all copied datasets, including nested CSV files.
dataset_files = sorted(
    p for p in DATA.rglob("*.csv") if p.is_file()
)
datasets = [
    {
        "name": p.relative_to(DATA).as_posix(),
        "url": "downloads/data/" + p.relative_to(DATA).as_posix(),
    }
    for p in dataset_files
]

# Discover all copied report and output files.
files = sorted(
    p for p in DOWNLOADS.rglob("*")
    if p.is_file() and p.name != "index.html"
)

file_rows = "\n".join(
    "<tr><td>" + html.escape(p.relative_to(DOWNLOADS).as_posix()) +
    "</td><td><a href=\"downloads/" +
    html.escape(p.relative_to(DOWNLOADS).as_posix(), quote=True) +
    "\">Open / Download</a></td></tr>"
    for p in files
)

# Load actual project results. No hardcoded example metrics.
model_rows = read_csv_rows(
    ROOT / "reports" / "garch_comparison" / "model_comparison.csv"
)
terminal_rows = read_csv_rows(
    ROOT / "reports" / "monte_carlo" / "terminal_values.csv"
)
var_es_rows = read_csv_rows(
    ROOT / "reports" / "monte_carlo" / "simulated_var_es.csv"
)
growth_rows = read_csv_rows(ROOT / "reports" / "growth_of_10000.csv")
correlation_rows = read_csv_rows(
    ROOT / "data" / "processed" / "stock_correlation.csv"
)

# Include model-comparison data as strings/numbers from the source CSV.
# JavaScript converts numeric fields when building charts.
page = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Monte Carlo portfolio risk analysis, GARCH volatility modelling, VaR, Expected Shortfall, and reproducible datasets.">
<title>Monte Carlo Portfolio Risk Simulator</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js"></script>
<style>
:root {
  color-scheme: dark;
  --bg:#0b1020; --panel:#142039; --border:#293954;
  --text:#edf3ff; --muted:#b5c3d9; --accent:#77e0c1;
}
* { box-sizing:border-box; }
html { scroll-behavior:smooth; scroll-padding-top:18px; }
body { margin:0; background:var(--bg); color:var(--text);
  font:16px/1.6 system-ui,-apple-system,Segoe UI,sans-serif; }
header { padding:60px 6%; background:linear-gradient(120deg,#14223b,#174e88,#087e86); }
header .eyebrow { text-transform:uppercase; letter-spacing:.12em;
  font-size:.78rem; font-weight:700; }
h1 { font-size:clamp(2.2rem,5vw,4.2rem); line-height:1.1; margin:.5em 0; }
h1 span,h2 { color:var(--accent); }
header p { max-width:850px; color:#edf3ff; }
a { color:var(--accent); }
nav { position:sticky; top:0; z-index:10; display:flex; flex-wrap:wrap;
  gap:5px; padding:10px 5%; background:#0b1020; border-bottom:1px solid var(--border); }
nav a { position:relative; padding:8px 10px; border-radius:7px;
  color:var(--text); text-decoration:none; font-size:.9rem; }
nav a:hover,nav a:focus-visible { background:#263956; outline:2px solid var(--accent); }
main { max-width:1450px; margin:auto; }
section { padding:32px 5%; border-bottom:1px solid var(--border); }
.cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,270px),1fr)); gap:16px; }
article { min-width:0; padding:18px; background:var(--panel);
  border:1px solid var(--border); border-radius:14px; }
.chart { min-height:320px; width:100%; }
.metric { font-size:clamp(1.35rem,2.5vw,2rem); font-weight:750; overflow-wrap:anywhere; }
.muted,p.note { color:var(--muted); }
.wrap { overflow:auto; max-width:100%; border:1px solid var(--border); border-radius:10px; }
table { width:100%; border-collapse:collapse; font-size:.9rem; }
td,th { text-align:left; vertical-align:top; padding:10px 12px;
  border-bottom:1px solid var(--border); overflow-wrap:anywhere; }
th { background:#1a2b47; position:sticky; top:0; }
button,select,input { max-width:100%; padding:10px; margin:5px 5px 5px 0;
  background:var(--panel); color:var(--text); border:1px solid #496078; border-radius:7px; }
button { cursor:pointer; }
button:hover { border-color:var(--accent); }
footer { padding:25px 5%; color:var(--muted); }
@media(max-width:650px) {
  header { padding:36px 5%; }
  section { padding:25px 4%; }
  nav { position:relative; }
  .chart { min-height:280px; }
}
</style>
</head>
<body>
<header>
  <p class="eyebrow">Quantitative Finance · Risk Analytics</p>
  <h1>Monte Carlo <span>Portfolio Risk Simulator</span></h1>
  <p>Explore simulated portfolio outcomes, compare multivariate-normal and
  GARCH-plus-bootstrap models, inspect tail risk, and download project outputs.</p>
  <p><a href="https://github.com/nasaamit005/monte-carlo-portfolio-risk-simulator">
  View source code on GitHub ↗</a></p>
</header>

<nav aria-label="Main navigation">
  <a href="#overview">Overview</a>
  <a href="#results">Results</a>
  <a href="#charts">Charts</a>
  <a href="#data">Data & tables</a>
  <a href="#reports">Reports</a>
  <a href="#method">Methodology</a>
  <a href="#limits">Limitations</a>
  <a href="#reproduce">Run project</a>
</nav>

<main>
<section id="overview">
  <h2>Project overview</h2>
  <p class="muted">A reproducible portfolio risk analysis using historical equity data,
  Monte Carlo simulation, GARCH(1,1) volatility modelling, and joint residual bootstrap sampling.</p>
  <div class="cards">
    <article><h3>Simulation paths</h3><div class="metric" id="simulationCount">—</div><p class="muted">From model configuration/results</p></article>
    <article><h3>Forecast horizon</h3><div class="metric" id="horizon">—</div><p class="muted">Trading days</p></article>
    <article><h3>Initial portfolio</h3><div class="metric" id="initialValue">—</div><p class="muted">Starting capital in the model output</p></article>
    <article><h3>Assets</h3><div class="metric">5 equities</div><p class="muted">AAPL, AMZN, GOOGL, MSFT, NVDA; S&P 500 as benchmark</p></article>
  </div>
</section>

<section id="results">
  <h2>Results from your model output</h2>
  <p class="note">Metrics below are read from reports/garch_comparison/model_comparison.csv.
  If a value is unavailable, it is shown as unavailable instead of being invented.</p>
  <div class="wrap"><table>
    <thead><tr><th>Metric</th><th>Model</th><th>Value</th></tr></thead>
    <tbody id="metrics"><tr><td colspan="3">Loading model results…</td></tr></tbody>
  </table></div>
</section>

<section id="charts">
  <h2>Interactive charts</h2>
  <div class="cards">
    <article><h3>Terminal value percentiles</h3><div id="terminalChart" class="chart"></div></article>
    <article><h3>Probability of loss</h3><div id="lossChart" class="chart"></div></article>
    <article><h3>VaR and Expected Shortfall</h3><div id="riskChart" class="chart"></div></article>
    <article><h3>Terminal value distribution</h3><div id="distributionChart" class="chart"></div></article>
    <article><h3>Growth of $10,000</h3><div id="growthChart" class="chart"></div></article>
    <article><h3>Asset correlation matrix</h3><div id="correlationChart" class="chart"></div></article>
  </div>
  <p class="note" id="chartStatus" role="status"></p>
</section>

<section id="data">
  <h2>Explore datasets</h2>
  <label for="dataset">Choose a CSV dataset:</label>
  <select id="dataset"></select>
  <button id="loadCsv">Load preview</button>
  <a id="downloadCsv" href="#" download>Download selected CSV</a>
  <p id="csvStatus" class="muted" role="status">Choose a dataset to preview.</p>
  <div class="wrap"><table id="preview"></table></div>
</section>

<section id="reports">
  <h2>Reports, datasets and outputs</h2>
  <p class="muted">Open or download the files generated by the project.</p>
  <div class="wrap"><table><thead><tr><th>File</th><th>Action</th></tr></thead>
  <tbody>__FILE_LINKS__</tbody></table></div>
</section>

<section id="method">
  <h2>Methodology</h2>
  <div class="cards">
    <article><h3>Multivariate-normal Monte Carlo</h3><p>Uses estimated joint return behaviour and covariance to generate correlated simulated returns.</p></article>
    <article><h3>GARCH(1,1) + residual bootstrap</h3><p>Models time-varying volatility and resamples aligned standardized residual vectors.</p></article>
    <article><h3>Out-of-sample validation</h3><p>Compares volatility forecasts against an expanding historical-variance baseline using QLIKE.</p></article>
  </div>
  <p class="muted">See the linked methodology and validation reports for detailed definitions and assumptions.</p>
</section>

<section id="limits">
  <h2>Limitations and interpretation</h2>
  <ul>
    <li>Simulation outputs are model-based scenarios, not predictions or guarantees.</li>
    <li>Results depend on historical data, assumptions, configuration, and random seed.</li>
    <li>VaR and Expected Shortfall must be interpreted with their confidence level, horizon, and loss definition.</li>
    <li>Out-of-sample validation measures historical holdout performance; it does not guarantee future forecast accuracy.</li>
  </ul>
  <p class="muted">Educational analytics only; not investment advice.</p>
</section>

<section id="reproduce">
  <h2>Run the project locally</h2>
  <p>From the project root, activate your virtual environment and install the project requirements.</p>
  <pre><code>pip install -r requirements.txt
python create_dashboard.py
python -m http.server 8000 --directory docs</code></pre>
  <p>Open <a href="http://localhost:8000">http://localhost:8000</a> in your browser.
  The hosted dashboard is a static report; rerun the analysis scripts first to refresh the underlying results.</p>
</section>
</main>

<footer>
  Monte Carlo Portfolio Risk Simulator · <a href="https://github.com/nasaamit005/monte-carlo-portfolio-risk-simulator">GitHub repository</a>
</footer>

<script>
const models = __MODELS__;
const terminalRows = __TERMINAL__;
const varEsRows = __VARES__;
const growthRows = __GROWTH__;
const correlationRows = __CORRELATION__;
const datasets = __DATASETS__;

const layout = {
  paper_bgcolor:"#142039", plot_bgcolor:"#142039",
  font:{color:"#edf3ff"}, margin:{l:60,r:20,t:25,b:70},
  xaxis:{gridcolor:"#293954"}, yaxis:{gridcolor:"#293954"}
};
const config = {responsive:true, displaylogo:false};
const $ = id => document.getElementById(id);
const val = (row,key) => {
  const n = Number(row?.[key]);
  return row && row[key] !== "" && Number.isFinite(n) ? n : null;
};
const money = n => n == null ? "Unavailable" :
  n.toLocaleString("en-US",{style:"currency",currency:"USD",maximumFractionDigits:2});
const pct = n => n == null ? "Unavailable" : n.toFixed(2) + "%";
const clean = s => String(s ?? "").replaceAll("_"," ");

function showEmpty(id, message) {
  $(id).innerHTML = "";
  Plotly.newPlot(id, [], {...layout, annotations:[{
    text:message, x:.5, y:.5, xref:"paper", yref:"paper",
    showarrow:false, font:{color:"#b5c3d9",size:14}
  }]}, config);
}
function plot(id, traces, extra={}) {
  if (!traces.length) {
    showEmpty(id, "No compatible data found in the source files.");
    return;
  }
  Plotly.newPlot(id, traces, {...layout,...extra}, config);
}
function metricRows() {
  const body = $("metrics");
  body.replaceChildren();
  const fields = [
    ["Mean terminal value","Mean_Terminal_Value",money],
    ["Median terminal value","Median_Terminal_Value",money],
    ["5th percentile terminal value","Terminal_Value_P05",money],
    ["95th percentile terminal value","Terminal_Value_P95",money],
    ["Probability of loss","Probability_Of_Loss_Percent",pct],
    ["95% VaR amount","VaR_95_Amount",money],
    ["95% Expected Shortfall amount","ES_95_Amount",money],
    ["99% VaR amount","VaR_99_Amount",money],
    ["99% Expected Shortfall amount","ES_99_Amount",money]
  ];
  if (!models.length) {
    body.innerHTML = '<tr><td colspan="3">Model comparison data unavailable. Check the report file.</td></tr>';
    return;
  }
  for (const model of models) {
    for (const [label,key,format] of fields) {
      const tr = document.createElement("tr");
      for (const text of [label,model.Model || "Unnamed model",format(val(model,key))]) {
        const td = document.createElement("td");
        td.textContent = text;
        tr.appendChild(td);
      }
      body.appendChild(tr);
    }
  }
  const first = models[0];
  $("simulationCount").textContent = first?.Simulation_Count || "Unavailable";
  $("horizon").textContent = first?.Horizon_Days || "Unavailable";
  $("initialValue").textContent = money(val(first,"Initial_Portfolio_Value"));
}
function makeCharts() {
  const names = models.map(m=>m.Model || "Model");
  plot("terminalChart",[
    {type:"bar",name:"5th percentile",x:names,y:models.map(m=>val(m,"Terminal_Value_P05"))},
    {type:"bar",name:"Median",x:names,y:models.map(m=>val(m,"Median_Terminal_Value"))},
    {type:"bar",name:"95th percentile",x:names,y:models.map(m=>val(m,"Terminal_Value_P95"))}
  ],{barmode:"group",yaxis:{title:"Terminal portfolio value",gridcolor:"#293954"}});
  plot("lossChart",[{
    type:"bar",x:names,y:models.map(m=>val(m,"Probability_Of_Loss_Percent")),
    text:models.map(m=>val(m,"Probability_Of_Loss_Percent") == null ? "" : pct(val(m,"Probability_Of_Loss_Percent"))),
    textposition:"outside"
  }],{showlegend:false,yaxis:{title:"Probability of loss (%)",gridcolor:"#293954"}});
  const riskFields = [
    ["95% VaR","VaR_95_Amount"],["95% ES","ES_95_Amount"],
    ["99% VaR","VaR_99_Amount"],["99% ES","ES_99_Amount"]
  ];
  plot("riskChart",models.map(m=>({
    type:"bar",name:m.Model || "Model",
    x:riskFields.map(f=>f[0]),y:riskFields.map(f=>val(m,f[1]))
  })),{barmode:"group",yaxis:{title:"Loss amount ($)",gridcolor:"#293954"}});
  const terminal = terminalRows.map(r=>val(r,"Terminal_Value")).filter(v=>v!==null);
  if (terminal.length) {
    plot("distributionChart",[{
      type:"histogram",x:terminal,nbinsx:45,name:"Terminal values",
      marker:{color:"#77e0c1"}
    }],{xaxis:{title:"Terminal portfolio value",gridcolor:"#293954"},
      yaxis:{title:"Simulation count",gridcolor:"#293954"}});
  } else showEmpty("distributionChart","Terminal values are unavailable.");

  const growthHeaders = Object.keys(growthRows[0] || {}).filter(k=>k!=="Date");
  const growthTraces = growthHeaders.map(name=>({
    type:"scatter",mode:"lines",name,
    x:growthRows.map(r=>r.Date),y:growthRows.map(r=>val(r,name))
  }));
  plot("growthChart",growthTraces,{xaxis:{title:"Date",gridcolor:"#293954"},
    yaxis:{title:"Growth of initial $10,000",gridcolor:"#293954"}});

  const corrNames = correlationRows.map(r=>Object.values(r)[0]).filter(Boolean);
  const corrColumns = Object.keys(correlationRows[0] || {}).slice(1);
  const z = correlationRows.map(r=>corrColumns.map(c=>val(r,c)));
  if (z.length && corrColumns.length) {
    plot("correlationChart",[{
      type:"heatmap",x:corrColumns,y:corrNames,z,
      zmin:-1,zmax:1,colorscale:"RdBu",reversescale:true
    }],{margin:{l:90,r:20,t:25,b:80}});
  } else showEmpty("correlationChart","Correlation matrix unavailable.");

  $("chartStatus").textContent =
    "Charts use the current project CSV files. Missing or invalid fields are shown as unavailable.";
}
function setupDatasets() {
  const select = $("dataset");
  for (const item of datasets) {
    const option = document.createElement("option");
    option.value = item.url;
    option.textContent = item.name;
    select.appendChild(option);
  }
  if (datasets.length) {
    $("downloadCsv").href = datasets[0].url;
    loadCSV();
  } else {
    $("csvStatus").textContent = "No copied CSV datasets were found.";
  }
}
async function loadCSV() {
  const select = $("dataset");
  const path = select.value;
  const status = $("csvStatus");
  const table = $("preview");
  table.replaceChildren();
  if (!path) { status.textContent = "No CSV selected."; return; }
  $("downloadCsv").href = path;
  try {
    const response = await fetch(path);
    if (!response.ok) throw new Error("HTTP " + response.status);
    const text = await response.text();
    const parsed = Papa.parse(text,{skipEmptyLines:true});
    const rows = parsed.data.slice(0,51);
    for (const [i,row] of rows.entries()) {
      const tr = document.createElement("tr");
      for (const value of row) {
        const cell = document.createElement(i===0 ? "th" : "td");
        cell.textContent = value;
        tr.appendChild(cell);
      }
      table.appendChild(tr);
    }
    status.textContent = "Preview: up to 50 data rows. Use Download selected CSV for the full dataset.";
  } catch (error) {
    status.textContent = "Could not load CSV. Check the copied file path and browser network access.";
  }
}
$("loadCsv").addEventListener("click",loadCSV);
$("dataset").addEventListener("change",()=>{
  $("downloadCsv").href=$("dataset").value;
});
metricRows();
makeCharts();
setupDatasets();
</script>
</body>
</html>"""

page = page.replace("__FILE_LINKS__", file_rows)
page = page.replace("__MODELS__", read_json_safe(model_rows))
page = page.replace("__TERMINAL__", read_json_safe(terminal_rows))
page = page.replace("__VARES__", read_json_safe(var_es_rows))
page = page.replace("__GROWTH__", read_json_safe(growth_rows))
page = page.replace("__CORRELATION__", read_json_safe(correlation_rows))
page = page.replace("__DATASETS__", read_json_safe(datasets))

(DOCS / "index.html").write_text(page, encoding="utf-8")

# Create a standalone index of copied output files.
output_links = "\n".join(
    '<li><a href="' +
    html.escape(p.relative_to(DOWNLOADS).as_posix(), quote=True) +
    '">' + html.escape(p.relative_to(DOWNLOADS).as_posix()) + '</a></li>'
    for p in files
)
(DOWNLOADS / "index.html").write_text(
    "<!doctype html><html lang='en'><meta charset='utf-8'>"
    "<meta name='viewport' content='width=device-width,initial-scale=1'>"
    "<title>Project outputs</title><body><h1>Datasets and reports</h1>"
    "<p><a href='../index.html'>Back to dashboard</a></p><ul>" +
    output_links + "</ul></body></html>",
    encoding="utf-8"
)

print("\nDashboard created successfully:")
print(DOCS / "index.html")
print("Datasets found:", len(datasets))
print("Output files indexed:", len(files))
print("Model comparison rows:", len(model_rows))
print("Terminal-value rows:", len(terminal_rows))
print("VaR/ES rows:", len(var_es_rows))
print("Next: python -m http.server 8000 --directory docs")
