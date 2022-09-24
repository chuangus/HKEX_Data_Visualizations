# -*- coding: utf-8 -*-
"""
Created on Tue Sep  7 14:21:28 2021

@author: angus
"""
import streamlit as st
import pandas as pd
import plotly.figure_factory as ff
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import numpy as np
import investpy
import base64
import yfinance as yf
import datetime as dt
from io import BytesIO

st.set_page_config(layout="wide")

st.title('HKEX IPO Performance')
st.write ('All assumptions and further info can be found in [documentation](https://github.com/epiphronquant/HKEX-IPO-app)')

@st.cache(ttl= 1800) ## Data would need to get reloaded every 30 minutes
def load_data(link):
    df = pd.read_excel(link)
    return df
link = r'https://github.com/chuangus/HKEX-IPO-app/blob/main/RawData.xlsx?raw=true'
df = load_data(link)


df_export = df
df = df.loc[df['Count as IPO?'] == 1] ### Filters rows where it is actually an IPO
df['Listing Date▼']= pd.to_datetime(df['Listing Date▼'])### converts listing date to datetime variable

### create dropdown selector
column_1, column_2, column_3 = st.columns(3) ### Divides page into 2 columns
with column_1:
    language = st.selectbox(
        'Which language should the company names be?',
          ['English', '中文'])
    'You selected: ', language
    if language =='中文':
        df['Name'] = df['Name CN']
    else:
        pass
sectors = df['Sector']
sectors = sectors.tolist()
sectors = list(dict.fromkeys(sectors))
healthcare = sectors [0]
sectors.append('All')### adds an option for All IPOs
try:
    sectors = sorted(sectors [1:])
except TypeError:
    st.write ('**Please contact administrator angus.chu100@gmail.com to manually update Sector and Industry Data.**')
    sectors = sorted(sectors [1:])
    
sectors.insert(0, healthcare)
with column_2:### Chart of distribution and Lead 1 Chart
    
    sector = st.selectbox(
        'Which sector are you interested in?',
          sectors)
    'You selected: ', sector
    if sector == 'All':
        df = df[(df['Listing Date▼'] >= '2019-01-01')] ### healthcare data runs from 2018 while all IPO data runs from 2019
    else:
        df = df.loc[df['Sector'] == sector]

with column_3:
    ### Dropdown box for median or mean
    central_tendancy = ['Average', 'Median']
    select_central = st.selectbox(
        'Average or Median?',
          central_tendancy)
    'You selected: ', select_central
### add a slider to filter data by dates
format = 'MMM DD, YYYY'  # format output
start_date = df ['Listing Date▼'].iloc [0]
start_date = start_date.date()
end_date = df ['Listing Date▼'].iloc [-1]
end_date = end_date.date()

slider = st.slider('Select date', min_value=start_date, value=(start_date,end_date) ,max_value=end_date, format=format)
start_date = slider [0].strftime('%Y%m%d')
end_date = slider [1].strftime('%Y%m%d')

def clean_time (date): ### presents selected slider time in the same format as the slider
    a = date.ctime()
    a = a.split()
    a = a[1] + ' '+ a[2] + ', '+ a[-1]
    return a
st.info('Start: **%s** End: **%s**' % (clean_time(slider[0]),clean_time(slider[1]))) ### info bar
df = df[(df['Listing Date▼'] >= start_date) & (df['Listing Date▼'] <= end_date)] ### filter the data

### create charts
def lead_chart(x, y1, y2, title):
    fig = go.Figure(
            data=[go.Bar(name='Count', x=x, y=y1, yaxis='y', offsetgroup=1),
                go.Bar(name='% Chg Debut', x=x, y=y2, yaxis='y2', offsetgroup=2)],
            layout={'yaxis': {'title': 'Count'},
                'yaxis2': {'title': '% Chg Debut', 'overlaying': 'y', 'side': 'right', 'tickformat': ',.0%'}})
    fig.update_layout(barmode='group',title={'text': title})
    fig.update_xaxes(categoryorder='max descending')
    return fig

