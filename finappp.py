# -*- coding: utf-8 -*-
###############################################################################
# FINANCIAL DASHBOARD EXAMPLE - v3
###############################################################################

#==============================================================================
# Initiating
#==============================================================================

# Libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from datetime import datetime, timedelta
import yfinance as yf
import streamlit as st
#==============================================================================
# HOT FIX FOR YFINANCE .INFO METHOD
# Ref: https://github.com/ranaroussi/yfinance/issues/1729
#==============================================================================

import requests
import urllib

class YFinance:
    user_agent_key = "User-Agent"
    user_agent_value = ("Mozilla/5.0 (Windows NT 6.1; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/58.0.3029.110 Safari/537.36")
    
    def __init__(self, ticker):
        self.yahoo_ticker = ticker

    def __str__(self):
        return self.yahoo_ticker

    def _get_yahoo_cookie(self):
        cookie = None

        headers = {self.user_agent_key: self.user_agent_value}
        response = requests.get("https://fc.yahoo.com",
                                headers=headers,
                                allow_redirects=True)

        if not response.cookies:
            raise Exception("Failed to obtain Yahoo auth cookie.")

        cookie = list(response.cookies)[0]

        return cookie

    def _get_yahoo_crumb(self, cookie):
        crumb = None

        headers = {self.user_agent_key: self.user_agent_value}

        crumb_response = requests.get(
            "https://query1.finance.yahoo.com/v1/test/getcrumb",
            headers=headers,
            cookies={cookie.name: cookie.value},
            allow_redirects=True,
        )
        crumb = crumb_response.text

        if crumb is None:
            raise Exception("Failed to retrieve Yahoo crumb.")

        return crumb

    @property
    def info(self):
        # Yahoo modules doc informations :
        # https://cryptocointracker.com/yahoo-finance/yahoo-finance-api
        cookie = self._get_yahoo_cookie()
        crumb = self._get_yahoo_crumb(cookie)
        info = {}
        ret = {}

        headers = {self.user_agent_key: self.user_agent_value}

        yahoo_modules = ("assetProfile,"  # longBusinessSummary
                         "summaryDetail,"
                         "financialData,"
                         "indexTrend,"
                         "defaultKeyStatistics")

        url = ("https://query1.finance.yahoo.com/v10/finance/"
               f"quoteSummary/{self.yahoo_ticker}"
               f"?modules={urllib.parse.quote_plus(yahoo_modules)}"
               f"&ssl=true&crumb={urllib.parse.quote_plus(crumb)}")

        info_response = requests.get(url,
                                     headers=headers,
                                     cookies={cookie.name: cookie.value},
                                     allow_redirects=True)

        info = info_response.json()
        info = info['quoteSummary']['result'][0]

        for mainKeys in info.keys():
            for key in info[mainKeys].keys():
                if isinstance(info[mainKeys][key], dict):
                    try:
                        ret[key] = info[mainKeys][key]['raw']
                    except (KeyError, TypeError):
                        pass
                else:
                    ret[key] = info[mainKeys][key]

        return ret

#==============================================================================
# Header
#==============================================================================

def render_header():
    """
    This function render the header of the dashboard with the following items:
        - Title
        - Dashboard description
        - 3 selection boxes to select: Ticker, Start Date, End Date
    """
    
    # Add dashboard title and description
    st.title("MY FINANCIAL DASHBOARD")
    st.header("Daya Ayala")
    col1, col2 = st.columns([1,5])
    col1.write("Data source:")
    

    # Add the ticker selection on the sidebar
    # Get the list of stock tickers from S&P500
    ticker_list = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]['Symbol']

    # Add the selection boxes
    col1, col2, col3 = st.columns(3)  # Create 3 columns
    # Ticker name
    global ticker  # Set this variable as global, so the functions in all of the tabs can read it
    ticker = col1.selectbox("Ticker", ticker_list)
    global my_var
    my_var = yf.Ticker(ticker)
    # Begin and end dates
    global start_date, end_date  # Set this variable as global, so all functions can read it
    start_date = col2.date_input("Start date", datetime.today().date() - timedelta(days=30))
    end_date = col3.date_input("End date", datetime.today().date())


#==============================================================================
# Tab 1
#==============================================================================

