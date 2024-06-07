import pandas as pd
import numpy as np
from pulp import LpVariable, LpProblem, LpMaximize, LpMinimize, value, getSolver, lpSum

import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
import datetime as dt
import numpy as np

# This code is used for configuration.py

###############################################################################
# Functions
###############################################################################


def add_features(data):
    dates = pd.to_datetime(data["Date"])

    data["Year"] = dates.dt.year
    data["Month"] = dates.dt.month
    data["Day"] = dates.dt.day
    data["Weekday"] = dates.dt.weekday
    data["Week"] = dates.dt.isocalendar().week

    # Number of days after 30 December 2020
    base_date = pd.to_datetime("2020-12-30")
    data["Index"] = (dates - base_date).dt.days
    return data

def preprocess(initial_data):
    data = initial_data.groupby(['Date', 'Product_line'])\
                       .sum()\
                       .dropna()\
                       .reset_index()

    data = data.pivot(index='Date', columns='Product_line', values='Total').dropna()
    data['Date'] = data.index
    data['Date'] = pd.to_datetime(data['Date'])
    final_data = data[['Date','Electronic accessories', 'Fashion accessories']] #'Food and beverages', 'Health and beauty', 'Home and lifestyle', 'Sports and travel'
    final_data = add_features(final_data)

    date = final_data['Date'].max()
    return final_data, date

def train_xgboost(train_data):    
    y_elect = train_data['Electronic accessories']
    y_fash = train_data['Fashion accessories']
    X = train_data.drop(['Electronic accessories', 'Fashion accessories', 'Date'], axis=1)

    
    model_elect = GradientBoostingRegressor()
    model_elect.fit(X,y_elect)

    model_fash = GradientBoostingRegressor()
    model_fash.fit(X,y_fash)
    return model_elect, model_fash

def forecast_xgboost(model_elect, model_fash, date):
    dates = pd.to_datetime([date + dt.timedelta(days=i)
                            for i in range(60)])
    X = add_features(pd.DataFrame({"Date":dates}))
    X.drop('Date', axis=1, inplace=True)
    predictions = pd.DataFrame({"Date":dates, "Predictions Electronic accessories":model_elect.predict(X), "Predictions Fashion accessories":model_fash.predict(X)})
    return predictions


def convert_to_demand(date, predictions_xgboost):
    dates = pd.to_datetime([date + dt.timedelta(days=i)
                            for i in range(len(predictions_xgboost))])

    demand = pd.DataFrame({
        "Date": dates,
        "Demand_Electronic_accessories": predictions_xgboost["Predictions Electronic accessories"]*1.2,
        "Demand_Fashion_accessories": predictions_xgboost["Predictions Fashion accessories"]*0.7
    })
    demand = add_features(demand)
    return demand