### Charts for normal distribution, industry performance, lead 1, lead 2
column_1, column_2 = st.columns(2) ### Divides page into 2 columns
with column_1:### Chart of distribution and Lead 1 Chart
    ### Chart of distribution    
    x1 = df ['% Chg. on2Debut▼'] 
    x1 = x1.tolist()
    x1 = [x1]
    label = '% Chg. on Debut'
    label = [label]
    names = df['Name']
    names = names.tolist()
    names = [names]
    
    fig = ff.create_distplot(x1, label, rug_text = names, bin_size = .2)
    fig.update_layout(  xaxis_tickformat = ',.2%',title={'text': "Normal Distribution Plot and Rugplot for First Day Return"})
    st.plotly_chart(fig)    

    #### Lead 1 Chart
    lead1 = df [['% Chg. on2Debut▼', 'Industry', 'Name', 'Lead 1', 'Listing Date▼']]
    a = lead1.groupby(['Lead 1']).count() ### gathers data by Lead 1
    industries = a.index
    industries = industries.tolist()
    
    a = a['% Chg. on2Debut▼'] ### data column that shows deal count
    a = a.rename('Count')
    a  = a.to_list()
    if select_central == 'Average':
        b = lead1.groupby(['Lead 1']).mean()
    
    else:
        b = lead1.groupby(['Lead 1']).median()
    b = b['% Chg. on2Debut▼'].to_list()
    fig = lead_chart(industries, a, b,"Lead 1 Deal Count and " + select_central + " First Day Return" )
    st.plotly_chart(fig)

with column_2:
    ### chart of industry performance and Lead 2 Chart
    industry = df [['% Chg. on2Debut▼', 'Industry', 'Name', 'Listing Date▼']]
    
    a = industry.groupby(['Industry']).count()
    industries = a.index
    industries = industries.tolist()
    
    a = a['% Chg. on2Debut▼']
    a = a.rename('Count')
    a  = a.to_list()
    if select_central == 'Average':
        b = industry.groupby(['Industry']).mean()
    
    else:
        b = industry.groupby(['Industry']).median()
    b = b['% Chg. on2Debut▼'].to_list()
    
    fig = go.Figure(
        data=[
            go.Bar(name='Count', x=industries, y=a, yaxis='y', offsetgroup=1),
            go.Bar(name='% Chg Debut', x=industries, y=b, yaxis='y2', offsetgroup=2)],
        layout={
            'yaxis': {'title': 'Count'},
            'yaxis2': {'title': '% Chg Debut', 'overlaying': 'y', 'side': 'right', 'tickformat': ',.0%'}
        })
    fig.update_layout(barmode='group',legend=dict(yanchor="top",y=1,xanchor="right",x=1.35),
                      title={'text': "Industry Deal Count and " + select_central + " First Day Return"})
    fig.update_xaxes(categoryorder='max descending')
    st.plotly_chart(fig)
    
    #### Lead 2 Chart
    lead2 = df [['% Chg. on2Debut▼', 'Industry', 'Name', 'Lead 2', 'Listing Date▼']]
    a = lead2.groupby(['Lead 2']).count()
    industries = a.index
    industries = industries.tolist()
    a = a['% Chg. on2Debut▼']
    a = a.rename('Count')
    a  = a.to_list()
    if select_central == 'Average':
        b = lead2.groupby(['Lead 2']).mean()
    
    else:
        b = lead2.groupby(['Lead 2']).median()
    b = b['% Chg. on2Debut▼'].to_list()
    
    fig = lead_chart(industries, a, b,"Lead 2 Deal Count and " + select_central+ " First Day Return" )
    st.plotly_chart(fig)
### Charts for Lead 1&2 Performance
#### combine lead 1 with lead 2
lead12 = df [['% Chg. on2Debut▼', 'Industry', 'Name','Lead 1', 'Lead 2', 'Listing Date▼']]
lead12 ['Lead 1 & 2'] = df ['Lead 1'] + ' & ' + df['Lead 2']
a = lead12.groupby(['Lead 1 & 2']).count()
industries = a.index
industries = industries.tolist()
a = a['% Chg. on2Debut▼']
a = a.rename('Count')
a  = a.to_list()
if select_central == 'Average':
    b = lead12.groupby(['Lead 1 & 2']).mean()