def render_tab1():
    """
    This function render the Tab 1 - Company Profile of the dashboard.
    """
    
       
    # Show the stock image
    col1, col2, col3 = st.columns([1, 3, 1])
    col2.image('./img/stock_market.jpg', use_column_width=True,
                caption='Company Stock Information')
    
    # Get the company information
    @st.cache_data
    def GetCompanyInfo(ticker):
        """
        This function get the company information from Yahoo Finance.
        """
        return YFinance(ticker).info
    
    # If the ticker is already selected
    if ticker != '':
        # Get the company information in list format
        info = GetCompanyInfo(ticker)

        # Show the company description using markdown + HTML
        st.write('**1. Business Summary:**')
        st.markdown('<div style="text-align: justify;">' + \
                    info['longBusinessSummary'] + \
                    '</div><br>',
                    unsafe_allow_html=True)
            
            
        #Get company profile
        st.write('**2. Company Profile:**')
        profile_keys = {'zip':'Zip Code',
                      'address1'          :'Address',
                      'country': 'Country',
                      'website'          :'Website',
                      'sector'    :'Sector',
                      'fullTimeEmployees'       :'fullTimeEmployees'}
        profile_dic = {}
        for i in profile_keys:
            profile_dic.update({profile_keys[i]:info[i]})
        profile_dic = pd.DataFrame({' ':pd.Series(profile_dic)}) 
        st.dataframe(profile_dic)
        st.write('Major Shareholders:')
        st.write(my_var.major_holders)
        st.write('Institutional Shareholders:')
        st.write(my_var.institutional_holders)
        
        # Show some statistics as a DataFrame
        st.write('**3. Key Statistics:**')
        info_keys = {'previousClose':'Previous Close',
                      'open'         :'Open',
                      'bid'          :'Bid',
                      'ask'          :'Ask',
                      'marketCap'    :'Market Cap',
                      'volume'       :'Volume'}
        company_stats = {}  # Dictionary
        for key in info_keys:
            company_stats.update({info_keys[key]:info[key]})
        company_stats = pd.DataFrame({'Value':pd.Series(company_stats)})  # Convert to DataFrame
        st.dataframe(company_stats)
        
        
        col4, col5, col6, col7, col8, col9, col10, col11 = st.columns(8)
        durations = ['1M', '3M', '6M', 'YTD', '1Y', '3Y', '5Y', 'MAX']
        selected_duration = col4.radio("Select Duration", durations, index=2)
        
        # Calculate start and end dates based on selected duration
        if selected_duration == '1M':
            start_date = datetime.today() - timedelta(days=30)
        elif selected_duration == '3M':
            start_date = datetime.today() - timedelta(days=90)
        elif selected_duration == '6M':
            start_date = datetime.today() - timedelta(days=180)
        elif selected_duration == 'YTD':
            start_date = datetime(datetime.today().year, 1, 1)
        elif selected_duration == '1Y':
            start_date = datetime.today() - timedelta(days=365)
        elif selected_duration == '3Y':
            start_date = datetime.today() - timedelta(days=3 * 365)
        elif selected_duration == '5Y':
            start_date = datetime.today() - timedelta(days=5 * 365)
        else:  # MAX
            start_date = datetime(1970, 1, 1)
            
        #Plotting the graph
        @st.cache_data
        def get_stock_data(ticker, start_date, end_date):
            stock_df = yf.Ticker(ticker).history(start=start_date, end=end_date)
            return stock_df
    
        if ticker != '':
            stock_price = get_stock_data(ticker, start_date, end_date)
            st.write('**Line Graph**')
            fig = go.Figure(data=[go.Scatter(
                x=stock_price.index,
                y=stock_price['Close'],
                mode='lines',
                name='Close Price'
            )])
            fig.update_xaxes(type='category')  # Use 'category' type for dates
            fig.update_layout(title=f'{ticker} Stock Price',
                              xaxis_title='Date',
                              yaxis_title='Price',
                              template='plotly_dark')
            st.plotly_chart(fig, use_container_width=True)
            
#==============================================================================
# Tab 2
#==============================================================================

