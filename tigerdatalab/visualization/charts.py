"""Chart engine: automatically selects and builds an appropriate set of
Plotly charts from the dataset + detected semantics, each with explicit
title/x-axis/y-axis/metric/aggregation metadata (explainability)."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from ..quality.types import numeric_columns, categorical_columns, detect_all_dtypes


def _empty_chart(title: str, reason: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=reason, x=0.5, y=0.5, xref="paper", yref="paper",
        showarrow=False, font=dict(size=16, color="#888"),
    )
    fig.update_layout(title=title, xaxis_visible=False, yaxis_visible=False,
                       template="plotly_white", height=380)
    return fig


class ChartSpec:
    def __init__(self, key: str, title: str, fig: go.Figure, x_axis: str = "",
                 y_axis: str = "", metric: str = "", aggregation: str = "",
                 dimension: str = "", note: str = ""):
        self.key = key
        self.title = title
        self.fig = fig
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.metric = metric
        self.aggregation = aggregation
        self.dimension = dimension
        self.note = note

    def to_meta(self) -> dict:
        return {
            "key": self.key, "title": self.title, "x_axis": self.x_axis,
            "y_axis": self.y_axis, "metric": self.metric,
            "aggregation": self.aggregation, "dimension": self.dimension,
            "note": self.note,
        }


def build_kpi_card_chart(kpis: dict) -> ChartSpec:
    """A Plotly 'indicator' grid rendering the headline KPIs as cards —
    the 12th required chart type (KPI Cards) alongside the HTML KPI grid
    already shown at the top of the dashboard."""
    labels_order = [
        ("total_revenue", "Revenue", "₹"),
        ("total_profit", "Profit", "₹"),
        ("profit_margin_pct", "Profit Margin", ""),
        ("orders", "Orders", ""),
        ("customers", "Customers", ""),
        ("total_quantity", "Quantity", ""),
    ]
    present = [(k, label, prefix) for k, label, prefix in labels_order if k in kpis]
    if not present:
        return ChartSpec("kpi_cards", "KPI Cards", _empty_chart("KPI Cards", "Not enough data for this visualization."))

    n = len(present)
    fig = go.Figure()
    for i, (key, label, prefix) in enumerate(present):
        value = kpis[key]
        suffix = "%" if key == "profit_margin_pct" else ""
        fig.add_trace(go.Indicator(
            mode="number", value=value,
            number={"prefix": prefix, "suffix": suffix, "valueformat": ",.2f" if isinstance(value, float) else ",d"},
            title={"text": label},
            domain={"row": 0, "column": i},
        ))
    fig.update_layout(
        grid={"rows": 1, "columns": n, "pattern": "independent"},
        template="plotly_white", height=180,
    )
    return ChartSpec("kpi_cards", "KPI Cards", fig, metric="Multiple KPIs", aggregation="SUM/COUNT")


def build_charts(df: pd.DataFrame, semantics: dict, trend: dict | None,
                  category_analysis: dict | None, kpis: dict | None = None) -> list[ChartSpec]:
    charts: list[ChartSpec] = []
    dtypes = detect_all_dtypes(df)
    revenue_col = semantics.get("revenue")
    profit_col = semantics.get("profit")
    category_col = semantics.get("category")
    product_col = semantics.get("product")

    if kpis:
        charts.append(build_kpi_card_chart(kpis))

    # 1. Performance Trend (line + rolling average)
    if trend:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=trend["periods"], y=trend["values"], mode="lines+markers",
                                  name=trend["metric_label"], line=dict(color="#2563eb", width=3)))
        fig.add_trace(go.Scatter(x=trend["periods"], y=trend["rolling_average"], mode="lines",
                                  name="Rolling Avg (3)", line=dict(color="#f59e0b", dash="dash")))
        fig.update_layout(title=trend["title"], xaxis_title=trend["date_column"],
                           yaxis_title=trend["metric_label"], template="plotly_white", height=420)
        charts.append(ChartSpec("performance_trend", trend["title"], fig,
                                 x_axis=trend["date_column"], y_axis=trend["metric_label"],
                                 metric=trend["metric_label"], aggregation="SUM",
                                 dimension=trend["date_column"]))
    else:
        fig = _empty_chart("Performance Trend", "Not enough data for this visualization.")
        charts.append(ChartSpec("performance_trend", "Performance Trend", fig, note="No valid date+numeric pair found."))

    # 2. Revenue by Category — bar, pie, donut
    if category_analysis and category_analysis.get("available") and category_analysis.get("revenue_by_category"):
        rows = category_analysis["revenue_by_category"]
        cats = [r["category"] for r in rows]
        vals = [r["revenue"] for r in rows]

        fig_col = go.Figure(go.Bar(x=cats, y=vals, marker_color="#2563eb"))
        # Dropdown filter: view all categories, or isolate a single one.
        buttons = [dict(label="All Categories",
                         method="update",
                         args=[{"x": [cats], "y": [vals]},
                               {"title": "Revenue by Category (Column)"}])]
        for c, v in zip(cats, vals):
            buttons.append(dict(label=c, method="update",
                                 args=[{"x": [[c]], "y": [[v]]},
                                       {"title": f"Revenue by Category (Column) — {c}"}]))
        fig_col.update_layout(
            title="Revenue by Category (Column)", xaxis_title=category_col,
            yaxis_title="Total Revenue", template="plotly_white", height=420,
            updatemenus=[dict(buttons=buttons, direction="down", x=1.0, xanchor="right",
                               y=1.15, yanchor="top", showactive=True)],
        )
        charts.append(ChartSpec("revenue_by_category_column", "Revenue by Category", fig_col,
                                 x_axis=category_col, y_axis="Total Revenue", metric="Revenue",
                                 aggregation="SUM", dimension=category_col,
                                 note="Includes a category dropdown filter."))

        fig_bar = go.Figure(go.Bar(x=vals, y=cats, orientation="h", marker_color="#16a34a"))
        fig_bar.update_layout(title="Revenue by Category (Bar)", xaxis_title="Total Revenue",
                               yaxis_title=category_col, template="plotly_white", height=420)
        charts.append(ChartSpec("revenue_by_category_bar", "Revenue by Category", fig_bar,
                                 x_axis="Total Revenue", y_axis=category_col, metric="Revenue",
                                 aggregation="SUM", dimension=category_col))

        fig_pie = go.Figure(go.Pie(labels=cats, values=vals, hole=0))
        fig_pie.update_layout(title="Revenue Share by Category (Pie)", template="plotly_white", height=420)
        charts.append(ChartSpec("category_pie", "Revenue Share by Category", fig_pie,
                                 metric="Revenue", aggregation="SUM", dimension=category_col))

        fig_donut = go.Figure(go.Pie(labels=cats, values=vals, hole=0.55))
        fig_donut.update_layout(title="Revenue Share by Category (Donut)", template="plotly_white", height=420)
        charts.append(ChartSpec("category_donut", "Revenue Share by Category", fig_donut,
                                 metric="Revenue", aggregation="SUM", dimension=category_col))

        # Pareto: revenue by category, sorted desc, with cumulative % line
        sorted_rows = sorted(rows, key=lambda r: r["revenue"], reverse=True)
        cats_s = [r["category"] for r in sorted_rows]
        vals_s = [r["revenue"] for r in sorted_rows]
        total = sum(vals_s) or 1
        cum = []
        running = 0
        for v in vals_s:
            running += v
            cum.append(100 * running / total)
        fig_pareto = go.Figure()
        fig_pareto.add_trace(go.Bar(x=cats_s, y=vals_s, name="Revenue", marker_color="#2563eb"))
        fig_pareto.add_trace(go.Scatter(x=cats_s, y=cum, name="Cumulative %", yaxis="y2",
                                         line=dict(color="#dc2626")))
        fig_pareto.update_layout(
            title="Revenue Pareto by Category", xaxis_title=category_col, yaxis_title="Total Revenue",
            yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 110]),
            template="plotly_white", height=420,
        )
        charts.append(ChartSpec("pareto_category", "Revenue Pareto by Category", fig_pareto,
                                 x_axis=category_col, y_axis="Total Revenue / Cumulative %",
                                 metric="Revenue", aggregation="SUM", dimension=category_col))
    else:
        for key, title in [("revenue_by_category_column", "Revenue by Category"),
                            ("category_pie", "Revenue Share by Category"),
                            ("category_donut", "Revenue Share by Category"),
                            ("pareto_category", "Revenue Pareto by Category")]:
            charts.append(ChartSpec(key, title, _empty_chart(title, "Not enough data for this visualization.")))

    # 3. Top products bar
    if product_col and revenue_col and product_col in df.columns and revenue_col in df.columns:
        top = (df.groupby(product_col)[revenue_col]
               .apply(lambda s: pd.to_numeric(s, errors="coerce").sum())
               .sort_values(ascending=False).head(10))
        fig = go.Figure(go.Bar(x=top.values, y=[str(i) for i in top.index], orientation="h",
                                marker_color="#7c3aed"))
        fig.update_layout(title="Top 10 Products by Revenue", xaxis_title="Total Revenue",
                           yaxis_title=product_col, template="plotly_white", height=420,
                           yaxis=dict(autorange="reversed"))
        charts.append(ChartSpec("product_bar", "Top 10 Products by Revenue", fig,
                                 x_axis="Total Revenue", y_axis=product_col, metric="Revenue",
                                 aggregation="SUM", dimension=product_col))
    else:
        charts.append(ChartSpec("product_bar", "Top Products by Revenue",
                                 _empty_chart("Top Products by Revenue", "Not enough data for this visualization.")))

    # 4. Revenue distribution (histogram)
    if revenue_col and revenue_col in df.columns:
        vals = pd.to_numeric(df[revenue_col], errors="coerce").dropna()
        fig = go.Figure(go.Histogram(x=vals, marker_color="#0891b2", nbinsx=30))
        fig.update_layout(title="Revenue Distribution", xaxis_title=revenue_col,
                           yaxis_title="Frequency", template="plotly_white", height=380)
        charts.append(ChartSpec("revenue_distribution", "Revenue Distribution", fig,
                                 x_axis=revenue_col, y_axis="Frequency", metric=revenue_col,
                                 aggregation="COUNT", dimension=revenue_col))

        fig_box = go.Figure(go.Box(y=vals, name=revenue_col, marker_color="#0891b2"))
        fig_box.update_layout(title="Revenue Box Plot", yaxis_title=revenue_col,
                               template="plotly_white", height=380)
        charts.append(ChartSpec("boxplot", "Revenue Box Plot", fig_box,
                                 y_axis=revenue_col, metric=revenue_col, aggregation="DISTRIBUTION"))
    else:
        charts.append(ChartSpec("revenue_distribution", "Revenue Distribution",
                                 _empty_chart("Revenue Distribution", "Not enough data for this visualization.")))
        charts.append(ChartSpec("boxplot", "Box Plot",
                                 _empty_chart("Box Plot", "Not enough data for this visualization.")))

    # 5. Revenue vs Profit scatter
    if revenue_col and profit_col and revenue_col in df.columns and profit_col in df.columns:
        x = pd.to_numeric(df[revenue_col], errors="coerce")
        y = pd.to_numeric(df[profit_col], errors="coerce")
        fig = go.Figure(go.Scatter(x=x, y=y, mode="markers", marker=dict(color="#ea580c", size=6, opacity=0.6)))
        fig.update_layout(title="Revenue vs Profit", xaxis_title=revenue_col, yaxis_title=profit_col,
                           template="plotly_white", height=420)
        charts.append(ChartSpec("revenue_vs_profit", "Revenue vs Profit", fig,
                                 x_axis=revenue_col, y_axis=profit_col, metric="Revenue vs Profit",
                                 aggregation="RAW"))
    else:
        charts.append(ChartSpec("revenue_vs_profit", "Revenue vs Profit",
                                 _empty_chart("Revenue vs Profit", "Not enough data for this visualization.")))

    # 6. Correlation heatmap across numeric columns
    numeric_cols = numeric_columns(df, dtypes)
    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].apply(pd.to_numeric, errors="coerce").corr()
        fig = go.Figure(go.Heatmap(z=corr.values, x=corr.columns.tolist(), y=corr.columns.tolist(),
                                    colorscale="RdBu", zmid=0))
        fig.update_layout(title="Correlation Heatmap", template="plotly_white", height=450)
        charts.append(ChartSpec("correlation_heatmap", "Correlation Heatmap", fig,
                                 metric="Correlation", aggregation="PEARSON"))
    else:
        charts.append(ChartSpec("correlation_heatmap", "Correlation Heatmap",
                                 _empty_chart("Correlation Heatmap", "Not enough numeric columns for this visualization.")))

    return charts
