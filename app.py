import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import fbprophet
import yfinance


def get_history(stock_data, n_years=5):
    history = stock_data.history(period=f'{n_years}y').Close.reset_index().rename({'Date': 'ds', 'Close': 'y'}, axis=1)

    if history.empty:
        raise ValueError

    prophet = fbprophet.Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        seasonality_mode='multiplicative'
    )
    prophet.fit(history)
    future = prophet.make_future_dataframe(periods=365)
    future['floor'] = 0
    forecast = prophet.predict(future)
    return history, forecast


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.H1('Fancy Stock Tool™'),
    html.Div(['Created using ',
              html.A('dash and plot.ly', href='https://plotly.com/', target='_blank'),
              ' for the dashboard and graphics, ',
              html.A('Facebook Prophet', href='https://facebook.github.io/prophet/', target='_blank'),
              ' for the prediction and ',
              html.A('yfinance', href='https://github.com/ranaroussi/yfinance', target='_blank'),
              ' for the financial data pulled from ',
              html.A('yahoo finance', href='https://finance.yahoo.com/', target='_blank'),
              '. Deployed using ',
              html.A('Docker', href='https://www.docker.com/', target='_blank'),
              '.',
              html.Br(),
              html.B('Only use for playing around, not for actually investing any money.')
              ]),
    html.Hr(),
    html.Div(id='input-and-error', children=[
        dcc.Input(id='ticker-input', debounce=True, placeholder='Ticker symbol, e.g. MSFT', type='text',
                  style={'width': '100', 'display': 'inline-block'}),
        html.Div(html.Button(id='predict-button', children='Make prediction', n_clicks=0),
                 style={'width': '100', 'display': 'inline-block', 'padding': 10}),
        html.Label(id='error-message',
                   style={'width': '49%', 'display': 'inline-block', 'padding': 10, 'color': 'red'}),
    ]),

    dcc.Loading(id='graph-placeholder')
])


@app.callback(
    Output('graph-placeholder', 'children'),
    [Input('predict-button', 'n_clicks')],
    [State('ticker-input', 'value')]
)
def update_ticker(n_clicks, ticker):
    if n_clicks > 0:
        stock_data = yfinance.Ticker(ticker)

        try:
            history, forecast = get_history(stock_data)
        except ValueError:
            return html.Label('Ticker symbol does not exist.', style={'color': 'red'})

        try:
            info = stock_data.get_info()
            currency = info['currency']
            name = info['longName']
        except IndexError:
            currency = 'Currency'
            name = ticker

        fig = go.Figure()

        fig.add_scatter(x=forecast.ds, y=forecast.yhat_lower, line={'color': 'rgba(0,0,0,0)', 'dash': 'dot'},
                        name='Forecast (lower)', showlegend=False)
        fig.add_scatter(x=forecast.ds, y=forecast.yhat_upper, line={'color': 'rgba(0,0,0,0)', 'dash': 'dot'},
                        fill='tonexty', fillcolor='rgb(192,192,192)', name='Forecast (upper)', showlegend=False)

        fig.add_scatter(x=forecast.ds, y=forecast.yhat, line={'color': 'black', 'dash': 'dot'}, name='Forecast')
        fig.add_scatter(x=history.ds, y=history.y, line={'color': 'red'}, name='Stock Price')

        fig.update_layout(
            title=f'Stock Price Forecast for {name}',
            xaxis_title='Date',
            yaxis_title=currency,
        )

        return dcc.Graph(figure=fig)

if __name__ == '__main__':
    app.run_server(host='0.0.0.0')
