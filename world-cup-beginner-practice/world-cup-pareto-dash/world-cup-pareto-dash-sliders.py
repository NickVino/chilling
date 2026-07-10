import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.graph_objects as go
from kaggle.api.kaggle_api_extended import KaggleApi

# ------------------------------------------------------------------------------
# 1. INITIAL DATA FETCHING & GLOBAL PREPROCESSING
# ------------------------------------------------------------------------------
api = KaggleApi()
api.authenticate()
dataset_path = "swaptr/fifa-wc-2026-players"
api.dataset_download_files(dataset_path, path="./", unzip=True)

df = pd.read_csv("players.csv")
df_country_colors = pd.read_csv("country_colors.csv")

# Add color columns from df_country_colors to df based on matching country names
df = df.merge(df_country_colors, how='left', left_on='team_country', right_on='Country')
df['age_years'] = df['age'].str.extract(r'(\d+)').astype(float)
df['position_first'] = df['position'].str.split(',').str[0]
df['pens_missed'] = df['pens_att'] - df['pens_made']

# Pre-aggregate dataframes to maximize callback performance
df_country_goals = df.groupby(['team_country', 'Primary Color HEX', 'Secondary Color HEX'], as_index=False).agg({'goals': 'sum'}).rename(columns={'goals': 'total_goals'})
df_pareto_country_base = df_country_goals.sort_values(by='total_goals', ascending=False)
df_pareto_country_base['cumulative_goals'] = df_pareto_country_base['total_goals'].cumsum()
df_pareto_country_base['cumulative_percentage'] = df_pareto_country_base['cumulative_goals'] / df_pareto_country_base['total_goals'].sum() * 100

df_player_goals = df.groupby(['player', 'team_country', 'Primary Color HEX', 'Secondary Color HEX'], as_index=False).agg({'goals': 'sum'})
df_pareto_players_base = df_player_goals.sort_values(by='goals', ascending=False)
df_pareto_players_base['cumulative_goals'] = df_pareto_players_base['goals'].cumsum()
df_pareto_players_base['cumulative_percentage'] = df_pareto_players_base['cumulative_goals'] / df_pareto_players_base['goals'].sum() * 100

# Global design variables
global_font = "Arial"
graph_title_size = 18
line_color = "crimson"
bar_opacity = 0.5

# ------------------------------------------------------------------------------
# 2. DASH APPLICATION INITIALIZATION
# ------------------------------------------------------------------------------
app = dash.Dash(__name__)

# ------------------------------------------------------------------------------
# 3. DASH APPLICATION LAYOUT
# ------------------------------------------------------------------------------
app.layout = html.Div(
    style={"backgroundColor": "#F8F9FA", "minHeight": "100vh", "margin": "0", "padding": "0", "fontFamily": "Arial, sans-serif"},
    children=[
        # Title Banner (White text on dark navy background)
        html.Div(
            style={
                "backgroundColor": "#0B192C", 
                "padding": "25px", 
                "textAlign": "center",
                "boxShadow": "0px 4px 10px rgba(0, 0, 0, 0.15)"
            },
            children=[
                html.H1(
                    "FIFA World Cup 2026 Pareto Analysis",
                    style={
                        "color": "#FFFFFF",
                        "margin": "0",
                        "fontFamily": "Arial, sans-serif",
                        "fontWeight": "bold",
                        "letterSpacing": "1px"
                    }
                )
            ]
        ),
        
        # Main Dashboard Grid Container
        html.Div(
            style={"padding": "30px", "display": "flex", "flexWrap": "wrap", "gap": "25px", "justifyContent": "center"},
            children=[
                
                # --- COUNTRY PANEL ---
                html.Div(
                    style={"flex": "1", "minWidth": "600px", "backgroundColor": "white", "padding": "20px", "borderRadius": "8px", "boxShadow": "0 4px 6px rgba(0,0,0,0.05)"},
                    children=[
                        html.Label("Adjust Country Pareto Threshold (%):", style={"fontWeight": "bold", "fontFamily": "Arial", "marginBottom": "15px", "display": "block"}),
                        
                        # Extra wrapper providing a large, tall arena with strict Arial fallback styling 
                        html.Div(
                            style={"height": "90px", "padding": "20px 15px 40px 15px", "fontFamily": "Arial, sans-serif"}, 
                            children=[
                                dcc.Slider(
                                    id="country-slider",
                                    min=5,
                                    max=100,
                                    step=5,
                                    value=40,
                                    # Formats the ticks under the bar directly via inline dictionaries
                                    marks={i: {"label": f"{i}%", "style": {"fontFamily": "Arial", "fontSize": "12px"}} for i in range(10, 101, 10)},
                                )
                            ]
                        ),
                        html.Div(style={"marginTop": "20px"}),
                        dcc.Graph(id="country-pareto-graph")
                    ]
                ),
                
                # --- PLAYER PANEL ---
                html.Div(
                    style={"flex": "1", "minWidth": "600px", "backgroundColor": "white", "padding": "20px", "borderRadius": "8px", "boxShadow": "0 4px 6px rgba(0,0,0,0.05)"},
                    children=[
                        html.Label("Adjust Player Pareto Threshold (%):", style={"fontWeight": "bold", "fontFamily": "Arial", "marginBottom": "15px", "display": "block"}),
                        
                        # Extra wrapper providing a large, tall arena with strict Arial fallback styling 
                        html.Div(
                            style={"height": "90px", "padding": "20px 15px 40px 15px", "fontFamily": "Arial, sans-serif"}, 
                            children=[
                                dcc.Slider(
                                    id="player-slider",
                                    min=5,
                                    max=100,
                                    step=5,
                                    value=20,
                                    # Formats the ticks under the bar directly via inline dictionaries
                                    marks={i: {"label": f"{i}%", "style": {"fontFamily": "Arial", "fontSize": "12px"}} for i in range(10, 101, 10)},
                                )
                            ]
                        ),
                        html.Div(style={"marginTop": "20px"}),
                        dcc.Graph(id="player-pareto-graph")
                    ]
                )
                
            ]
        )
    ]
)