def render_tab2():
    """
    This function renders Tab 2 - Chart of the dashboard.
    """
    
    # Button for different date styles
    selected_style = st.selectbox("Date Style:", ("Date range", "Time duration", "Time intervals"))

    
    col12, col13, col14, col15, col16, col17, col18, col19 = st.columns(8)
    col1, col2 = st.columns([1, 5])
    start_date = None
    end_date = datetime.today()

    # Depending on the style, display the buttons corresponding to it
    if selected_style == "Date range":
        start_date = col1.date_input("Start Date", datetime.today() - timedelta(days=365))
        end_date = col2.date_input("End Date", datetime.today())
    elif selected_style == "Time duration":
        durations1 = ['1M', '3M', '6M', 'YTD', '1Y', '3Y', '5Y', 'MAX']
        selected_duration = col14.radio("Select:", durations1, index=2)
        # Calculate start and end dates based on selected duration
        if selected_duration == '1M':
            start_date = datetime.today() - timedelta(days=30)
        elif selected_duration == '3M':
            start_date = datetime.today() - timedelta(days=90)
        elif selected_duration == '6M':
            start_date = datetime.today() - timedelta(days=180)
        elif selected_duration == 'YTD':
            start_date = datetime(datetime.today().year, 1, 1)
        elif selected_duration == '1Y':
            start_date = datetime.today() - timedelta(days=365)
        elif selected_duration == '3Y':
            start_date = datetime.today() - timedelta(days=3 * 365)
        elif selected_duration == '5Y':
            start_date = datetime.today() - timedelta(days=5 * 365)
        else:  # MAX
            start_date = datetime(1970, 1, 1)
    elif selected_style == "Time intervals":
        intervals = ['Day', 'Month', 'Year']
        selected_interval = col15.radio("Select Time Interval:", intervals, index=1)

        # Calculate start and end dates based on selected interval
        if selected_interval == 'Day':
            start_date = datetime.today() - timedelta(days=1)
        elif selected_interval == 'Month':
            start_date = datetime.today() - timedelta(days=30)
        elif selected_interval == 'Year':
            start_date = datetime.today() - timedelta(days=365)

    # Add a table to show stock data
    @st.cache_data
    def GetStockData(ticker, start_date, end_date):
        stock_df = yf.Ticker(ticker).history(start=start_date, end=end_date)
        stock_df.reset_index(inplace=True)  # Drop the indexes
        stock_df['Date'] = stock_df['Date']#.dt.date  # Convert date-time to date
        return stock_df

    # Add check boxes to show/hide data
    show_data = st.checkbox("Show data table")
    show_volume = st.checkbox("Show Trading Volume")
    show_sma = st.checkbox("Show Simple Moving Average (50 days)")

    if ticker != '':
        stock_price = GetStockData(ticker, start_date, end_date)
        if show_data:
            st.write('**Stock price data**')
            st.dataframe(stock_price, hide_index=True, use_container_width=True)

    update_button = st.button(" Update ")

    if update_button:
        # chart based on selection
        st.write('**Stock Price Chart**')
        fig = go.Figure()

        if show_volume:
            # Bar chart for trading volume
            fig.add_trace(go.Bar(x=stock_price['Date'], y=stock_price['Volume'], name='Volume'))

        if show_sma:
            stock_price['SMA'] = stock_price['Close'].rolling(window=50).mean()
            # Line plot for simple moving average
            fig.add_trace(go.Scatter(x=stock_price['Date'], y=stock_price['SMA'], mode='lines', name='SMA'))

        if selected_style != "Time intervals" or (selected_style == "Time intervals" and selected_interval == 'Day'):
            # Plot based on user-selected style
            if selected_style == "Date range":
                x_data = stock_price['Date']
            elif selected_style == "Time duration":
                x_data = stock_price['Date']
            elif selected_style == "Time intervals":
                x_data = stock_price['Date']
                ##THIS DOESNT WORK FOR THE TIME INTERVALS AND I HAVE NO CLUE WHY :'(
            if selected_style == "Date range" or selected_style == "Time duration" or selected_style == "Time intervals":
                # Line plot for stock price
                fig.add_trace(go.Scatter(x=x_data, y=stock_price['Close'], mode='lines', name='Stock Price'))
                # Candlestick chart
                fig.add_trace(go.Candlestick(x=x_data,
                                             open=stock_price['Open'],
                                             high=stock_price['High'],
                                             low=stock_price['Low'],
                                             close=stock_price['Close'], name='Candlestick'))
            
            
        # Customize the layout
        fig.update_xaxes(type='category')  
        fig.update_layout(title=f'{ticker} Stock Price',
                          xaxis_title='Date',
                          yaxis_title='Price',
                          template='plotly_dark')
        st.plotly_chart(fig, use_container_width=True)
    
    st.write("Click on the legend to select the type of graph!")
#==============================================================================
# Tab 3
#==============================================================================

def render_tab3():
    "This function renders the third tab- Financials of the Selected Company"
    #User input for either the time freq. or the financial statement required
    time_frequency = st.selectbox("Select Time Frequency:", ("Annual", "Quarterly"))
    sel = st.multiselect("Show:", ["Income statement", "Balance sheet", "Cash flow"])
      #Simply displays the appropriate financial statement depending on what the user chose
    if "Income statement" in sel:
        if time_frequency == "Quarterly":
            my_var.quarterly_income_stmt
        else:
            my_var.income_stmt
    if "Balance sheet" in sel:
        if time_frequency == "Quarterly":
            my_var.quarterly_balance_sheet
        else:
            my_var.balance_sheet
    if "Cash flow" in sel:
        if time_frequency == "Quarterly":
            my_var.quarterly_cash_flow
        else:
            my_var.cash_flow
   
