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

COLORSCALES = ["Turbo", "Jet", "Viridis", "Hot", "Portland", "Earth"]


@st.cache_resource
def build_figure(colorscale, elevation_range):
    z = np.where(
        (ELEVATION >= elevation_range[0]) & (ELEVATION <= elevation_range[1]),
        TEMP,
        np.nan,
    )
    fig = go.Figure(
        go.Surface(
            x=X,
            y=Y,
            z=z,
            name="Sun Heated Landscape",
            colorscale=colorscale,
            cmin=float(TEMP.min()),
            cmax=float(TEMP.max()),
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

    fig.update_layout(
        title="☀️ Sun Heated Landscape",
        scene=dict(
            xaxis_title="East-West",
            yaxis_title="North-South",
            zaxis_title="Temperature",
            zaxis=dict(range=[float(TEMP.min()), float(TEMP.max())]),
            camera=dict(eye=dict(x=1.7, y=1.7, z=0.9)),
        ),
        margin=dict(l=0, r=0, b=0, t=40),
        height=750,
    )
    return fig


_dropdown_col, _, _, _ = st.columns(4)
with _dropdown_col:
    selected_colorscale = st.selectbox("Colorscale", COLORSCALES, index=0)

elevation_range = st.slider(
    "🏔️ Elevation slicer (m)",
    float(ELEVATION.min()),
    float(ELEVATION.max()),
    (float(ELEVATION.min()), float(ELEVATION.max())),
)

fig = build_figure(selected_colorscale, elevation_range)


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

    st.markdown("---")
    st.subheader("✂️ Cross-section")

    axis_col, slider_col = st.columns([1, 3])
    with axis_col:
        axis = st.selectbox("Axis", ["X (East-West)", "Y (North-South)"])
    with slider_col:
        if axis.startswith("X"):
            fixed_value = st.slider("X value", float(x.min()), float(x.max()), 0.0)
        else:
            fixed_value = st.slider("Y value", float(y.min()), float(y.max()), 0.0)

    if axis.startswith("X"):
        idx = int(np.abs(x - fixed_value).argmin())
        section_x = y
        section_temp = TEMP[:, idx]
        section_title = f"Temperature along Y at X = {x[idx]:.1f} km"
        section_xaxis = "North-South (km)"
    else:
        idx = int(np.abs(y - fixed_value).argmin())
        section_x = x
        section_temp = TEMP[idx, :]
        section_title = f"Temperature along X at Y = {y[idx]:.1f} km"
        section_xaxis = "East-West (km)"

    section_fig = go.Figure(
        go.Scatter(x=section_x, y=section_temp, mode="lines", line=dict(color="#ff6b35", width=3))
    )
    section_fig.update_layout(
        title=section_title,
        xaxis_title=section_xaxis,
        yaxis_title="Temperature (°C)",
        height=350,
        margin=dict(l=0, r=0, b=0, t=40),
    )
    st.plotly_chart(section_fig, use_container_width=True)

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
