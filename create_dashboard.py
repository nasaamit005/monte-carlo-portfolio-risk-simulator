
from pathlib import Path
import shutil
import html
import json

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
DOWNLOADS = DOCS / "downloads"
DATA = DOWNLOADS / "data"
REPORTS = DOWNLOADS / "reports"

DATA.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

# Copy processed datasets
source_data = ROOT / "data" / "processed"

if source_data.exists():
    for file in source_data.rglob("*.csv"):
        target = DATA / file.relative_to(source_data)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, target)
        print("Copied dataset:", file.name)
else:
    print("No data/processed folder found.")

# Copy existing analysis reports
for folder_name in ("reports", "outputs", "results"):
    source = ROOT / folder_name
    if source.exists():
        for file in source.rglob("*"):
            if file.is_file() and file.suffix.lower() in {
                ".html", ".csv", ".md", ".json",
                ".png", ".jpg", ".jpeg", ".svg"
            }:
                target = REPORTS / folder_name / file.relative_to(source)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file, target)
                print("Copied report:", file.name)

# Build the output file list
files = sorted(
    p for p in DOWNLOADS.rglob("*")
    if p.is_file() and p.name != "index.html"
)

links = "\n".join(
    '<tr><td>' +
    html.escape(p.relative_to(DOWNLOADS).as_posix()) +
    '</td><td><a href="downloads/' +
    html.escape(p.relative_to(DOWNLOADS).as_posix(), quote=True) +
    '">Open / Download</a></td></tr>'
    for p in files
)

# Discover datasets
datasets = sorted(p.name for p in DATA.glob("*.csv"))