#==============================================================================
# Tab 4
#==============================================================================

def render_tab4():
    """
    This function will render the fourth tab - the Monte Carlo Simulation
    """
    global start_date, end_date
    
    stock_price = my_var.history(start=start_date, end=end_date)
    close_price = stock_price['Close']
    daily_return = close_price.pct_change()
    daily_volatility = np.std(daily_return)
    
    # Setup the Monte Carlo simulation
    np.random.seed(123)
    simulations = st.slider("Pick a number of simulations:", 0, 1000)
    time_horizon = st.select_slider("Number of days:", [100, 150, 200, 250, 300])
    
    
    simulation_df = pd.DataFrame()
    
    for i in range(simulations):
        
        next_price = []
        
        # Create the next stock price
        last_price = close_price.iloc[-1]
        
        for j in range(time_horizon):
            # Generate the random percentage change around the mean (0) and std (daily_volatility)
            future_return = np.random.normal(0, daily_volatility)
    
            # Generate the random future price
            future_price = last_price * (1 + future_return)
    
            # Save the price and go next
            next_price.append(future_price)
            last_price = future_price
        
        # Store the result of the simulation
        next_price_df = pd.Series(next_price, name='sim' + str(i))
        simulation_df = pd.concat([simulation_df, next_price_df], axis=1)

    # Plot the simulation stock price in the future using Streamlit
    st.line_chart(simulation_df)

    #Graph for the last known stock price
    toggle = st.toggle("Show last known stock price")
    if toggle == 1:
       st.line_chart(close_price)
      
#==============================================================================
# Tab 5
#==============================================================================

def render_tab5():
    "This tab offers useful information about the selected company, for example the beta value and financial ratios"
    #beta value
    beta = YFinance(ticker).info['beta']
    st.write(str(ticker), "has a beta of:", beta)
    if beta == 1:
        st.write(str(ticker), "has the same volatility as the market.")
    elif beta < 1:
        st.write(str(ticker), "is a stable stock!")
    elif beta > 1:
        st.write(str(ticker), "is a risky stock- be careful.")
        
    inc =  my_var.income_stmt
    bal = my_var.balance_sheet
    
    #Following is the extraction of several different financial ratios
    #Liquidity ratio
    current_assets = bal.loc['Current Assets']
    current_liabilities = bal.loc['Current Liabilities']
    inventory = bal.loc['Inventory']
    #Asset Management
    cogs = inc.loc['Cost Of Revenue']
    accounts_receivable = bal.loc['Accounts Receivable']
    sales = inc.loc['Total Revenue']
    net_fixed_assets = bal.loc['Total Non Current Assets']
    total_assets = bal.loc['Total Assets']
    #Debt Management
    total_liabilities = bal.loc['Current Liabilities']
    ebit = inc.loc['EBIT']
    interest = inc.loc['Interest Expense']
    #Profitability ratio
    net_income = inc.loc['Net Income']
    common_equity = bal.loc['Common Stock Equity']
    
    col1, col2 = st.columns(2)
    #Calculation of the ratios...
    #LIQUIDITY RATIOS
    with col1:
        st.write("The current ratio is:", current_assets/current_liabilities)
    with col2:
        st.write("Quick Ratio:", (current_assets - inventory)/current_liabilities)
    
    #ASSET MANAGEMENT RATIOS
    with col1:
        st.write("Inventory turnover ratio:", cogs/inventory)
        st.write("Days Sales Outstanding:", accounts_receivable/(sales/360))
    with col2:
        st.write("Fixed Assets Turnover:", sales/net_fixed_assets)
        st.write("Total Assets Turnover:", sales/total_assets)
    
    #DEBT MANAGEMENT RATIOS
    with col1:
        st.write("Debt Ratio:", total_liabilities/total_assets)
    with col2:
       st.write("Times Interest Earned Ratio:", ebit/interest)
    
    #PROFITABILITY RATIOS
    with col1:
        st.write("Net Profit Margin Ratio:", net_income/sales)
        st.write("Return On Equity:", net_income/common_equity)
    with col2:
        st.write("Return on Assets:", net_income/total_assets)
           
   
#==============================================================================
# Main body
#==============================================================================
 
# Render the header
render_header()

# Render the tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Company profile", "Chart", "Financials", "Monte-Carlo Simulation", "Financial ratios"])
with tab1:
    render_tab1()
with tab2:
    render_tab2()
with tab3:
    render_tab3()
with tab4:
    render_tab4()
with tab5:
    render_tab5()
    
# Customize the dashboard with CSS
st.markdown(
    """
    <style>
        .stApp {
            background: #F0F8FF;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

###############################################################################
# END
###############################################################################
