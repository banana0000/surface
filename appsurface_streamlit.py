import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Sun Heated Landscape", layout="wide")

# --------------------------
# Pre-generated dataset (for the table below the surface)
# --------------------------

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sun_heated_landscape.csv")


@st.cache_data
def load_dataset(path):
    return pd.read_csv(path)


dataset_df = load_dataset(CSV_PATH)

# --------------------------
# Grid
# --------------------------

x = np.linspace(-20, 20, 120)
y = np.linspace(-20, 20, 120)
X, Y = np.meshgrid(x, y)

# --------------------------
# Temperature model
# --------------------------

BASE = 20

SUN = 18 * np.exp(-((X - 2) ** 2 + (Y - 1) ** 2) / 30)
ROCK = 6 * np.exp(-((X + 10) ** 2 + (Y + 8) ** 2) / 20)
SHADOW = -5 * np.exp(-((X - 12) ** 2 + (Y - 10) ** 2) / 15)

ELEVATION = 300 * np.sin(X / 4) + 200 * np.cos(Y / 5) + 250  # synthetic terrain elevation, meters

LAPSE_RATE = 6.5 / 1000  # standard atmospheric lapse rate: -6.5°C per 1000 m
LAPSE = -LAPSE_RATE * ELEVATION

TEMP = BASE + SUN + ROCK + SHADOW + LAPSE

# --------------------------
# Summary stats
# --------------------------

_hottest = dataset_df.loc[dataset_df["temperature"].idxmax()]
_coldest = dataset_df.loc[dataset_df["temperature"].idxmin()]

SUMMARY_TEXT = (
    f"The terrain contains {TEMP.size} grid points. Temperature ranges "
    f"from {TEMP.min():.1f}°C to {TEMP.max():.1f}°C, "
    f"averaging {TEMP.mean():.1f}°C. "
    f"The hottest point is at ({_hottest['x']:.1f}, {_hottest['y']:.1f}) "
    f"with {_hottest['temperature']:.1f}°C, mainly due to sun exposure. "
    f"The coldest point is at ({_coldest['x']:.1f}, {_coldest['y']:.1f}) "
    f"with {_coldest['temperature']:.1f}°C, where the shadow effect dominates."
)


# --------------------------
# Surface figure
# --------------------------

@st.cache_resource
def build_figure():
    fig = go.Figure(
        go.Surface(
            x=X,
            y=Y,
            z=TEMP,
            name="Sun Heated Landscape",
            colorscale="Turbo",
            hovertemplate=(
                "<b>X</b>: %{x:.2f} km<br>"
                "<b>Y</b>: %{y:.2f} km<br>"
                "<b>Temperature</b>: %{z:.1f} °C<extra></extra>"
            ),
            lighting=dict(ambient=0.5, diffuse=1, specular=0.8, roughness=0.15),
            lightposition=dict(x=200, y=150, z=400),
            contours={"z": {"show": True, "project": {"z": True}}},
        )
    )

    colorscales = ["Turbo", "Jet", "Viridis", "Hot", "Portland", "Earth"]
    fig.update_layout(
        title="☀️ Sun Heated Landscape",
        scene=dict(
            xaxis_title="East-West",
            yaxis_title="North-South",
            zaxis_title="Temperature",
            camera=dict(eye=dict(x=1.7, y=1.7, z=0.9)),
        ),
        margin=dict(l=0, r=0, b=0, t=40),
        height=750,
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                showactive=True,
                x=1,
                y=1.1,
                xanchor="right",
                yanchor="top",
                buttons=[
                    dict(label=scale, method="restyle", args=[{"colorscale": scale}])
                    for scale in colorscales
                ],
            )
        ],
    )
    return fig


fig = build_figure()


# --------------------------
# Layout
# --------------------------

main_col, side_col = st.columns([3, 1])

with main_col:
    st.plotly_chart(fig, use_container_width=True, key="surface")

    st.download_button(
        "⬇️ Download as HTML",
        data=fig.to_html(full_html=True, include_plotlyjs="cdn"),
        file_name="sun_heated_landscape.html",
        mime="text/html",
    )

    st.markdown("---")
    st.subheader("Summary")
    st.write(SUMMARY_TEXT)

with side_col:
    st.markdown(
        """
        <style>
        div[data-testid="stVerticalBlock"] > div:has(> div.side-panel) {
            background: #F5F5F5;
            padding: 20px;
            border-radius: 6px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.header("☀️ Sun Heated Landscape")
    st.markdown("---")
    st.subheader("Statistics")
    st.write(f"Minimum : {TEMP.min():.1f} °C")
    st.write(f"Average : {TEMP.mean():.1f} °C")
    st.write(f"Maximum : {TEMP.max():.1f} °C")

# --------------------------
# Dataset table
# --------------------------

st.markdown("---")
st.subheader("📋 Dataset (sun_heated_landscape.csv)")

_column_labels = {
    "x": "↔️ X",
    "y": "↕️ Y",
    "sun": "☀️ Sun",
    "rock": "🪨 Rock",
    "shadow": "🌑 Shadow",
    "elevation": "🏔️ Elevation (m)",
    "lapse": "❄️ Lapse (°C)",
    "temperature": "🌡️ Temperature",
}

st.dataframe(
    dataset_df.round(3),
    column_config={
        col: st.column_config.Column(label=label)
        for col, label in _column_labels.items()
        if col in dataset_df.columns
    },
    height=500,
    use_container_width=True,
)