# Create dashboard website
page = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Monte Carlo Portfolio Risk Dashboard</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
body{margin:0;background:#0b1020;color:#edf3ff;
font:16px/1.6 system-ui}
header,section{padding:30px 5%;border-bottom:1px solid #293954}
header{background:#14223b}
h1{font-size:clamp(30px,5vw,55px);line-height:1.1}
h1 span,h2{color:#77e0c1}
a{color:#77e0c1}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}
article{background:#142039;border:1px solid #293954;
border-radius:12px;padding:16px;min-width:0}
.chart{height:320px}
.wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse}
td,th{text-align:left;padding:12px;border-bottom:1px solid #293954}
select,button{padding:10px;margin:5px;background:#142039;
color:white;border:1px solid #496078;border-radius:6px}
p{color:#b5c3d9}
</style>
</head>
<body>
<header>
<p>QUANTITATIVE FINANCE · ANALYSIS DASHBOARD</p>
<h1>Monte Carlo Portfolio<br><span>Risk Simulator</span></h1>
<p>Interactive charts, risk comparisons, datasets and generated reports.</p>
<a href="https://github.com/nasaamit005/monte-carlo-portfolio-risk-simulator">
View GitHub repository</a>
</header>

<section>
<h2>Interactive charts</h2>
<p>Example figures are shown here. Replace them with verified results
from your latest simulation before publishing.</p>
<div class="cards">
<article><h3>Terminal portfolio values</h3><div id="terminal" class="chart"></div></article>
<article><h3>Probability of loss</h3><div id="loss" class="chart"></div></article>
<article><h3>Tail-risk comparison</h3><div id="risk" class="chart"></div></article>
</div>
</section>

<section>
<h2>Model comparison</h2>
<div class="wrap"><table>
<thead><tr><th>Metric</th><th>Normal model</th>
<th>GARCH + Bootstrap</th></tr></thead>
<tbody id="metrics"></tbody></table></div>
</section>

<section>
<h2>Explore CSV datasets</h2>
<select id="dataset"></select>
<button onclick="loadCSV()">Load preview</button>
<a id="download" href="#">Download selected CSV</a>
<p id="status">Choose a dataset.</p>
<div class="wrap"><table id="preview"></table></div>
</section>

<section>
<h2>Reports, datasets and outputs</h2>
<div class="wrap"><table>
<thead><tr><th>File</th><th>Action</th></tr></thead>
<tbody>__FILE_LINKS__</tbody>
</table></div>
</section>

<script>
const layout={
 paper_bgcolor:"#142039",plot_bgcolor:"#142039",
 font:{color:"#edf3ff"},
 margin:{l:55,r:15,t:20,b:65}
};
const config={responsive:true,displaylogo:false};
const models=["Normal","GARCH + Bootstrap"];

Plotly.newPlot("terminal",[
 {x:models,y:[8544.50,8854.19],name:"5th percentile",type:"bar"},
 {x:models,y:[13628.99,13871.93],name:"Median",type:"bar"},
 {x:models,y:[21777.04,21254.57],name:"95th percentile",type:"bar"}
],{...layout,barmode:"group"},config);

Plotly.newPlot("loss",[
 {x:models,y:[13.97,11.05],type:"bar",
  text:["13.97%","11.05%"],textposition:"outside"}
],{...layout,showlegend:false},config);

Plotly.newPlot("risk",[
 {x:["95% VaR","95% ES","99% VaR","99% ES"],
  y:[1455.50,2345.24,2984.64,3517.86],
  name:"Normal",type:"bar"},
 {x:["95% VaR","95% ES","99% VaR","99% ES"],
  y:[1145.81,2226.71,2924.60,3746.47],
  name:"GARCH + Bootstrap",type:"bar"}
],{...layout,barmode:"group"},config);

const metrics=[
 ["Mean terminal value","$14,210.08","$14,571.12"],
 ["Median terminal value","$13,628.99","$13,871.93"],
 ["5th percentile","$8,544.50","$8,854.19"],
 ["95th percentile","$21,777.04","$21,254.57"],
 ["Probability of loss","13.97%","11.05%"],
 ["95% VaR","$1,455.50","$1,145.81"],
 ["95% ES","$2,345.24","$2,226.71"],
 ["99% VaR","$2,984.64","$2,924.60"],
 ["99% ES","$3,517.86","$3,746.47"]
];

document.getElementById("metrics").innerHTML=metrics.map(row=>
 "<tr>"+row.map(v=>"<td>"+v+"</td>").join("")+"</tr>"
).join("");

const datasets=__DATASETS__;
const selector=document.getElementById("dataset");

datasets.forEach(name=>{
 const option=document.createElement("option");
 option.value=name;
 option.textContent=name;
 selector.appendChild(option);
});

selector.addEventListener("change",()=>{
 document.getElementById("download").href="downloads/data/"+
 encodeURIComponent(selector.value);
});

async function loadCSV(){
 const name=selector.value;
 const status=document.getElementById("status");
 const table=document.getElementById("preview");

 if(!name){status.textContent="No CSV files found.";return;}

 const path="downloads/data/"+encodeURIComponent(name);
 document.getElementById("download").href=path;

 try{
  const response=await fetch(path);
  if(!response.ok)throw Error("CSV unavailable");
  const text=await response.text();
  const rows=text.trim().split(/\r?\n/).slice(0,51);
  table.replaceChildren();

  rows.forEach((line,index)=>{
   const tr=document.createElement("tr");
   line.split(",").forEach(value=>{
    const cell=document.createElement(index===0?"th":"td");
    cell.textContent=value;
    tr.appendChild(cell);
   });
   table.appendChild(tr);
  });

  status.textContent="Preview shows up to 50 rows. Download CSV for full data.";
 }catch(error){
  status.textContent="CSV not found. Rebuild the dashboard and check the data folder.";
 }
}
</script>
</body>
</html>"""

page = page.replace("__FILE_LINKS__", links)
page = page.replace("__DATASETS__", json.dumps(datasets))

(DOCS / "index.html").write_text(page, encoding="utf-8")

# Create an index of all copied output files
output_links = "\n".join(
    '<li><a href="' +
    html.escape(p.relative_to(DOWNLOADS).as_posix(), quote=True) +
    '">' + html.escape(p.relative_to(DOWNLOADS).as_posix()) +
    '</a></li>'
    for p in files
)

(DOWNLOADS / "index.html").write_text(
    "<!doctype html><html><meta charset='utf-8'><title>Project outputs</title>"
    "<body><h1>Datasets and reports</h1>"
    "<p><a href='../index.html'>Back to dashboard</a></p><ul>" +
    output_links + "</ul></body></html>",
    encoding="utf-8"
)

print("\nDashboard created successfully:")
print(DOCS / "index.html")
print("Datasets found:", len(datasets))
print("Output files indexed:", len(files))
print("Next: python -m http.server 8000 --directory docs")