else:
    b = lead12.groupby(['Lead 1 & 2']).median()
# b = lead12.groupby(['Lead 1 & 2']).mean()
b = b['% Chg. on2Debut▼'].to_list()
### graph
fig = lead_chart(industries, a, b,"Lead 1 & 2 Deal Count and "+ select_central+" First Day Return" )
st.plotly_chart(fig, use_container_width=True)

column_1, column_2 = st.columns(2) ### Divides page into 2 columns
with column_1:
    ### Chart showing first day return performance over time with HSH and HSI
        #add a box to select Chg on debut or -1 trading day as primary axis
    ret = st.selectbox(
        'Which return would you like to analyse?',
          ['Chg on Debut', 'Return till Today'])
    'You selected: ', ret
    
    if ret == 'Chg on Debut':
        fdayret = df [['Listing Date▼','% Chg. on2Debut▼']]
    else:
        fdayret = df [['Listing Date▼','-1 Trading Days']]
    
    
    # fdayret = df [['Listing Date▼','% Chg. on2Debut▼']]
    if select_central == 'Average':
        a = fdayret.groupby(['Listing Date▼']).mean()
    
    else:
        a = fdayret.groupby(['Listing Date▼']).median()
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
with column_2:
        #add a box to select HSI or HSH as second axis
    index = st.selectbox(
        'Which index would you like to compare it to?',
          ['Hang Seng Healthcare', 'Hang Seng Index'])
    'You selected: ', index

### Download HSH and HSI data
today = pd.to_datetime('today').strftime('%d/%m/%Y')
start = a.index[0].strftime('%d/%m/%Y')
end = a.index[-1].strftime('%d/%m/%Y')
if index == 'Hang Seng Index':
    df_index = investpy.get_index_historical_data(index='Hang Seng',
                                        country='hong kong',
                                        from_date= start,
                                        to_date= end)
else:
    df_index = investpy.get_index_historical_data(index='hs healthcare',
                                            country='hong kong',
                                            from_date= start,
                                            to_date= end)
# Add traces
if ret == 'Chg on Debut':
    fig.add_trace(go.Scatter(x= a.index, y= a['% Chg. on2Debut▼'], name= ret),
        secondary_y=False)
else:
    # fdayret = df [['Listing Date▼','-1 HSI Days']]
    fig.add_trace(go.Scatter(x= a.index, y= a['-1 Trading Days'], name= ret),
        secondary_y=False)

fig.add_trace(go.Scatter(x = df_index.index, y= df_index['Close'], name= index),
    secondary_y=True)
# Add figure title
fig.update_layout(title_text= ret + " with Index Level")

# Set x-axis title
fig.update_xaxes(title_text="Date")

# Set y-axes titles
fig.update_yaxes(title_text= ret, secondary_y=False)
fig.update_yaxes(title_text="Index Level", secondary_y=True)
fig.layout.yaxis.tickformat= ',.2%'
# fig.show()
st.plotly_chart(fig, use_container_width=True)

