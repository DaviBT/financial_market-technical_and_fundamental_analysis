import yfinance as yf
import pandas as pd
from datetime import datetime
import pandas as pd
import plotly.express as px  
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, Input, Output  

app = Dash(__name__, external_stylesheets=[dbc.themes.CERULEAN]) 

# defining the date format and the year where the analisis will begin
difYears = 2
refDate = datetime.now() - pd.DateOffset(years = difYears)
refDate = refDate.strftime('%Y-%m-%d')

# tickers
tickers = [

    # Tickers brasileiros (.SA)
    "VALE3.SA","ABEV3.SA","BPAC11.SA","WEGE3.SA","PETR4.SA","PETR3.SA",
    "ITUB4.SA","ITSA4.SA","BBDC4.SA","BBDC3.SA","BBAS3.SA","B3SA3.SA",
    "ELET3.SA","ELET6.SA","LREN3.SA","MGLU3.SA","GGBR4.SA","CSNA3.SA",
    "SUZB3.SA","VIVT4.SA","HYPE3.SA","RADL3.SA","PRIO3.SA","CPFE3.SA",
    "ENGI11.SA","TAEE11.SA","TIMS3.SA","TOTS3.SA","ITUB3.SA","BBSE3.SA",
    "BTGL11.SA","BRML3.SA","CCRO3.SA","CYRE3.SA","UGPA3.SA","QUAL3.SA"
]


# App layout
app.layout = dbc.Container([

    dbc.Row([
        dbc.Col(html.H1("Análise Técnica e Fundamentalista", 
                        className="text-center text-primary mb-4"),
                width=12)
    ]),

    dbc.Row([
        dbc.Col([
            html.Label("Selecione um Ticker:", className="fw-bold"),
            dcc.Dropdown(
                id="ticker_slct",
                options=[{"label": ticker, "value": ticker} for ticker in tickers],
                multi=False,
                value="VALE3.SA",
                style={"width": "100%"}
            ),
        ], md=6, className="mb-3")
    ], justify="center"),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Ticker"),
                dbc.CardBody(id='output_container', children=[]),
            ])
        ], md=12)
    ], className="mb-4"),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Performance da Ação"),
                dbc.CardBody([
                    dcc.Graph(id='ticker_graph', figure={})
                ])
            ])
        ], md=12)
    ], className="mb-4"),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Informações da Empresa"),
                dbc.CardBody(id='output-div')
            ])
        ], md=12)
    ])

], fluid=True, className="p-4 bg-light") 


# ------------------------------------------------------------------------------
# Connect the Plotly graphs with Dash Components
@app.callback(
    [
        Output(component_id='output_container', component_property='children'),
        Output(component_id='ticker_graph', component_property='figure')
    ],
    [
        Input(component_id='ticker_slct', component_property='value')
    ]
)
def update_graph(option_slctd):

    container = f"{option_slctd}"

    # downloading the data from yahoo finance
    df = yf.download(option_slctd, start=refDate)
    df.columns = df.columns.get_level_values(0)
    df.reset_index(inplace=True)

    # deleting the lines that doesn'tt contaiin values
    df.dropna(subset=['Open', 'High', 'Low', 'Close'], inplace=True)
    df = df[(df['Open'] > 0) & (df['High'] > 0) & (df['Low'] > 0) & (df['Close'] > 0)]

    # moving averages
    df['SMA_7'] = df['Close'].rolling(window=7).mean()
    df['SMA_25'] = df['Close'].rolling(window=25).mean()

    # reupload the graph when a new ticker is selected
    fig = go.Figure()

    # graphic
    fig.add_trace(go.Candlestick(
        x=df['Date'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Candlestick'
    ))
    # Moving Average 7 days
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['SMA_7'],
        mode='lines',
        name='Média Móvel 7 dias',
        line=dict(color='orange', width=1)
    ))

    # Moving Average 25 days
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['SMA_25'],
        mode='lines',
        name='Média Móvel 25 dias',
        line=dict(color='blue', width=1)
    ))

    # latest close in the pandas dataframe
    latest_close = df['Close'].iloc[-1]
    # Layout
    fig.update_layout(
        title=f'Evolução: {option_slctd}',
        yaxis_title='Preço (R$)',
        xaxis_title='Data',
        xaxis_rangeslider_visible=False,
        annotations=[
        dict(
            text=f'Último Fechamento: R$ {latest_close:.2f}',
            x=0.5,
            y=1.00,
            xref='paper',
            yref='paper',
            showarrow=False,
            font=dict(size=12)
        )
    ]
    )

    return container, fig



