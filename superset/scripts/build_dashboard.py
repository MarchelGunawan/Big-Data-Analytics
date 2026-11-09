"""Build the Chapter VII dashboard in a running Superset through its REST API.

Run it after `docker compose up -d --build`:

    python3 scripts/build_dashboard.py

It creates the database connection, datasets, charts and dashboard, then
saves an export to exports/dashboard_export.zip. Standard library only.
"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE_URL = "http://localhost:8088"
USERNAME = "admin"
PASSWORD = "admin"

DB_NAME = "BDA Final Project"
DB_URI = "postgresql+psycopg2://superset:superset@postgres:5432/bda"
DASHBOARD_TITLE = "Fraud Detection and Personalization Dashboard"
DASHBOARD_SLUG = "bda-final-project"
CHART_PREFIX = "[BDA] "

EXPORT_PATH = Path(__file__).resolve().parent.parent / "exports" / "dashboard_export.zip"

TABLES = [
    "kpis", "event_funnel", "session_segments", "flag_groups", "reco_quality",
    "reco_ndcg_by_share", "community_enrichment", "pagerank_top10",
    "fit_time_kmeans", "fit_time_als",
]


def call(method, path, body=None, token=None, raw=False):
    # Superset takes rison in ?q=, which has to be URL-encoded
    if "?q=" in path:
        head, q = path.split("?q=", 1)
        path = head + "?q=" + urllib.parse.quote(q)

    req = urllib.request.Request(BASE_URL + path, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)

    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data) as resp:
            out = resp.read()
    except urllib.error.HTTPError as err:
        sys.exit(f"{method} {path} -> {err.code}: {err.read().decode()[:600]}")
    return out if raw else json.loads(out or b"{}")


def find_one(path, column, value, operator="eq"):
    """Return the first row of a list endpoint matching a filter, or None."""
    q = {"filters": [{"col": column, "opr": operator, "value": value}]}
    res = call("GET", f"{path}?q=" + json.dumps(q), token=token)
    return res["result"][0] if res["count"] else None


token = call("POST", "/api/v1/security/login", {
    "username": USERNAME, "password": PASSWORD, "provider": "db", "refresh": True,
})["access_token"]


# database and datasets

db = find_one("/api/v1/database/", "database_name", DB_NAME)
if db:
    db_id = db["id"]
else:
    db_id = call("POST", "/api/v1/database/", {
        "database_name": DB_NAME, "sqlalchemy_uri": DB_URI, "expose_in_sqllab": True,
    }, token)["id"]

dataset_ids = {}
for table in TABLES:
    found = find_one("/api/v1/dataset/", "table_name", table)
    if found:
        dataset_ids[table] = found["id"]
    else:
        dataset_ids[table] = call("POST", "/api/v1/dataset/", {
            "database": db_id, "schema": "public", "table_name": table,
        }, token)["id"]


# recreate the dashboard and its charts from scratch

existing = find_one("/api/v1/dashboard/", "slug", DASHBOARD_SLUG)
if existing:
    call("DELETE", f"/api/v1/dashboard/{existing['id']}", token=token)
dash_id = call("POST", "/api/v1/dashboard/", {
    "dashboard_title": DASHBOARD_TITLE, "slug": DASHBOARD_SLUG, "published": True,
}, token)["id"]

old_charts = call("GET", "/api/v1/chart/?q=" + json.dumps({
    "filters": [{"col": "slice_name", "opr": "sw", "value": CHART_PREFIX}],
    "page_size": 100,
}), token=token)
for chart in old_charts["result"]:
    call("DELETE", f"/api/v1/chart/{chart['id']}", token=token)


# chart helpers

chart_names = {}


def metric(column, label=None, aggregate="SUM"):
    return {
        "expressionType": "SIMPLE",
        "column": {"column_name": column},
        "aggregate": aggregate,
        "label": label or column,
        "hasCustomLabel": True,
    }


def make_chart(name, table, viz_type, form_data, queries):
    form_data = dict(form_data, viz_type=viz_type, datasource=f"{dataset_ids[table]}__table")
    query_context = {
        "datasource": {"id": dataset_ids[table], "type": "table"},
        "force": False,
        "queries": queries,
        "form_data": form_data,
        "result_format": "json",
        "result_type": "full",
    }
    chart_id = call("POST", "/api/v1/chart/", {
        "slice_name": CHART_PREFIX + name,
        "viz_type": viz_type,
        "datasource_id": dataset_ids[table],
        "datasource_type": "table",
        "params": json.dumps(form_data),
        "query_context": json.dumps(query_context),
        "dashboards": [dash_id],
    }, token)["id"]
    chart_names[chart_id] = name
    return chart_id


def bar_chart(name, table, x, metrics, group=None, sort_by=None, ascending=False,
              number_format="SMART_NUMBER", horizontal=True, x_title="", y_bounds=None):
    ms = [metric(col, label) for col, label in metrics]
    form_data = {
        "x_axis": x,
        "metrics": ms,
        "groupby": [group] if group else [],
        "orientation": "horizontal" if horizontal else "vertical",
        "row_limit": 1000,
        "show_legend": bool(group) or len(ms) > 1,
        "legendType": "scroll",
        "legendOrientation": "top",
        "y_axis_format": number_format,
        "show_value": True,
        "xAxisForceCategorical": True,
        "x_axis_sort": ms[0]["label"] if sort_by is None else sort_by,
        "x_axis_sort_asc": ascending,
        "color_scheme": "supersetColors",
        "rich_tooltip": True,
        "adhoc_filters": [],
        "truncateYAxis": False,
        "x_axis_title": x_title,
        "x_axis_title_margin": 30,
        "stack": None,
        "tooltipTimeFormat": "smart_date",
        "zoomable": False,
        "y_axis_bounds": y_bounds or [None, None],
    }
    query = {
        "columns": [x] + ([group] if group else []),
        "metrics": ms,
        "orderby": [[ms[0], ascending]],
        "row_limit": 1000,
        "filters": [],
        "extras": {"having": "", "where": ""},
        "annotation_layers": [],
        "series_columns": [group] if group else [],
        "series_limit": 0,
        "order_desc": not ascending,
        "url_params": {},
        "custom_params": {},
        "custom_form_data": {},
    }
    return make_chart(name, table, "echarts_timeseries_bar", form_data, [query])


def kpi_chart(kpi_name):
    m = metric("value")
    form_data = {
        "metric": m,
        "adhoc_filters": [{
            "expressionType": "SIMPLE", "subject": "kpi", "operator": "==",
            "comparator": kpi_name, "clause": "WHERE",
        }],
        "header_font_size": 0.5,
        "subheader_font_size": 0.15,
        "y_axis_format": ",d",
        "time_format": "smart_date",
    }
    query = {
        "columns": [],
        "metrics": [m],
        "filters": [{"col": "kpi", "op": "==", "val": kpi_name}],
        "extras": {"having": "", "where": ""},
        "row_limit": 1,
        "url_params": {},
        "custom_params": {},
        "custom_form_data": {},
    }
    return make_chart(kpi_name, "kpis", "big_number_total", form_data, [query])


def table_chart(name, table, columns, order_by):
    form_data = {
        "query_mode": "raw",
        "all_columns": columns,
        "order_by_cols": [json.dumps([order_by, True])],
        "row_limit": 100,
        "adhoc_filters": [],
        "page_length": 0,
        "include_search": False,
        "show_cell_bars": False,
        "table_timestamp_format": "smart_date",
    }
    query = {
        "columns": columns,
        "metrics": [],
        "orderby": [[order_by, True]],
        "row_limit": 100,
        "filters": [],
        "extras": {"having": "", "where": ""},
        "url_params": {},
        "custom_params": {},
        "custom_form_data": {},
    }
    return make_chart(name, table, "table", form_data, [query])


# charts

KPI_NAMES = ["Raw events", "Distinct users", "Sessions", "Flagged sessions", "Flagged users"]
kpis = {name: kpi_chart(name) for name in KPI_NAMES}

funnel = bar_chart(
    "Event funnel (events by type)", "event_funnel", "event_type",
    [("events", "Events")], ascending=True, number_format=",d")
segments = bar_chart(
    "Session segments (share of sessions, %)", "session_segments", "segment",
    [("share_pct", "Share of sessions (%)")],
    sort_by="Share of sessions (%)", ascending=True, number_format=",.2f")
cart_per_view = bar_chart(
    "Flagged vs normal: cart per view", "flag_groups", "grp",
    [("cart_per_view", "Cart per view")], number_format=",.2f")
events_products = bar_chart(
    "Flagged vs normal: events and products per session", "flag_groups", "grp",
    [("avg_events", "Avg events"), ("avg_products", "Avg distinct products")],
    number_format=",.1f")
reco_quality = bar_chart(
    "Recommendation quality at 10", "reco_quality", "metric",
    [("value", "Value")], group="model", number_format=",.4f")
ndcg_by_share = bar_chart(
    "NDCG@10 by share of users", "reco_ndcg_by_share", "user_share_pct",
    [("ndcg_at_10", "NDCG@10")], group="model", number_format=",.4f",
    sort_by="user_share_pct", ascending=True, x_title="Share of users (%)")
communities = bar_chart(
    "Flagged-user rate by community (%)", "community_enrichment", "community",
    [("flagged_rate_pct", "Flagged users (%)")], number_format=",.1f")
pagerank = table_chart(
    "Top 10 products by PageRank", "pagerank_top10",
    ["rank", "product_id", "brand", "category"], order_by="rank")
kmeans_time = bar_chart(
    "K-Means fit time (seconds)", "fit_time_kmeans", "sessions_m",
    [("seconds", "Seconds")], group="engine", number_format=",.1f",
    sort_by="sessions_m", ascending=True, x_title="Sessions (millions)")
als_time = bar_chart(
    "ALS fit time (seconds)", "fit_time_als", "user_share_pct",
    [("seconds", "Seconds")], group="engine", number_format=",.1f",
    sort_by="user_share_pct", ascending=True, x_title="Share of users (%)",
    y_bounds=[0, 180])


# layout: one tab per topic

position = {
    "DASHBOARD_VERSION_KEY": "v2",
    "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
    "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": ["TABS-main"], "parents": ["ROOT_ID"]},
    "HEADER_ID": {"id": "HEADER_ID", "type": "HEADER", "meta": {"text": DASHBOARD_TITLE}},
    "TABS-main": {"type": "TABS", "id": "TABS-main", "children": [], "parents": ["ROOT_ID", "GRID_ID"]},
}
counter = 0


def add_tab(label, rows):
    """rows is a list of rows, each a list of (chart_id, width, height)."""
    global counter
    tabs = position["TABS-main"]["children"]
    tab_id = f"TAB-{len(tabs) + 1}"
    tabs.append(tab_id)
    tab_parents = ["ROOT_ID", "GRID_ID", "TABS-main"]
    position[tab_id] = {"type": "TAB", "id": tab_id, "children": [], "meta": {"text": label}, "parents": tab_parents}

    for row in rows:
        counter += 1
        row_id = f"ROW-{counter}"
        position[tab_id]["children"].append(row_id)
        position[row_id] = {
            "type": "ROW", "id": row_id, "children": [],
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
            "parents": tab_parents + [tab_id],
        }
        for chart_id, width, height in row:
            counter += 1
            node_id = f"CHART-{counter}"
            position[row_id]["children"].append(node_id)
            position[node_id] = {
                "type": "CHART", "id": node_id, "children": [],
                "meta": {"chartId": chart_id, "width": width, "height": height,
                         "sliceNameOverride": chart_names[chart_id]},
                "parents": tab_parents + [tab_id, row_id],
            }


add_tab("Overview", [
    [(kpis[name], 2, 14) for name in KPI_NAMES],
    [(funnel, 6, 50), (segments, 6, 50)],
])
add_tab("Fraud", [[(cart_per_view, 6, 50), (events_products, 6, 50)]])
add_tab("Recommendation", [[(reco_quality, 6, 50), (ndcg_by_share, 6, 50)]])
add_tab("Graph", [[(communities, 6, 50), (pagerank, 6, 50)]])
add_tab("Spark vs single machine", [[(kmeans_time, 6, 50), (als_time, 6, 50)]])

call("PUT", f"/api/v1/dashboard/{dash_id}", {
    "position_json": json.dumps(position),
    "published": True,
    "json_metadata": json.dumps({
        "color_scheme": "supersetColors", "refresh_frequency": 0, "positions": position,
    }),
}, token)


# export

export = call("GET", "/api/v1/dashboard/export/?q=" + json.dumps([dash_id]), token=token, raw=True)
EXPORT_PATH.parent.mkdir(exist_ok=True)
EXPORT_PATH.write_bytes(export)
print(f"dashboard {dash_id} built: {BASE_URL}/superset/dashboard/{DASHBOARD_SLUG}/")
print(f"export written to {EXPORT_PATH} ({len(export)} bytes)")