#### trading performance's chart
column_1, column_2 = st.columns(2) ### Divides page into 2 columns
with column_1:
    last_x = st.number_input('Number of most recent IPOs to display', value = 10)
    last_x = int(last_x)
    @st.cache(ttl = 1800)
    def chart_7(df):
        ### add chart showing last 10 IPOs and their detailed trading performances
        ## gather the last 10 tickers and stock names and listing date and price
        df_10 = df [-last_x:]
        df_10 = df_10 [['Name', 'Code', 'Listing Price', 'Listing Date▼']]
        ## Gather stock codes and tickers
        df_yf = df_10 ['Code']
        df_tickers = df_yf.tolist()
        df_yf = yf.download(df_tickers)
        df_yf = df_yf ['Close']
        df_yf = df_yf [df_tickers] ## reorder the columns so it is in the order as inputted
        
        df_name = df_10 ['Name']
        df_name = df_name.tolist()
        df_yf.columns = df_name ## rename the column codes to column names
        
        df_yf8 = pd.DataFrame()
        for name in df_name:
            df_yf2 = df_yf [name]
            df_yf2 = df_yf2.dropna()
            
            list_date = df_10.loc [df_10['Name'] == name]
            list_date = list_date ['Listing Date▼'].values
            list_date = list_date [0]
            
            df_yf2 = df_yf2.reset_index()
            
            df_yf2 = df_yf2[(df_yf2['Date'] >= list_date)]
            
            df_yf2 = df_yf2.set_index('Date')
            df_yf2=df_yf2.iloc[:,0]
            
            price = df_10.loc [df_10['Name'] == name]
            price = price ['Listing Price'].values
            price = price [0]
            
            df_yf2 = df_yf2 / price -1 
            date = df_yf2.index [0]
            
            date = date - dt.timedelta(days=1)
            
            ser = pd.Series(data= {date : 0}, index=[date], name = 'Stock Name')# df_yf2 = df_yf2.append()
            
            ser = ser.append(df_yf2)
            
            ser = pd.DataFrame(ser, columns = ['Close'])
            ser ['Stock Name'] = name
            
            df_yf8 = df_yf8.append(ser)
        df_yf8 = df_yf8.reset_index()
        df_yf8 = df_yf8.rename({'index':'Date', 'Close':'Return'}, axis = 'columns')
        markers = df_yf8 ['Date'].min() ### display of markers settings
        markers = markers.date()
        markers = markers > dt.date.today() - dt.timedelta(days=120) 
        return df_yf8, markers
    df_yf8, markers = chart_7(df)
    fig = px.line(df_yf8, x= 'Date', y= 'Return', color = 'Stock Name', title= 'Last ' + str(last_x)+' '  + sector + ' IPOs Return Post IPO', markers = markers) 
    fig.layout.yaxis.tickformat = ',.0%'
    st.plotly_chart(fig)
with column_2:
    ### customizable chart for displaying various IPOs
    names = st.text_input('Type in names of stock/stocks that have IPOd in the past 3 years. e.g TRANSCENTA-B, bioheart-b')    
    @st.cache(ttl = 1800)
    def chart_8(names):
        names = names.split(',')
        names = map(str.strip, names)
        names = map(str.upper, names)
        names = list(names)
        
        tickers = []
        for name in names:
            # name = 'SENSETIME-W'
            ticker = df.loc [df['Name'] == name]
            ticker = ticker ['Code'].values
            ticker = ticker [0]
            tickers.append(ticker)
        
        df_yf = yf.download(tickers) ['Close']
        if len(tickers) ==1:
            df_yf = df_yf.rename(names[0])
        else:
            df_yf = df_yf [tickers] ## reorder the columns so it is in the order as inputted
        
        df_yf.columns = names ## rename the column codes to column names
        df_yf8 = pd.DataFrame()
        for name in names:
            if len(tickers) ==1:
                df_yf2 = df_yf
            else:
                df_yf2 = df_yf [name] ## reorder the columns so it is in the order as inputted
            
            df_yf2 = df_yf2.dropna()
            
            list_date = df.loc [df['Name'] == name]
            list_date = list_date ['Listing Date▼'].values
            list_date = list_date [0]
            
            df_yf2 = df_yf2.reset_index()
            
            df_yf2 = df_yf2[(df_yf2['Date'] >= list_date)]
            
            df_yf2 = df_yf2.set_index('Date')
            df_yf2=df_yf2.iloc[:,0]
            
            price = df.loc [df['Name'] == name]
            price = price ['Listing Price'].values
            price = price [0]
            
            df_yf2 = df_yf2 / price -1 
            date = df_yf2.index [0]
            
            date = date - dt.timedelta(days=1)
            
            ser = pd.Series(data= {date : 0}, index=[date], name = 'Stock Name')# df_yf2 = df_yf2.append()
            
            ser = ser.append(df_yf2)
            
            ser = pd.DataFrame(ser, columns = ['Close'])
            ser ['Stock Name'] = name
            
            df_yf8 = df_yf8.append(ser)
        df_yf8 = df_yf8.reset_index()
        df_yf8 = df_yf8.rename({'index':'Date', 'Close':'Return'}, axis = 'columns')
        
        markers = df_yf8 ['Date'].min() ### display of markers settings
        markers = markers.date()
        markers = markers > dt.date.today() - dt.timedelta(days=120)    
        return df_yf8, markers        
    if names == '':
        pass
    else: 
        df_yf8, markers = chart_8(names)
        fig = px.line(df_yf8, x= 'Date', y= 'Return', color = 'Stock Name', title= 'Selected '+sector + ' IPOs Return Post IPO', markers = markers)        
        fig.layout.yaxis.tickformat = ',.0%'
        st.plotly_chart(fig)

