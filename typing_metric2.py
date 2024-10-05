import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, dash_table
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import webbrowser
from threading import Timer
from datetime import datetime

# Custom color theme for Bloomberg-like interface
theme = {
    'background': '#121212',
    'text': '#F5F5F5',
    'accent': '#FF4500',
    'highlight': '#FF6347',
    'plot_bg': '#1a1a1a',
    'line': '#00CED1',
    'table_header': '#FF4500',
    'table_border': '#FF6347',
    'choropleth_shades': ['#00CED1', '#00BFFF', '#1E90FF', '#4169E1', '#000080'],
    'dropdown_text_color': '#FF4500'
}

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

def open_browser():
    webbrowser.open_new("http://127.0.0.1:8050/")

# Function to get stock data based on ticker and date range
def get_stock_data(ticker, start_date, end_date):
    stock = yf.Ticker(ticker)
    
    try:
        # Fetch stock data for the given date range
        hist = stock.history(start=start_date, end=end_date)
        
        metrics = {
            'Open': stock.info.get('open', 'N/A'),
            'Close': stock.info.get('previousClose', 'N/A'),
            'High': stock.info.get('dayHigh', 'N/A'),
            'Low': stock.info.get('dayLow', 'N/A'),
            'Volume': stock.info.get('volume', 'N/A'),
            'Market Cap': stock.info.get('marketCap', 'N/A'),
            'PE Ratio': stock.info.get('trailingPE', 'N/A'),
            'Dividend Yield': stock.info.get('dividendYield', 'N/A'),
        }
        return hist, pd.DataFrame(metrics.items(), columns=['Metric', 'Value'])
    except Exception as e:
        print(f"Error fetching data for {ticker}: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()  # Return empty dataframes if there's an error

# Metric and chart type options
metric_options = [
    {'label': 'Open Price', 'value': 'Open'},
    {'label': 'Close Price', 'value': 'Close'},
    {'label': 'Day High', 'value': 'High'},
    {'label': 'Day Low', 'value': 'Low'},
    {'label': 'Volume', 'value': 'Volume'},
    {'label': 'Market Cap', 'value': 'Market Cap'},
    {'label': 'PE Ratio', 'value': 'PE Ratio'},
    {'label': 'Dividend Yield', 'value': 'Dividend Yield'}
]

chart_type_options = [
    {'label': 'Line', 'value': 'lines'},
    {'label': 'Bar', 'value': 'bars'},
    {'label': 'Scatter', 'value': 'markers'},
    {'label': 'Bubble', 'value': 'bubble'},
    {'label': 'Candlestick', 'value': 'candlestick'},
    {'label': 'Choropleth Map', 'value': 'choropleth'}
]

# Generate metric graph
def generate_metric_graph(ticker, metric, chart_type, start_date, end_date):
    stock_data, _ = get_stock_data(ticker, start_date, end_date)
    fig = go.Figure()

    if metric in stock_data.columns:
        if chart_type == 'lines':
            fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data[metric], mode='lines', line=dict(color=theme['line'])))
        elif chart_type == 'bars':
            fig.add_trace(go.Bar(x=stock_data.index, y=stock_data[metric], marker_color=theme['line']))
        elif chart_type == 'markers':
            fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data[metric], mode='markers', marker=dict(color=theme['line'])))
        elif chart_type == 'bubble':
            fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data[metric], mode='markers',
                                     marker=dict(size=stock_data['Volume'], color=theme['line'])))
        elif chart_type == 'candlestick':
            fig.add_trace(go.Candlestick(x=stock_data.index,
                                         open=stock_data['Open'],
                                         high=stock_data['High'],
                                         low=stock_data['Low'],
                                         close=stock_data['Close'],
                                         increasing_line_color='green',
                                         decreasing_line_color='red'))
        fig.update_layout(
            title=f"{metric} for {ticker}",
            plot_bgcolor=theme['plot_bg'],
            paper_bgcolor=theme['background'],
            font_color=theme['text'],
            xaxis_title="Time",
            yaxis_title=metric,
            height=400,
        )
    else:
        fig.update_layout(
            title=f"No data available for {metric} of {ticker}",
            plot_bgcolor=theme['plot_bg'],
            paper_bgcolor=theme['background'],
            font_color=theme['text'],
            height=400,
        )
    return fig

