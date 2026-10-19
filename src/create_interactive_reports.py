
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

metrics = pd.read_csv(DATA / "performance_metrics.csv", index_col=0)
corr = pd.read_csv(DATA / "stock_correlation.csv", index_col=0)

# ---------- 1. Interactive performance table ----------
percent_cols = [
    "Cumulative Return", "CAGR", "Annualized Mean Return",
    "Annualized Volatility", "Maximum Drawdown"
]

display = metrics.copy()
for col in percent_cols:
    display[col] = display[col].map(
        lambda x: f"{x:.2%}" if pd.notna(x) else "N/A"
    )

display["Sharpe Ratio (RF=0)"] = metrics["Sharpe Ratio (RF=0)"].map(
    lambda x: f"{x:.3f}" if pd.notna(x) else "N/A"
)

headers = ["Asset / Portfolio"] + list(display.columns)
cells = [display.index.tolist()] + [
    display[col].tolist() for col in display.columns
]

table = go.Figure(data=[go.Table(
    header=dict(
        values=headers,
        fill_color="#1D4ED8",
        font=dict(color="white", size=12),
        align="center",
        height=38
    ),
    cells=dict(
        values=cells,
        fill_color=[
            ["#EFF6FF" if i % 2 == 0 else "#FFFFFF"
             for i in range(len(display))]
        ] + [
            ["#F8FAFC" if i % 2 == 0 else "#FFFFFF"
             for i in range(len(display))]
            for _ in display.columns
        ],
        font=dict(color="#172033", size=12),
        align=["left"] + ["center"] * len(display.columns),
        height=34
    )
)])

table.update_layout(
    title="Portfolio Performance — Interactive Metrics Table",
    template="plotly_white",
    height=480,
    margin=dict(l=20, r=20, t=70, b=20)
)

table.write_html(
    REPORTS / "performance_metrics_interactive.html",
    include_plotlyjs=True
)

# ---------- 2. Interactive correlation heatmap ----------
heatmap = px.imshow(
    corr,
    text_auto=".3f",
    color_continuous_scale="RdYlBu_r",
    zmin=-1,
    zmax=1,
    aspect="auto",
    title="Stock Correlation Matrix",
    labels=dict(x="Stock", y="Stock", color="Correlation")
)

heatmap.update_traces(
    hovertemplate="Row: %{y}<br>Column: %{x}<br>Correlation: %{z:.3f}<extra></extra>"
)
heatmap.update_layout(
    template="plotly_white",
    height=600
)

heatmap.write_html(
    REPORTS / "correlation_heatmap.html",
    include_plotlyjs=True
)

# ---------- 3. Interactive performance comparison ----------
chart_metrics = [
    ("CAGR", "CAGR", ".1%"),
    ("Annualized Volatility", "Annualized Volatility", ".1%"),
    ("Sharpe Ratio (RF=0)", "Sharpe Ratio (RF=0)", ".3f"),
    ("Maximum Drawdown", "Maximum Drawdown", ".1%")
]

for column, title, hover_format in chart_metrics:
    chart = px.bar(
        metrics.reset_index(names="Asset"),
        x="Asset",
        y=column,
        color=column,
        color_continuous_scale="Teal",
        title=title,
        template="plotly_white",
        hover_data={"Asset": True, column: hover_format}
    )

    chart.update_layout(
        height=520,
        xaxis_title="Asset / Portfolio",
        yaxis_title=title,
        coloraxis_showscale=False
    )

    if column == "Maximum Drawdown":
        chart.update_yaxes(tickformat=".0%")
    elif column in ("CAGR", "Annualized Volatility"):
        chart.update_yaxes(tickformat=".0%")

    filename = column.lower().replace(" ", "_").replace("(", "").replace(")", "")
    chart.write_html(
        REPORTS / f"{filename}.html",
        include_plotlyjs=True
    )

print("Interactive reports created successfully:")
for file in sorted(REPORTS.glob("*.html")):
    print(file)