### Charts for Trading Day return by benchmark and by industry
###### to better display the data, 480 trading days is used as the return till today
st.subheader ('480 Trading Days post IPO is used as a placeholder for the return till Today') 

column_1, column_2 = st.columns(2) ### Divides page into 2 columns
with column_1: ### trading day performance compared to HSI and HSH
    ### gather the data columns
    comps = df [["0 Trading Days",	"80 Trading Days",	"100 Trading Days",	"120 Trading Days",	"140 Trading Days",	"160 Trading Days",	"252 Trading Days",	"372 Trading Days",	"-1 Trading Days"]]
    compsHSI = df[["80 HSI Days",	"100 HSI Days",	"120 HSI Days",	"140 HSI Days",	"160 HSI Days",	"252 HSI Days",	"372 HSI Days","-1 HSI Days"
    ]]
    compsHSH = df [["80 HSH Days",	"100 HSH Days",	"120 HSH Days",	"140 HSH Days",	"160 HSH Days",	"252 HSH Days",	"372 HSH Days","-1 HSH Days"]]
    ### find central tendancy using selected option
    if select_central == 'Average':
        comps = comps.mean()
        compsHSI = compsHSI.mean()
        compsHSH = compsHSH.mean()
    else:
        comps = comps.median()
        compsHSI = compsHSI.median()
        compsHSH = compsHSH.median()
    ### add 0's for compsHSI and compsHSH because there is only data for market close on the day
    a = pd.Series(data = [0], index = ['0 HSI Days'])
    compsHSI = a.append(compsHSI)
    
    a = pd.Series(data = [0], index = ['0 HSH Days'])
    compsHSH = a.append(compsHSH)
    ## Convert the numerous series to one dataframe that has multiple columns
    def clean_comps(comps):
        comps = comps.to_frame()
        comps = comps.reset_index()
        comps2 = comps ['index']
        comps2 = comps2.str.split(expand = True)
        comps ['Trading Days since IPO'] = comps2.iloc [:,0:1]
        comps3 = comps2[comps2.columns[1]] +' '+ comps2[comps2.columns[2]]
        comps ['Benchmark'] = comps3
        return comps
    comps = clean_comps(comps)
    comps = comps.append(clean_comps(compsHSI))
    comps = comps.append(clean_comps(compsHSH))
    ### clean the dataframe
    comps ['Trading Days since IPO'] = pd.to_numeric(comps ['Trading Days since IPO'])
    comps = comps.rename( columns = {comps.columns[1]: 'return'})
    comps['Trading Days since IPO'] = comps ['Trading Days since IPO'].replace (-1, 480)
    ### Graph it onto a chart
    fig = px.line(comps, x= 'Trading Days since IPO', y= 'return', color = 'Benchmark', title= select_central + ' Trading Day Return Post IPO by Benchmark', markers = True)
    fig.layout.yaxis.tickformat = ',.0%'
    st.plotly_chart(fig)