# ------------------------------------------------------------------------------
# 4. INTERACTIVE CALLBACKS
# ------------------------------------------------------------------------------

# Callback for Country Pareto Chart
@app.callback(
    Output("country-pareto-graph", "figure"),
    Input("country-slider", "value")
)
def update_country_chart(threshold):
    df_above = df_pareto_country_base[df_pareto_country_base['cumulative_percentage'] < threshold]
    
    country_count = df_above.shape[0]  # Fixed: extracted row index integer
    total_goals = df_pareto_country_base['total_goals'].sum()
    title_text = f"Pareto Analysis: {country_count} Countries Account for {threshold}% of the {total_goals:.0f} Total Goals Scored"
    
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df_above['team_country'],
            y=df_above['total_goals'],
            name="Country",
            opacity=bar_opacity,
            marker=dict(
                color=df_above['Primary Color HEX'],
                line=dict(color=df_above['Secondary Color HEX'], width=4)
            ),
            yaxis='y1',
            customdata=df_above[['cumulative_goals']].values,
            hovertemplate='<b>%{x}</b><br>Team Goals: %{y}<br>Cumulative Goals: %{customdata[0]}<br><extra></extra>'
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df_above['team_country'],
            y=df_above['cumulative_percentage'],
            name="Cumulative %",
            mode="lines+markers+text",
            text=df_above['cumulative_percentage'].apply(lambda x: f"{x:.1f}%"),
            textposition='top center',
            textfont=dict(color='black', size=12),
            line=dict(color=line_color, width=2, dash='dot', shape='spline'),
            marker=dict(color=line_color, size=14, symbol='circle'),
            yaxis="y2"
        )
    )
    fig.update_layout(
        showlegend=False,
        xaxis=dict(title="Countries", showgrid=False),
        yaxis=dict(title="Goals", side="left", showgrid=False),
        yaxis2=dict(title="Cumulative % of all Goals", side="right", overlaying="y", range=[0, 105], ticksuffix="%", showgrid=False),
        font=dict(family=global_font, size=13, color="Black"),
        title=dict(text=f"<b>{title_text}</b>", font=dict(family=global_font, size=graph_title_size, color="Black")),
        paper_bgcolor='white',
        plot_bgcolor='white',
        template="plotly_white",
        margin=dict(t=80, b=40, l=50, r=50)
    )
    return fig


# Callback for Player Pareto Chart
@app.callback(
    Output("player-pareto-graph", "figure"),
    Input("player-slider", "value")
)
def update_player_chart(threshold):
    df_above = df_pareto_players_base[df_pareto_players_base['cumulative_percentage'] < threshold]
    
    player_count = df_above.shape[0]  # Fixed: extracted row index integer
    total_goals = df_pareto_players_base['goals'].sum()
    title_text = f"Pareto Analysis: {player_count} Players Account for {threshold}% of the {total_goals:.0f} Total Goals Scored"
    
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df_above['player'],
            y=df_above['goals'],
            name="Player",
            opacity=bar_opacity,
            marker=dict(
                color=df_above['Primary Color HEX'],
                line=dict(color=df_above['Secondary Color HEX'], width=4)
            ),
            yaxis='y1',
            customdata=df_above[['team_country']].values,
            hovertemplate='<b>%{x}</b><br>Goals: %{y}<br>Country: %{customdata[0]}<br><extra></extra>'
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df_above['player'],
            y=df_above['cumulative_percentage'],
            name="Cumulative %",
            mode="lines+markers+text",
            text=df_above['cumulative_percentage'].apply(lambda x: f"{x:.1f}%"),
            textposition='top center',
            textfont=dict(color='black', size=12),
            line=dict(color=line_color, width=2, dash='dot', shape='spline'),
            marker=dict(color=line_color, size=14, symbol='circle'),
            yaxis="y2"
        )
    )
    fig.update_layout(
        showlegend=False,
        xaxis=dict(title="Players", showgrid=False),
        yaxis=dict(title="Goals", side="left", showgrid=False),
        yaxis2=dict(title="Cumulative % of all Goals", side="right", overlaying="y", range=[0, 105], ticksuffix="%", showgrid=False),
        font=dict(family=global_font, size=13, color="Black"),
        title=dict(text=f"<b>{title_text}</b>", font=dict(family=global_font, size=graph_title_size, color="Black")),
        paper_bgcolor='white',plot_bgcolor='white',template="plotly_white",margin=dict(t=80, b=40, l=50, r=50))
    return fig

if __name__ == "__main__":
    app.run(debug=True, port=8050)