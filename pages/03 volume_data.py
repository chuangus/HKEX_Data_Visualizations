# -*- coding: utf-8 -*-
"""
Created on Mon Jul 11 09:53:20 2022

@author: Angus
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import numpy as np

st.set_page_config(layout="wide")
st.title('HKEX Volume Analysis')
st.info("Please read documentation https://github.com/epiphronquant/HKEX_Volume regarding methodology")
@st.cache(ttl= 1800) ## Data would need to get reloaded every 30 minutes
def load_data(link):
    df = pd.read_excel(link,sheet_name='Sheet1', header = 0, engine = 'openpyxl', parse_dates = False)
    return df
link = r'https://github.com/chuangus/HKEX_Volume/blob/main/Volume.xlsx?raw=true'
df = load_data(link)

### select sector, select main board, 18A listed 
column_1, column_2,column_3 = st.columns(3) ### Divides page into 2 columns
with column_1:## dropdown box for sector selection
    sectors = df['Sector']
    sectors = sectors.tolist()
    sectors = list(dict.fromkeys(sectors))
    sectors.append('All')### adds an option for All IPOs
    sectors.remove ('Healthcare')
    sectors.append('Healthcare') 
    sectors = sectors [::-1]
    sector = st.selectbox(
        'Which sector are you interested in?',
          sectors)
    'You selected: ', sector
    if sector == 'All':
        pass
    else:
        df = df.loc[df['Sector'] == sector]
        
with column_2: ### Dropdown box for filtering board/boards
    boards = ['Main Board',  'Both', 'GEM']
    board = st.selectbox(
        'Which board are you interested in?',
          boards)
    'You selected: ', board
    if board == 'Main Board': 
        df = df.loc[df['Main Board'] == 1]
    elif board == 'GEM':
        df = df.loc[df['Main Board'] == 0]
    else:
        df = df
with column_3: ### Dropdown box for filtering whether company is 18A or Not
    biotech_listings = ['18A Listed', 'All', 'Not 18A Listed']
    biotech_listing = st.selectbox(
        'Which type of listing are you interested in?',
          biotech_listings)
    'You selected: ', biotech_listing
    if biotech_listing == '18A Listed': 
        df = df.loc[df['18A Listed'] == 1]
    elif biotech_listing == 'Not 18A Listed':
        df = df.loc[df['18A Listed'] == 0]
    else:
        df = df

### chart 1 that shows data on stock price and volume 
# filter data for chart 1      
companies = df['Stock Name']
companies = companies.tolist()
companies = list(dict.fromkeys(companies))
tickers = df['Stock Code']
tickers = tickers.tolist()
tickers = list(dict.fromkeys(tickers))
companies.extend(tickers)
company = st.selectbox( ### can select tickers and company name for individual company chart
    'Which company/stock code are you interested in?',
      companies)
'You selected: ', company

if type(company) == int: ## if input is a ticker
    company = df.loc[df['Stock Code'] == company, 'Stock Name'] 
    company = company.iloc[0]

else:
    pass  

### function that appends average trading days column to df given number of days in a list and respective column
def average_trading (df2, trading_days, column_of_interest):
    #input dataframe that includes a column named "column_of_interest"(str) that includes respective data (df), number of observations to average (int)
    #output, dataframe with calculated volume data (df)
    df_vol = df2 [column_of_interest]
    df3 = df_vol.rolling(trading_days, min_periods=trading_days).mean() ### this function is key to calculating trading days
    df3 = df3.rename("Average " + str (trading_days) + " Trading Days "+ column_of_interest)
    df2 = pd.concat ([df2, df3], axis = 1)
    return df2

@st.cache(ttl= 1800, allow_output_mutation=True) ## input holds for 30 mins before getting refreshed
def chart_1 (company, df):
    ticker = df.loc[df['Stock Name'] == company]
    ticker = ticker ['Yf Ticker']
    ticker = list (ticker )
    ticker = ticker [0]
    
    # download and calculate data for chart 1
    df2 = yf.download(ticker, period = 'max')   
    
    # visualize chart 1
    fig = make_subplots(specs=[[{"secondary_y": True}]])
        # Add traces
    fig.add_trace(go.Scatter(x= df2.index, y= df2 ['Adj Close'], name= 'Adjusted Close' ),
        secondary_y=False)
    
    trading_days = [20, 40, 60] ### trading days that are being calculated
    for day in trading_days:
        df2 = average_trading(df2, day, 'Volume')
        fig.add_trace(go.Scatter(x = df2.index, y= df2['Average '+str (day) +' Trading Days Volume'], name= 'Average '+str (day) +' Trading Days Volume'),
                      secondary_y=True)
        # Add figure title
    fig.update_layout(title_text= company + ' Price and Average Volume Chart')
        # Set x-axis title
    fig.update_xaxes(title_text="Date")
        # Set y-axes titles
    fig.update_yaxes(title_text= 'Adjusted Closing Price', secondary_y=False)
    fig.update_yaxes(title_text="Volume", secondary_y=True)
    return fig

fig = chart_1(company, df)
st.plotly_chart(fig, use_container_width=True)

### filter data by industry using dropdown box
industries = df['Industry']
industries = industries.tolist()
industries = list(dict.fromkeys(industries))
 # healthcare = sectors [3]
industries.append('All')### adds an option for All IPOs
try:
    industries.remove ('Biotechnology')
    industries.append('Biotechnology') 
except ValueError:
    pass
industries = industries [::-1]
industry = st.selectbox(
    'Which Industry are you interested in?',
      industries)
'You selected: ', industry

if industry == 'All':
    pass
else:
    df = df.loc[df['Industry'] == industry]

tickers = df['Yf Ticker']
tickers = tickers.to_list()

@st.cache(ttl= 1800, allow_output_mutation=True) ## input holds for 30 mins before getting refreshed
def download(tickers):
    data = yf.download(tickers)
    return data
data = download(tickers)

def to_market(x, column, data2):
    if pd.isna(x):
        return 0
    return data2[data2["Yf Ticker"] == column]["Mkt Cap (Jul 8)"].values[0]

def homemade_index(data, df, datatype):   
    ### input data and df
    ### output a dataframe showing the homemade index value###    
    
    # adjust yf downloaded data so it matches data.xlsx format
    Adj_Close2 = data [datatype]
    Adj_Close2 = Adj_Close2.replace(to_replace=0,method='ffill')
    columns = Adj_Close2.columns
    columns = columns.to_list()
    columns = columns
    df8 = []
    df8.append(columns)
    
    df9 = [np.nan] *len(columns)
    df8.append(df9)
    
    df10 = pd.DataFrame(data = df8, columns = columns)
    df2 = pd.concat([df10, Adj_Close2], ignore_index=False, axis = 0)
    #### 
    
    Adj_Close = df2
    
    Adj_Close = Adj_Close
    data1_index = Adj_Close.index[2:]
    data1_columns = Adj_Close.iloc[0]
    Adj_Close = pd.DataFrame(Adj_Close.iloc[2:, :].values, index=data1_index, columns=data1_columns)
    Adj_Close_return = Adj_Close.pct_change()
    Volume = df
    market = Adj_Close.copy()
    for column in market.columns:
        market[column] = market[column].apply(to_market, column=column, data2=Volume)
    market_sum = market.sum(axis=1)
    weight = market.div(market_sum.values, axis=0)
    Homemade_Index_Return = pd.DataFrame(index=weight.index, columns=["Homemade_Index_Return"])
    Adj_Close_return.fillna(0, inplace=True)
    for index, series in Adj_Close_return.iterrows():
        #     print(index)
        #     print(series.values)
        Homemade_Index_Return.loc[index, "Homemade_Index_Return"] = \
        np.matmul(series.values, weight.loc[index, :].values.reshape(-1, 1))[0]
    Homemade_Index_Return = Homemade_Index_Return + 1
    Homemade_Index_Return.iloc[0, 0] = 100
    Homemade_Index_Return = Homemade_Index_Return.cumprod()
    Homemade_Index_Return = Homemade_Index_Return.astype(float)
    return Homemade_Index_Return

@st.cache(ttl= 1800, allow_output_mutation=True) ## input holds for 30 mins before getting refreshed
def chart_2 (df, data):
    # download and calculate data for chart 2
    df2 = homemade_index(data, df, 'Adj Close')
    
    # visualize chart 2
    fig = make_subplots(specs=[[{"secondary_y": True}]])
        # Add traces
    fig.add_trace(go.Scatter(x= df2.index, y= df2 ['Homemade_Index_Return'], name= 'Adjusted Close' ),
        secondary_y=False)
    
    df2 = homemade_index(data, df, 'Volume')
    trading_days = [20, 40, 60] ### trading days that are being calculated
    for day in trading_days:
        df2 = average_trading(df2, day, 'Homemade_Index_Return')
        fig.add_trace(go.Scatter(x = df2.index, y= df2['Average '+str (day) +' Trading Days Homemade_Index_Return'], name= 'Average '+str (day) +' Trading Days Volume'),
                      secondary_y=True)
        # Add figure title
    fig.update_layout(title_text= industry + ' Homemade Index Price and Average Volume Chart')
        # Set x-axis title
    fig.update_xaxes(title_text="Date")
        # Set y-axes titles
    fig.update_yaxes(title_text= 'Adjusted Closing Price Index', secondary_y=False)
    fig.update_yaxes(title_text="Volume Index", secondary_y=True)
    return fig
fig = chart_2(df, data)
st.plotly_chart(fig, use_container_width=True)

#### mkt cap slider
## lower and higher end of market cap, need to adjust units into maybe 100M or B HKD
df ['Mkt Cap (Jul 8) 100M'] = df ['Mkt Cap (Jul 8)']/ 100000000
df['Mkt Cap (Jul 8) 100M'] = df['Mkt Cap (Jul 8) 100M'].astype(float)

min_mktcap = df ['Mkt Cap (Jul 8) 100M'].min()
max_mktcap = df ['Mkt Cap (Jul 8) 100M'].max()

## the slider and selecting relevant data
slider = st.slider('Select Market Cap in 100M', min_value=min_mktcap, value=(float(min_mktcap),float(max_mktcap)), max_value=max_mktcap)
lower_mktcap = slider [0]
upper_mktcap = slider [1]

## info bar showing selected market caps
st.info('Lower: **' + str(lower_mktcap) + '** Higher: **' + str(upper_mktcap) +'**') ### info bar

## filter data by  market cap
df = df[(df['Mkt Cap (Jul 8) 100M'] >= lower_mktcap) & (df['Mkt Cap (Jul 8) 100M'] <= upper_mktcap)] ### filter the data

### filter downloaded data
tickers = df ['Yf Ticker']
tickers = tickers.to_list()
data = data.loc[:, (['Adj Close', 'Volume'], tickers)]

### display df with filtered data and appropriate data
df2  = data ['Volume'] ### this could be referenced with the dataset used for homemade_index()
df3 = df [['Yf Ticker', 'Stock Name', 'Stock Name CN', 'Mkt Cap (Jul 8) 100M']]

df88 = []
for ticker in tickers:
    df8 = [ticker]
    trading_days = [20,40,60]
    for day in trading_days:
        df4 = df2 [ticker]
        df5 = df4.iloc[-day:]
        df5 = df5.mean()
        df8.append(df5)
    df88.append (df8)
columns = ['Yf Ticker', '20 TD Avg Vol', '40 TD Avg Vol', '60 TD Avg Vol']
df88 = pd.DataFrame(df88, columns = columns)
df3 = df3.merge(df88, left_on='Yf Ticker', right_on='Yf Ticker')
df3 

### Chart 3: same charting excerise with homemade index and display
@st.cache(ttl= 1800, allow_output_mutation=True) ## input holds for 30 mins before getting refreshed
def chart_3 (df, data):
    # download and calculate data for chart 3
    df2 = homemade_index(data, df, 'Adj Close')
    
    # visualize chart 3
    fig = make_subplots(specs=[[{"secondary_y": True}]])
        # Add traces
    fig.add_trace(go.Scatter(x= df2.index, y= df2 ['Homemade_Index_Return'], name= 'Adjusted Close' ),
        secondary_y=False)
    
    df2 = homemade_index(data, df, 'Volume')
    trading_days = [20, 40, 60] ### trading days that are being calculated
    for day in trading_days:
        df2 = average_trading(df2, day, 'Homemade_Index_Return')
        fig.add_trace(go.Scatter(x = df2.index, y= df2['Average '+str (day) +' Trading Days Homemade_Index_Return'], name= 'Average '+str (day) +' Trading Days Volume'),
                      secondary_y=True)
        # Add figure title
    fig.update_layout(title_text= industry + ' '+ str(lower_mktcap) + ' - ' + str(upper_mktcap) + ' 100M HKD Mkt Cap Homemade Index Price and Average Volume Chart')
        # Set x-axis title
    fig.update_xaxes(title_text="Date")
        # Set y-axes titles
    fig.update_yaxes(title_text= 'Adjusted Closing Price Index', secondary_y=False)
    fig.update_yaxes(title_text="Volume Index", secondary_y=True)
    return fig
fig = chart_3(df, data)
st.plotly_chart(fig, use_container_width=True)