with column_2:### trading day performance by industry
    ### gather the data columns
    comps = df [['Industry',"0 Trading Days",	"80 Trading Days",	"100 Trading Days",	"120 Trading Days",	"140 Trading Days",	"160 Trading Days",	"252 Trading Days",	"372 Trading Days",	"-1 Trading Days"]]
    compsHSI = df[['Industry',"80 HSI Days",	"100 HSI Days",	"120 HSI Days",	"140 HSI Days",	"160 HSI Days",	"252 HSI Days",	"372 HSI Days","-1 HSI Days"
    ]]
    compsHSH = df [['Industry',"80 HSH Days",	"100 HSH Days",	"120 HSH Days",	"140 HSH Days",	"160 HSH Days",	"252 HSH Days",	"372 HSH Days","-1 HSH Days"]] 
    ### for selected option, calculate the central tendancy
    if select_central == 'Average':
        comps = comps.groupby(['Industry']).mean()
    
    else:
        comps = comps.groupby(['Industry']).median()
    comps = comps.reset_index()
    industries = comps['Industry']
    
    comps1 = pd.DataFrame() ### initialize an empty dataframe to add data on it later
    for industry in industries:
        a = comps.loc[comps['Industry'] == industry]
        a = a.transpose()
        b = a.iloc [1:]
        a = a.iloc [0]
        b = b.squeeze()
        b = clean_comps(b)
        b = b.drop(['index', 'Benchmark'], axis = 1)
        a = a.iloc[np.arange(len(a)).repeat(len(b.index))]
        a = a.to_frame()
        a = a.reset_index(drop=True)
        c = pd.concat([a,b], axis = 1)
        c = c.rename( columns = {c.columns[1]: 'return'})
    
        comps1 = comps1.append(c)
    comps1 ['Trading Days since IPO'] = pd.to_numeric(comps1 ['Trading Days since IPO'])
    comps1['Trading Days since IPO'] = comps1 ['Trading Days since IPO'].replace (-1, 480) ### replacing return till today with 480
    comps1 ['return'] = pd.to_numeric(comps1 ['return'])
    ### graph
    fig = px.line(comps1, x= 'Trading Days since IPO', y= 'return', color = 'Industry', title= select_central + ' Trading Day Return Post IPO by Industry', markers = True)
    fig.layout.yaxis.tickformat = ',.0%'
    st.plotly_chart(fig)

### display raw data below
st.header ('Data Used for Graph')

    ### Download data
def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1', index = False)
    writer.save()
    processed_data = output.getvalue()
    return processed_data
def get_table_download_link(df):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    val = to_excel(df)
    b64 = base64.b64encode(val)  # val looks like b'...'
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="extract.xlsx">Download Data file</a>' # decode b'abc' => abc
st.markdown(get_table_download_link(df_export), unsafe_allow_html=True)

df2 = df [['Listing Date▼', '% Chg. on2Debut▼', 'Name', 'Industry', 'Lead 1', 'Lead 2']] ### gathers relevant data
df2 ['Listing Date▼'] = df ['Listing Date▼'].dt.strftime('%Y-%m-%d')
df2 = df2.set_index('Listing Date▼')
df2 = df2.rename(columns={'% Chg. on2Debut▼': 'Chg.Debut'})
s = df2.style.format({
    'Chg.Debut': '{:,.2%}'.format})
s

df2 = df [['Listing Date▼', 'Name',"0 Trading Days",	"80 Trading Days",	"100 Trading Days",	"120 Trading Days", "-1 Trading Days" ]] ### gathers relevant data
df2 ['Listing Date▼'] = df ['Listing Date▼'].dt.strftime('%Y-%m-%d')
df2 = df2.set_index('Listing Date▼')
df2 = df2.rename(columns={'% Chg. on2Debut▼': 'Chg.Debut'})
s = df2.style.format(formatter = {"0 Trading Days":'{:,.2%}'.format,
                                  "80 Trading Days":'{:,.2%}'.format,
                                  "100 Trading Days":'{:,.2%}'.format,
                                  "120 Trading Days":'{:,.2%}'.format,
                                  "-1 Trading Days":'{:,.2%}'.format
                                  })
s
#### to gather details of a company
comapnies = df2 ['Name']
company = st.selectbox(
    'Which company do you want to know more about?',
      comapnies)
'You selected: ', company
summary = df.loc[df['Name'] == company]
summary = summary ['Business Summary']
summary = summary.iloc [0]
summary
