import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.graph_objects as go
import numpy as np

st.title("Premier League GF vs xG with Club Logos")

# Step 1: Scrape the table + logos
@st.cache_data(ttl=3600)
def get_pl_data():
    url = "https://fbref.com/en/comps/9/Premier-League-Stats"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table", {"class": "stats_table"})

    # Extract logos and team names
    logos = []
    teams = []
    rows = table.find_all("tr")[1:]  # skip header
    for row in rows:
        squad_cell = row.find("td", {"data-stat": "team"})
        if squad_cell:
            img_tag = squad_cell.find("img")
            if img_tag and img_tag.has_attr("src"):
                src = img_tag["src"]
                if src.startswith("http"):
                    logo_url = src
                else:
                    logo_url = "https://fbref.com" + src
            else:
                logo_url = None
            logos.append(logo_url)
            teams.append(squad_cell.text.strip())

    # Parse table to DataFrame
    df = pd.read_html(str(table))[0]

    # Align lengths and add logos and clean data
    df = df.iloc[: len(teams)].copy()
    df["Logo"] = logos
    df["Squad"] = teams

    df["GF"] = pd.to_numeric(df["GF"], errors="coerce")
    df["xG"] = pd.to_numeric(df["xG"], errors="coerce")

    return df

df = get_pl_data()

# Show the full extracted Premier League table first
st.write("Premier League full table:")
st.dataframe(df)

# Prepare figure
fig = go.Figure()

# Add logos as scatter points
for _, row in df.iterrows():
    if pd.notna(row["GF"]) and pd.notna(row["xG"]):
        if row["Logo"]:
            fig.add_layout_image(
                dict(
                    source=row["Logo"],
                    x=row["xG"],
                    y=row["GF"],
                    xref="x",
                    yref="y",
                    sizex=1.5,
                    sizey=1.5,
                    xanchor="center",
                    yanchor="middle",
                    sizing="contain",
                    layer="above",
                )
            )
        else:
            fig.add_trace(
                go.Scatter(
                    x=[row["xG"]],
                    y=[row["GF"]],
                    mode="markers+text",
                    text=[row["Squad"]],
                    textposition="top center",
                    marker=dict(size=10, color="blue"),
                    showlegend=False,
                )
            )

# Add line of best fit (linear regression)
x_vals = df["xG"].dropna().values
y_vals = df["GF"].dropna().values
if len(x_vals) > 1:
    coeffs = np.polyfit(x_vals, y_vals, 1)
    poly_eq = np.poly1d(coeffs)
    x_line = np.linspace(min(x_vals), max(x_vals), 100)
    y_line = poly_eq(x_line)

    fig.add_trace(
        go.Scatter(
            x=x_line,
            y=y_line,
            mode="lines",
            line=dict(color="red", dash="dash"),
            name="Best Fit Line",
        )
    )

# Layout settings
fig.update_layout(
    title="Goals For (GF) vs Expected Goals (xG) with Club Logos",
    xaxis_title="xG (Expected Goals)",
    yaxis_title="GF (Goals For)",
    xaxis=dict(range=[df["xG"].min() - 1, df["xG"].max() + 1], zeroline=False),
    yaxis=dict(range=[df["GF"].min() - 1, df["GF"].max() + 1], zeroline=False),
    height=600,
    width=800,
    showlegend=True,
    template="plotly_white",
    margin=dict(l=40, r=40, t=60, b=40),
)

st.plotly_chart(fig, use_container_width=True)
