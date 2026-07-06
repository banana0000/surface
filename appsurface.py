from dash import Dash, dcc, html, Input, Output
import dash_ag_grid as dag
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import os

app = Dash(__name__)

# --------------------------
# Pre-generated dataset (for the table below the surface)
# --------------------------

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sun_heated_landscape.csv")
dataset_df = pd.read_csv(CSV_PATH)

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

SUN = 18*np.exp(-((X-2)**2+(Y-1)**2)/30)

ROCK = 6*np.exp(-((X+10)**2+(Y+8)**2)/20)

SHADOW = -5*np.exp(-((X-12)**2+(Y-10)**2)/15)

ELEVATION = 300*np.sin(X/4) + 200*np.cos(Y/5) + 250  # synthetic terrain elevation, meters

LAPSE_RATE = 6.5/1000  # standard atmospheric lapse rate: -6.5°C per 1000 m

LAPSE = -LAPSE_RATE * ELEVATION

TEMP = BASE + SUN + ROCK + SHADOW + LAPSE

# --------------------------
# Summary stats (for below the surface)
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
# Surface
# --------------------------

fig = go.Figure(

go.Surface(

x=X,

y=Y,

z=TEMP,

colorscale="Turbo",

hovertemplate=

"<b>X</b>: %{x:.2f} km<br>"+

"<b>Y</b>: %{y:.2f} km<br>"+

"<b>Temperature</b>: %{z:.1f} °C<extra></extra>",

lighting=dict(

ambient=0.5,

diffuse=1,

specular=0.8,

roughness=0.15

),

lightposition=dict(

x=200,

y=150,

z=400

),

contours={

"z":{

"show":True,

"project":{"z":True}

}

}

)

)

COLORSCALES = ["Turbo", "Jet", "Viridis", "Hot", "Portland", "Earth"]

fig.update_layout(

title="☀️ Sun Heated Landscape",

scene=dict(

xaxis_title="East-West",

yaxis_title="North-South",

zaxis_title="Temperature",

camera=dict(

eye=dict(

x=1.7,

y=1.7,

z=0.9

)

)

),

margin=dict(

l=0,

r=0,

b=0,

t=40

),

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

for scale in COLORSCALES

],

)

]

)

# --------------------------
# Layout
# --------------------------

app.layout = html.Div([

html.Div([

dcc.Download(id="download-html"),

dcc.Graph(

id="surface",

figure=fig,

style={

"height":"95vh",

"width":"100%"

}

),

html.Hr(),

html.H3("Summary"),

html.P(SUMMARY_TEXT),

],

style={

"width":"74%",

"display":"inline-block"

}),

html.Div([

html.Button(
    "⬇️ Download as HTML",
    id="download-html-btn",
    style={
        "width": "100%",
        "margin": "0 0 15px 0",
        "padding": "8px 16px",
        "background": "#ff6b35",
        "color": "#fff",
        "border": "none",
        "borderRadius": "6px",
        "cursor": "pointer",
        "fontSize": "13px",
    },
),

html.Div(

id="info",

children=[

html.H2("☀️ Selected Point"),

html.Hr(),

html.P("Click on the surface."),

],

),

],

style={

"width":"24%",

"display":"inline-block",

"verticalAlign":"top",

"padding":"20px",

"fontFamily":"Arial",

"background":"#F5F5F5",

"height":"95vh",

"boxSizing":"border-box",

"overflow":"auto"

}

),

    html.Div([

        html.H3("📋 Dataset (sun_heated_landscape.csv)"),

        dag.AgGrid(
            id="dataset-table",
            rowData=dataset_df.head(200).round(3).to_dict("records"),
            columnDefs=[
                {"field": c, "headerName": h, "sortable": True, "filter": True}
                for c, h in {
                    "x": "↔️ X",
                    "y": "↕️ Y",
                    "sun": "☀️ Sun",
                    "rock": "🪨 Rock",
                    "shadow": "🌑 Shadow",
                    "elevation": "🏔️ Elevation (m)",
                    "lapse": "❄️ Lapse (°C)",
                    "temperature": "🌡️ Temperature",
                }.items()
                if c in dataset_df.columns
            ],
            columnSize="responsiveSizeToFit",
            defaultColDef={"resizable": True},
            dashGridOptions={"pagination": True, "paginationPageSize": 15},
            style={"height": "500px", "width": "100%"},
        ),

    ], style={"padding": "20px", "clear": "both"}),

])

# --------------------------
# Callback
# --------------------------

@app.callback(
    Output("download-html", "data"),
    Input("download-html-btn", "n_clicks"),
    prevent_initial_call=True,
)
def download_html(n_clicks):
    html_str = fig.to_html(full_html=True, include_plotlyjs="cdn")
    return dcc.send_string(html_str, filename="sun_heated_landscape.html")


@app.callback(

    Output("info","children"),

    Input("surface","clickData")

)

def update_panel(clickData):

    if clickData is None:

        return [

            html.H2("☀️ Sun Heated Landscape"),

            html.Hr(),

            html.P("Click anywhere on the surface."),

            html.Br(),

            html.H3("Statistics"),

            html.P(f"Minimum : {TEMP.min():.1f} °C"),

            html.P(f"Average : {TEMP.mean():.1f} °C"),

            html.P(f"Maximum : {TEMP.max():.1f} °C")

        ]

    p = clickData["points"][0]

    xx = p["x"]

    yy = p["y"]

    temp = p["z"]

    sun = 18*np.exp(-((xx-2)**2+(yy-1)**2)/30)

    rock = 6*np.exp(-((xx+10)**2+(yy+8)**2)/20)

    shadow = -5*np.exp(-((xx-12)**2+(yy-10)**2)/15)

    elevation = 300*np.sin(xx/4) + 200*np.cos(yy/5) + 250

    lapse = -LAPSE_RATE * elevation

    return [

        html.H2("☀️ Selected Point"),

        html.Hr(),

        html.H3(f"{temp:.1f} °C"),

        html.Br(),

        html.Table([

            html.Tr([html.Td("East-West"),html.Td(f"{xx:.2f} km")]),

            html.Tr([html.Td("North-South"),html.Td(f"{yy:.2f} km")]),

            html.Tr([html.Td("Sun effect"),html.Td(f"+{sun:.1f} °C")]),

            html.Tr([html.Td("Rock heating"),html.Td(f"+{rock:.1f} °C")]),

            html.Tr([html.Td("Shadow"),html.Td(f"{shadow:.1f} °C")]),

            html.Tr([html.Td("Elevation"),html.Td(f"{elevation:.0f} m")]),

            html.Tr([html.Td("Lapse effect"),html.Td(f"{lapse:.1f} °C")]),

            html.Tr([html.Td("Base"),html.Td("20.0 °C")])

        ],

        style={"width":"100%"}

        ),

        html.Br(),

        html.H3("Statistics"),

        html.P(f"Minimum : {TEMP.min():.1f} °C"),

        html.P(f"Average : {TEMP.mean():.1f} °C"),

        html.P(f"Maximum : {TEMP.max():.1f} °C")

    ]

# --------------------------
# Run
# --------------------------

if __name__ == "__main__":

    app.run(debug=True)