# App layout
app.layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                html.H1("Global Stock Dashboard", style={'color': theme['text'], 'textAlign': 'left'}),
                width=12,
            ),
            style={'padding': '20px'}
        ),
        dbc.Row([
            dbc.Col(
                dcc.Input(
                    id="stock-input", 
                    type="text", 
                    placeholder="Enter Stock Symbol...", 
                    style={'width': '100%', 'backgroundColor': theme['plot_bg'], 'color': theme['text']}
                ),
                width=12,
            )
        ], style={'padding': '10px'}),

        # Date range filter
        dbc.Row([
            dbc.Col(
                dcc.DatePickerRange(
                    id='date-picker-range',
                    min_date_allowed=datetime(2000, 1, 1),
                    max_date_allowed=datetime.now(),
                    start_date=datetime.now().replace(year=datetime.now().year - 1),
                    end_date=datetime.now(),
                    style={'color': theme['text']}
                ),
                width=12
            ),
        ], style={'padding': '10px'}),

        # Dropdowns and graph
        dbc.Row([
            dbc.Col([ 
                dcc.Dropdown(
                    id=f"metric-dropdown-{i}",
                    options=metric_options,
                    value='Close',
                    style={'backgroundColor': theme['plot_bg'], 'color': theme['dropdown_text_color']},
                    clearable=False
                ),
                dcc.Dropdown(
                    id=f"chart-type-dropdown-{i}",
                    options=chart_type_options,
                    value='lines',
                    style={'backgroundColor': theme['plot_bg'], 'color': theme['dropdown_text_color']},
                    clearable=False
                ),
            ], width=3) for i in range(4)
        ]),

        dbc.Row([
            dbc.Col(
                dcc.Graph(id=f"metric-graph-{i}", style={'height': '400px'}),
                width=6
            ) for i in range(4)
        ]),

        dbc.Row([  
            dbc.Col(
                dash_table.DataTable(
                    id="stock-metrics",
                    columns=[{"name": i, "id": i} for i in ['Metric', 'Value']],
                    style_header={
                        'backgroundColor': theme['plot_bg'], 
                        'color': theme['table_header'],
                        'border': f"2px solid {theme['table_border']}"
                    },
                    style_data={
                        'backgroundColor': theme['plot_bg'], 
                        'color': theme['text'],
                    },
                    style_table={
                        'border': f"2px solid {theme['table_border']}"
                    },
                    style_cell={'textAlign': 'left', 'padding': '10px'},
                    style_data_conditional=[
                        {'if': {'row_index': 'odd'}, 'backgroundColor': '#1a1a1a'},
                    ],
                ),
                width=6
            ),
        ], style={'paddingTop': '20px'}),
    ],
    fluid=True,
    style={'backgroundColor': theme['background']}
)

# Callback to update graphs based on inputs
@app.callback(
    [Output(f"metric-graph-{i}", "figure") for i in range(4)] + 
    [Output("stock-metrics", "data")],
    [Input("stock-input", "value"),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date')] +
    [Input(f"metric-dropdown-{i}", "value") for i in range(4)] +
    [Input(f"chart-type-dropdown-{i}", "value") for i in range(4)]
)
def update_graphs(ticker, start_date, end_date, *args):
    if not ticker:
        return [go.Figure()] * 4, []
    
    metric_values = args[:4]
    chart_values = args[4:]
    
    figures = [
        generate_metric_graph(ticker, metric_values[i], chart_values[i], start_date, end_date)
        for i in range(4)
    ]

    # Get stock metrics table data
    _, metrics_df = get_stock_data(ticker, start_date, end_date)
    
    return figures + [metrics_df.to_dict('records')]

if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run_server(debug=False)
