import pandas as pd
import plotly.graph_objs as go
import requests
import streamlit as st
import yaml
import yfinance as yf
from streamlit_authenticator import Authenticate
from yaml.loader import SafeLoader

from config import api_key

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

name, authentication_status, username = authenticator.login('Login', 'main')

def show_main_currencies():
    vs_currency = 'USD'
    currencies = ['MXN','AUD','JPY', 'GBP']

    st.subheader("Principales Monedas Globales")
    exchange_rate = {}
    bid_price = {}
    ask_price ={}
    st.text(f"Moneda de referencia: {vs_currency}")
    for c in currencies:
        url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={c}&to_currency={vs_currency}&apikey={api_key}"
        r = requests.get(url)
        data = r.json()
        data = data['Realtime Currency Exchange Rate']
        exchange_rate[c] = data['5. Exchange Rate']
        bid_price[c] = data['8. Bid Price']
        ask_price[c] = data['9. Ask Price']
    with st.container():
        df = pd.DataFrame({
            'Moneda': currencies,
            'Tipo de Cambio': exchange_rate.values(),
            'Compra': bid_price.values(),
            'Venta': ask_price.values()
            })
        st.table(df)


if authentication_status is None:
    st.warning('Please enter your username and password')
    st.session_state["Auth"] = 0
elif not authentication_status:
    st.error('Username/password is incorrect')
    st.session_state["Auth"] = 0
elif authentication_status:
    st.session_state["Auth"] = 1
    with st.sidebar:
        authenticator.logout('Logout', 'main')

if st.session_state["Auth"] == 1:
    st.title("Analysis of economic situation by stock")

    ticker = st.text_input("Select your Ticker: ")
    start_date = st.date_input("Select starting date to analyze")
    end_date = st.date_input("Select ending date to analyze")
    if len(ticker) == 0 or start_date == end_date:
        st.error("Stock not available or date not selected")
        st.stop()
    data = yf.download(ticker, start=start_date, end=end_date)

    # Crear una figura de Plotly
    fig = go.Figure()

    # Agregar una línea de gráfica para el precio de cierre ajustado
    fig.add_trace(go.Scatter(x=data.index, y=data['Adj Close'], mode='lines', line=dict(color='maroon')))

    # Configurar el título y etiquetas de los ejes
    fig.update_layout(
        title=ticker,
        xaxis_title='Date',
        yaxis_title='Adj. Close Price',
        xaxis=dict(tickangle=-45)
    )
    st.plotly_chart(fig)
    st_date = str(start_date)
    n_news = st.number_input("Select the number of news", 0, 5, 3)
    # NEWS
    url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&" \
          f"time_from={st_date.replace('-', '') + 'T0000'}&limit=3&sort=RELEVANCE&apikey={api_key}"
    r = requests.get(url)
    data = r.json()
    st.subheader("News")
    news_list = [data['feed'][i]['summary'] for i in range(n_news)]
    for i in range(n_news):
        st.write(news_list[i])
        st.write("---")

    show_main_currencies()

