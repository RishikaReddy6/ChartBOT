import streamlit as st
import pandas as pd
import json
import re
import google.generativeai as genai
import plotly.express as px

# ————— Your Gemini key & model setup —————
genai.configure(api_key="YOUR_API_KEY_HERE")  # Replace with your actual Gemini API key
model = genai.GenerativeModel("gemini-2.5-pro")

def parse_prompt_with_gemini(user_prompt: str, columns: list) -> dict:
    """
    Ask Gemini to interpret the user's natural-language prompt
    and return a chart spec JSON with keys:
      - chart_type: bar|pie|line|histogram|scatter|box|heatmap|treemap
      - x_column, y_column, group_by: or null
      - filters: list of {column, op, values}
    Strips any ```json fences before parsing.
    """
    cols = ", ".join(columns)
    full_prompt = (
        f"You are a data-visualization assistant. I have a CSV with these columns: {cols}."
        "When given a user request, respond in strict JSON with keys:"
        "  - chart_type: one of \"bar\", \"pie\", \"line\", \"histogram\", \"scatter\", \"box\", \"heatmap\", \"treemap\""
        "  - x_column: column name or null"
        "  - y_column: column name or null"
        "  - group_by: column name or list of columns or null"
        "  - filters: list of objects with keys 'column', 'op', 'values' or empty list"
        "For example:"
        "{\"chart_type\":\"bar\",\"x_column\":\"city\",\"y_column\":null,"
        "\"group_by\":\"season\",\"filters\":[{\"column\":\"season\",\"op\":\"between\",\"values\":[2020,2024]}]}"
        f"User request: {user_prompt}"
    )
    response = model.generate_content(full_prompt)
    content = response.text.strip()
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content).strip()
    try:
        spec = json.loads(content)
    except json.JSONDecodeError:
        return {"chart_type": None, "x_column": None,
                "y_column": None, "group_by": None,
                "filters": [], "error": "Could not parse JSON from Gemini:\n" + content}
    spec.setdefault("filters", [])
    return spec


def apply_filters(df: pd.DataFrame, filters: list) -> pd.DataFrame:
    """Apply Gemini-provided filters to the DataFrame."""
    df_filtered = df.copy()
    for flt in filters:
        col = flt.get("column")
        op = flt.get("op")
        vals = flt.get("values")
        if not col or vals is None:
            continue
        # Prepare a series for comparison, coerce types if necessary
        try:
            series = pd.to_numeric(df_filtered[col], errors='coerce')
            val0 = float(vals[0]) if isinstance(vals, (list, tuple)) else float(vals)
            val1 = float(vals[1]) if isinstance(vals, (list, tuple)) and len(vals) > 1 else None
        except Exception:
            series = df_filtered[col]
            val0 = vals[0] if isinstance(vals, (list, tuple)) else vals
            val1 = vals[1] if isinstance(vals, (list, tuple)) and len(vals) > 1 else None

        if op == "between" and val1 is not None:
            mask = series.between(val0, val1)
        elif op == "==":
            mask = series == val0
        elif op == ">=":
            mask = series >= val0
        elif op == "<=":
            mask = series <= val0
        else:
            # unsupported op: skip
            continue

        df_filtered = df_filtered[mask]
    return df_filtered


def make_chart(df: pd.DataFrame, spec: dict):
    """
    Given a DataFrame and a spec dict, produce a Plotly Figure.
    Supported chart_type: bar, pie, line, histogram, scatter, box, heatmap, treemap.
    """
    ct   = spec.get("chart_type")
    xcol = spec.get("x_column")
    ycol = spec.get("y_column")
    grp  = spec.get("group_by")
    if isinstance(grp, str): grp = [grp]

    # BAR
    if ct == "bar":
        if ycol:
            fig = px.bar(df, x=xcol, y=ycol, color=grp or None,
                         barmode="group" if grp else None,
                         title=f"Bar chart of {ycol} vs {xcol}")
        else:
            counts = df[xcol].value_counts().reset_index()
            counts.columns = [xcol, "count"]
            fig = px.bar(counts, x=xcol, y="count",
                         title=f"Count of {xcol}")

    # PIE
    elif ct == "pie":
        if ycol:
            df_agg = df.groupby(grp or xcol)[ycol].sum().reset_index()
            names = grp or xcol; values = ycol
        else:
            df_agg = df[xcol].value_counts().reset_index()
            df_agg.columns = [xcol, "count"]; names = xcol; values = "count"
        fig = px.pie(df_agg, names=names, values=values,
                     title=f"Pie chart of {names}")

    # LINE
    elif ct == "line":
        if not ycol:
            st.error("Line chart requires a y_column."); return None
        fig = px.line(df, x=xcol, y=ycol, color=grp or None,
                      title=f"Line chart of {ycol} vs {xcol}")

    # HISTOGRAM
    elif ct == "histogram":
        col = ycol or xcol
        fig = px.histogram(df, x=col, title=f"Histogram of {col}")

    # SCATTER
    elif ct == "scatter":
        if not ycol:
            st.error("Scatter plot requires a y_column."); return None
        fig = px.scatter(df, x=xcol, y=ycol, color=grp or None,
                         title=f"Scatter plot of {ycol} vs {xcol}")

    # BOX
    elif ct == "box":
        if not ycol:
            st.error("Box plot requires a y_column."); return None
        fig = px.box(df, x=grp or None, y=ycol,
                     title=f"Box plot of {ycol}{' by ' + ','.join(grp) if grp else ''}")

    # HEATMAP
    elif ct == "heatmap":
        corr = df.select_dtypes(include=['number']).corr()
        fig = px.imshow(corr, text_auto=True,
                        title="Heatmap of numeric feature correlations")

    # TREEMAP
    elif ct == "treemap":
        path = grp or []
        if not path:
            st.error("Treemap requires at least one grouping column."); return None
        if not ycol:
            df_agg = df.groupby(path).size().reset_index(name="count"); size_col = "count"
        else:
            df_agg = df.groupby(path)[ycol].sum().reset_index(); size_col = ycol
        fig = px.treemap(df_agg, path=path, values=size_col,
                         title=f"Treemap of {size_col} grouped by {' → '.join(path)}")

    else:
        st.error(f"Unsupported chart type: {ct}"); return None

    fig.update_layout(margin={"l":40,"r":40,"t":50,"b":40}, hovermode="closest")
    return fig

# ————— Streamlit UI —————
st.title("Smart CSV Visualizer MVP")

uploaded_file = st.file_uploader("Upload a CSV file", type="csv")
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.subheader("Preview of your data")
    st.write(df.head())

    user_prompt = st.text_input(
        "Enter your chart request (e.g., 'bar chart of matches by city for season 2020-2024')"
    )

    if st.button("Generate"):
        st.subheader("Your request:")
        st.write(user_prompt)

        cols = df.columns.tolist()
        spec = parse_prompt_with_gemini(user_prompt, cols)
        st.subheader("🔍 Parsed spec:")
        st.json(spec)

        df_filtered = apply_filters(df, spec.get("filters", []))
        fig = make_chart(df_filtered, spec)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        elif spec.get("error"):
            st.error(spec["error"])
