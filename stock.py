#!/usr/bin/env python
# coding: utf-8

# In[2]:


from collections import Counter
import datetime as dt
import matplotlib.pyplot as plt
from matplotlib import style
import numpy as np
import pandas as pd
import pandas_datareader.data as web
import seaborn as sns
from sklearn import svm,model_selection, neighbors
from sklearn.ensemble import VotingClassifier, RandomForestClassifier


# In[3]:


style.use('ggplot')


# In[4]:


start=dt.datetime(2000,1,1)
end=dt.datetime(2018,10,31)


# In[5]:


# pull off tesla data from yahoo finance and store into a dataframe
df= web.DataReader('TSLA', 'yahoo', start, end) 


# In[6]:


df.head()


# In[7]:


fig_size = plt.rcParams["figure.figsize"]
fig_size[0] = 15
fig_size[1] = 12
plt.rcParams["figure.figsize"] = fig_size


# In[8]:


df.plot()
plt.show()


# In[9]:


fig_size[0] = 20
fig_size[1] = 25
plt.rcParams["figure.figsize"] = fig_size


# In[10]:


df.plot(subplots=True)
plt.show()


# In[11]:


fig_size[0] = 15
fig_size[1] = 12
plt.rcParams["figure.figsize"] = fig_size


# In[12]:


dfwithmovingaverage=df


# In[13]:


dfwithmovingaverage['100ma']= df['Adj Close'].rolling(window=100,min_periods=0).mean()
dfwithmovingaverage.head()


# In[14]:


dfwithmovingaverage.tail()


# In[15]:


ax1=plt.subplot2grid((7,1),(0,0),rowspan=5, colspan=1)
ax2=plt.subplot2grid((7,1),(5,0),rowspan=2, colspan=1)

ax1.plot(dfwithmovingaverage.index,df['Adj Close'])
ax1.plot(dfwithmovingaverage.index,df['100ma'])
ax2.bar(dfwithmovingaverage.index,df['Volume'])
plt.show()


# In[16]:


from mpl_finance import candlestick_ohlc
import matplotlib.dates as mdates


# In[17]:


df_ohlc=df['Adj Close'].resample('10D').ohlc()
df_volume=df['Volume'].resample('10D').sum()


# In[18]:


df_ohlc.reset_index(inplace=True)


# In[19]:


df_ohlc.head()


# In[20]:


df_ohlc['Date']= df_ohlc['Date'].map(mdates.date2num)


# In[21]:


df_ohlc.head()


# In[22]:


fig_size[0] = 50
fig_size[1] = 50
plt.rcParams["figure.figsize"] = fig_size


# In[23]:


ax1=plt.subplot2grid((7,1),(0,0),rowspan=6, colspan=1)
ax2=plt.subplot2grid((7,1),(6,0),rowspan=1, colspan=1)

ax1.xaxis_date()
ax2.xaxis_date()
candlestick_ohlc(ax1, df_ohlc.values, width=4, colorup='g', colordown='r')
ax2.fill_between(df_volume.index.map(mdates.date2num), df_volume.values, 0)
plt.show()


# In[24]:


# Automating getting the s&p500 list


# In[25]:


import bs4 as bs
import pickle
import requests
import lxml


# In[26]:


def save_sp_500_tickers():
    resp = requests.get('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    soup = bs.BeautifulSoup(resp.text,"lxml")
    table = soup.find('table', {'class':'wikitable sortable'})
    tickers = []
    for row in table.findAll('tr')[1:]:
        ticker = row.findAll('td')[0].text
        ticker = ticker.replace('.','-').strip()
        tickers.append(ticker)
    with open('sp500tickers.pickle','wb') as f:
        pickle.dump(tickers, f)
        
    return tickers

#save_sp_500_tickers()


# In[27]:


# Getting all company pricing data in the S&P 500


# In[28]:


import os


# In[29]:


def get_data_from_yahoo(reload_sp500=True):
    if reload_sp500: 
        tickers = save_sp_500_tickers() 
    else: 
        with open("sp500tickers.pickle", "rb") as f: 
            tickers = pickle.load(f)
    if not os.path.exists('stock_dfs'):
            os.makedirs('stock_dfs')
               
    start = dt.datetime(2000,1,1)
    end = dt.datetime(2016,12,31)
            
    for ticker in tickers:
        try:
            print(ticker)
            if not os.path.exists('stocks_dfs/{}.csv'.format(ticker)):
                df = web.DataReader(ticker, 'yahoo', start, end)
                df.to_csv('stock_dfs/{}.csv'.format(ticker))
            else: print('Already have {}'.format(ticker)) 
                
        except: 
            print('Cannot obtain data for ' +ticker) 

get_data_from_yahoo()


# In[30]:


# combining data
# SOURCE:https://pythonprogramming.net/combining-stock-prices-into-one-dataframe-python-programming-for-finance/


# In[31]:


def compile_data():
    with open('sp500tickers.pickle', 'rb') as f:
        tickers = pickle.load(f)
        
    main_df = pd.DataFrame()
    
    for count,ticker in enumerate(tickers):
        df = pd.read_csv('stock_dfs/{}.csv'.format(ticker))
        df.set_index('Date',inplace =True)
        
        df.rename(columns = {'Adj Close': ticker}, inplace=True)
        df.drop(['Open','High','Low','Close','Volume'],1,inplace=True)
        
        if main_df.empty:
            main_df = df
        else:
            main_df = main_df.join(df, how='outer')
            
        if count % 10 ==0:
            print(count)
    
    print(main_df.head())
    main_df.to_csv('sp500_joined_closes.csv')

compile_data()
            


# In[32]:


# Visualizing correlations


# In[33]:


fig_size[0] = 100
fig_size[1] = 100
plt.rcParams["figure.figsize"] = fig_size


# In[34]:


def visualize_data():
    df=pd.read_csv('sp500_joined_closes.csv')
    df_corr=df.corr()
    print(df_corr.head())
    
    data = df_corr.values
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    
    heatmap = ax.pcolor(data,cmap=plt.cm.RdYlGn)
    fig.colorbar(heatmap)
    ax.set_xticks(np.arange(data.shape[0]) + 0.5, minor=False)
    ax.set_yticks(np.arange(data.shape[1]) + 0.5, minor=False)
    ax.invert_yaxis()
    ax.xaxis.tick_top()
    
    column_labels = df_corr.columns
    row_labels = df_corr.index
    
    ax.set_xticklabels(column_labels)
    ax.set_yticklabels(row_labels)
    plt.xticks(rotation=90)
    heatmap.set_clim(-1,1)
    plt.tight_layout()
    #plt.show()
    


# In[35]:


visualize_data()


# In[36]:


# Preprocessing data for machine learning


# In[37]:


def process_data_for_labels(ticker):
    hm_days = 7
    df = pd.read_csv('sp500_joined_closes.csv', index_col=0)
    tickers = df.columns.values.tolist()
    df.fillna(0, inplace=True)
    
    for i in range(1, hm_days+1):
        df['{}_{}d'.format(ticker,i)] = (df[ticker].shift(-i) - df[ticker]) / df[ticker]
        
    df.fillna(0, inplace=True)
    return tickers,df


# In[38]:


# Creating machine learning target function


# In[39]:


def buy_sell_hold(*args):
    cols = [c for c in args]
    requirement = 0.04
    for col in cols:
        if col > requirement:
            return 1       # label 1 = buy
        if col <-requirement:
            return -1      # label -1 = sell
    return 0               # label 0 = hold


# In[40]:


# Creating labels for Machine Learning


# In[41]:


def extract_featuresets(ticker):
    tickers, df = process_data_for_labels(ticker)
    
    df['{}_target'.format(ticker)] = list(map(buy_sell_hold,
                                             df['{}_1d'.format(ticker)],
                                             df['{}_2d'.format(ticker)],
                                             df['{}_3d'.format(ticker)],
                                             df['{}_4d'.format(ticker)],
                                             df['{}_5d'.format(ticker)],
                                             df['{}_6d'.format(ticker)],
                                             df['{}_7d'.format(ticker)]))
                                                
    vals = df['{}_target'.format(ticker)].values.tolist()
    str_vals = [str(i) for i in vals]
    print('Data spread:', Counter(str_vals))
    
    df.fillna(0, inplace = True)
    df = df.replace([np.inf,-np.inf],np.nan)
    df.dropna(inplace=True)
    
    df_vals = df[[ticker_name for ticker_name in tickers]].pct_change()
    df_vals = df_vals.replace([np.inf,-np.inf],0)
    df_vals.fillna(0,inplace=True)
    
    X = df_vals.values
    y = df['{}_target'.format(ticker)].values
    
    return X, y, df


# In[42]:


extract_featuresets('GOOGL')


# In[43]:


# Perform Machine learning


# In[44]:


def do_ml(ticker):
    X, y, df = extract_featuresets(ticker)
    X_train, X_test, y_train, y_test = model_selection.train_test_split(X,y,test_size=0.25)
    
    clf = VotingClassifier([('lsvc', svm.LinearSVC()),
                           ('knn',neighbors.KNeighborsClassifier()),
                           ('rfor', RandomForestClassifier())])
    
    clf.fit(X_train, y_train)
    confidence = clf.score(X_test, y_test)
    print('Accuracy',confidence)
    predictions = clf.predict(X_test)
    print('Predicted spread:', Counter(predictions))
    
    return confidence


# In[45]:


do_ml('CRM')


# In[ ]:


from sklearn import model_selection
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC



# prepare configuration for cross validation test harness
seed = 7
# prepare models
models = []
models.append(('LR', LogisticRegression()))
models.append(('LDA', LinearDiscriminantAnalysis()))
models.append(('KNN', KNeighborsClassifier()))
models.append(('CART', DecisionTreeClassifier()))
models.append(('NB', GaussianNB()))
models.append(('SVM', SVC()))

# evaluate each model in turn
results = []
names = []
scoring = 'accuracy'
X, y, df = extract_featuresets('BAC')
for name, model in models:
	kfold = model_selection.KFold(n_splits=10, random_state=seed)
	cv_results = model_selection.cross_val_score(model, X,y, cv=kfold, scoring=scoring)
	results.append(cv_results)
	names.append(name)
	msg = "%s: %f (%f)" % (name, cv_results.mean(), cv_results.std())
	print(msg)
# boxplot algorithm comparison
fig = plt.figure()
fig.suptitle('Algorithm Comparison')
ax = fig.add_subplot(80)
plt.boxplot(results)
ax.set_xticklabels(names)
#plt.show()



# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