# company info
@app.callback(
    Output('output-div', 'children'),
    [
        Input(component_id='ticker_slct', component_property='value')
    ]
)
def update_info(option_slctd):
    share = yf.Ticker(option_slctd)
    info = share.info

    company_info = {
        'Name': info.get('longName'),
            'Industry': info.get('industry'),
            'Sector': info.get('sector'),
            'Market Cap': info.get('marketCap'),
            'Enterprise Value': info.get('enterpriseValue'),
            'EBITDA': info.get('ebitda'),
            'EV/EBITDA': round(info.get('enterpriseValue') / info.get('ebitda'), 2)
                if info.get('enterpriseValue') and info.get('ebitda') else None,
            'P/E': round(info.get('trailingPE'), 2),
            'P/B': round(info.get('priceToBook'), 2),
            'ROE': round(info.get('returnOnEquity') * 100, 2) if info.get('returnOnEquity') else None,
            'ROA': round(info.get('returnOnAssets') * 100, 2) if info.get('returnOnAssets') else None,
            'Revenue (TTM)': info.get('totalRevenue'),
            'Net Income': info.get('netIncomeToCommon'),
            'Dividend Yield (%)': info.get('dividendYield') if info.get('dividendYield') else None,
            'Business Summary': info.get('longBusinessSummary')
    }
    
    if not company_info['Name']:
        return html.P("Error")
    
    return dbc.Container([
        html.H3(company_info['Name'], className='text-center my-4'),

        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("Sector"),
                dbc.CardBody(html.P(company_info['Sector'] or "N/A"))
            ]), md=4),

            dbc.Col(dbc.Card([
                dbc.CardHeader("Industry"),
                dbc.CardBody(html.P(company_info['Industry'] or "N/A"))
            ]), md=4),

            dbc.Col(dbc.Card([
                dbc.CardHeader(
                    "Market Cap", id="market-cap-text",
                    style={"cursor": "help"}
                    ),
                dbc.CardBody(
                    html.P([
                        html.Span(
                            f"R${company_info['Market Cap']:,}" if company_info['Market Cap'] else "N/A"
                        )
                    ])
                )
            ]), md=4),], className="mb-3"),

            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Enterprise Value"),
                    dbc.CardBody(html.P(f"R${company_info['Enterprise Value']:,}" if company_info['Enterprise Value'] else "N/A"))
            ]), md=4),

            dbc.Col(dbc.Card([
                dbc.CardHeader(
                    "EBITDA", id="ebitda-text",
                    style={"cursor": "help"}
                    ),
                dbc.CardBody(
                    html.P([
                        html.Span(
                            f"R${company_info['EBITDA']:,}" if company_info['EBITDA'] else "N/A"
                        )
                    ])
                )
            ]), md=4),


            dbc.Col(dbc.Card([
                dbc.CardHeader(
                    "EV/EBITDA", id="ev/ebitda-text",
                    style={"cursor": "help"}
                    ),
                dbc.CardBody(
                    html.P([
                        html.Span(
                            f"{company_info['EV/EBITDA']:,}" if company_info['EV/EBITDA'] else "N/A"
                        )
                    ])
                )
            ]), md=4),
            ], className="mb-3"),

            dbc.Row([
                dbc.Col(dbc.Card([
                dbc.CardHeader(
                    "P/E", id="P/E-text",
                    style={"cursor": "help"}
                    ),
                dbc.CardBody(
                    html.P([
                        html.Span(
                            f"{company_info['P/E']:,}" if company_info['P/E'] else "N/A"
                        )
                    ])
                    )
                ]), md=4),

            dbc.Col(dbc.Card([
                dbc.CardHeader(
                    "P/B", id="P/B-text",
                    style={"cursor": "help"}
                    ),
                dbc.CardBody(
                    html.P([
                        html.Span(
                            f"{company_info['P/B']:,}" if company_info['P/B'] else "N/A"
                        )
                    ])
                )
            ]), md=4),

            dbc.Col(dbc.Card([
                dbc.CardHeader(
                    "Dividend Yield", id="dividend-yield-text",
                    style={"cursor": "help"}
                    ),
                dbc.CardBody(
                    html.P([
                        html.Span(
                            f"{company_info['Dividend Yield (%)']:,}%" if company_info['Dividend Yield (%)'] else "N/A"
                        )
                    ])
                )
            ]), md=4),], className="mb-3"),


            dbc.Row([
                dbc.Col(dbc.Card([
                dbc.CardHeader(
                    "ROE", id="ROE-text",
                    style={"cursor": "help"}
                    ),
                dbc.CardBody(
                    html.P([
                        html.Span(
                            f"{company_info['ROE']:,}%" if company_info['ROE'] else "N/A"
                        )
                    ])
                )
            ]), md=6),

            dbc.Col(dbc.Card([
                dbc.CardHeader(
                    "ROA", id="ROA-text",
                    style={"cursor": "help"}
                    ),
                dbc.CardBody(
                    html.P([
                        html.Span(
                            f"{company_info['ROA']:,}%" if company_info['ROA'] else "N/A"
                        )
                    ])
                )
            ]), md=6),], className="mb-3"),

            dbc.Row([
                dbc.Col(dbc.Card([
                dbc.CardHeader(
                    "Revenue (TTM)", id="revenue-ttm-text",
                    style={"cursor": "help"}
                    ),
                dbc.CardBody(
                    html.P([
                        html.Span(
                            f"R${company_info['Revenue (TTM)']:,}" if company_info['Revenue (TTM)'] else "N/A"
                        )
                    ])
                )
            ]), md=6),

                dbc.Col(dbc.Card([
                dbc.CardHeader(
                    "Net Income", id="net-income-text",
                    style={"cursor": "help"}
                    ),
                dbc.CardBody(
                    html.P([
                        html.Span(
                            f"R${company_info['Net Income']:,}" if company_info['Net Income'] else "N/A"
                        )
                    ])
                )
            ]), md=6),
            ]),
        
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Business Summary"),
                    dbc.CardBody(
                        html.P(
                            company_info['Business Summary']
                            if 'Business Summary' in company_info and company_info['Business Summary']
                            else "N/A"
                        ),
                        style={'marginTop': '15px'}
                    )
                ]), md=12),
            ], className="mb-3 mt-2"),



            # tooltips
            # ebitda
            dbc.Tooltip(
                "EBITDA é o proxy da capacidade de geração de caixa de uma empresa. Não leva em conta a variação de necessidade de capital de giro e a necessidade de reinvestimento em ativo fixo.",
                target="ebitda-text",
                placement="top",
                style={"fontSize": "0.9rem"}
            ),
            # market cap
            dbc.Tooltip(
                "Preço da ação multiplicado pela quantidade de ações em circulação.",
                target="market-cap-text",
                placement="top",
                style={"fontSize": "0.9rem"}
            ),
            # EV/EBITDA
            dbc.Tooltip(
                "O resultado do market cap somado com a dívida líquida e dividido pelo EBITDA. Mostra quantos anos de EBITDA são necessários para “pagar” o valor da empresa.",
                target="ev/ebitda-text",
                placement="top",
                style={"fontSize": "0.9rem"}
            ),
            # P/E
            dbc.Tooltip(
                "É o resultado do preço da ação dividido pelo lucro por ação nos últimos 12 meses. Representa quantas vezes o lucro dos últimos 12 meses está sendo pago por cada ação.",
                target="P/E-text",
                placement="top",
                style={"fontSize": "0.9rem"}
            ),
            # P/B
            dbc.Tooltip(
                "Comparação entre o preço da ação e o valor patrimonial por ação. Se for maior que 1, o mercado está pagando mais que o valor patrimonial da empresa.",
                target="P/B-text",
                placement="top",
                style={"fontSize": "0.9rem"}
            ),
            # dividend yield
            dbc.Tooltip(
                "Apresenta o retorno em dividendos sobre a ação comprada em um ano.",
                target="dividend-yield-text",
                placement="top",
                style={"fontSize": "0.9rem"}
            ),
            # ROE
            dbc.Tooltip(
                "Mostra o percentual que o lucro líquido representa do patrimônio líquido da empresa.",
                target="ROE-text",
                placement="top",
                style={"fontSize": "0.9rem"}
            ),
            # ROA
            dbc.Tooltip(
                "Mostra a eficiência da empresa em gerar lucro com os seus ativos.",
                target="ROA-text",
                placement="top",
                style={"fontSize": "0.9rem"}
            ),
            # Revenue TTM
            dbc.Tooltip(
                "Receita bruta da empresa nos últimos 12 meses.",
                target="revenue-ttm-text",
                placement="top",
                style={"fontSize": "0.9rem"}
            ),
            # Net Income
            dbc.Tooltip(
                "Lucro líquido. É a subtração da receita bruta por despesas operacionais, juros e impostos.",
                target="net-income-text",
                placement="top",
                style={"fontSize": "0.9rem"}
            ),


], fluid=True)

server = app.server

if __name__ == '__main__':
    app.run(debug=True)