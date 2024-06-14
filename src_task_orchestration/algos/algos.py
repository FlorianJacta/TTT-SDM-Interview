import pandas as pd
import numpy as np
from pulp import LpVariable, LpProblem, LpMaximize, LpMinimize, value, getSolver, lpSum

import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
import datetime as dt
import numpy as np

# This code is used for configuration.py
fixed_variables = pd.DataFrame(
    {"Max_Capacity_FPA": [15000], "cost_FPA_Back_Order": [200], "cost_FPA_Stock": [45], "Initial_Back_Order_FPA": [0], "Initial_Stock_FPA": [5000], "Initial_Production_FPA": [3000], "number_RPone_to_produce_FPA": [20], "number_RPtwo_to_produce_FPA": [15], "Max_Capacity_FPB": [7000], "cost_FPB_Back_Order": [250], "cost_FPB_Stock": [40], "Initial_Back_Order_FPB": [0], "Initial_Stock_FPB": [10000], "Initial_Production_FPB": [5000], "number_RPone_to_produce_FPB": [50], "number_RPtwo_to_produce_FPB": [45], "Initial_Stock_RPone": [10000], "Max_Stock_RPone": [100000], "cost_RPone_Stock": [30], "cost_RPone_Purchase": [100], "Initial_Purchase_RPone": [10000], "Initial_Stock_RPtwo": [10000], "Max_Stock_RPtwo": [100000], "cost_RPtwo_Stock": [60], "cost_RPtwo_Purchase": [150], "Initial_Purchase_RPtwo": [10000], "Weight_of_Stock": [100], "Weight_of_Back_Order": [100], "Max_Capacity_of_FPA_and_FPB": [100000]}
)


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
        "Demand_Electronic_accessories": (predictions_xgboost["Predictions Electronic accessories"]*1.2).astype(int),
        "Demand_Fashion_accessories": (predictions_xgboost["Predictions Fashion accessories"]*0.7).astype(int)
    })
    demand = add_features(demand)
    return demand