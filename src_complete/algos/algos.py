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


def create_model(demand: pd.DataFrame, fixed_variables: pd.DataFrame):
    """This function creates the model. It will creates all the variables and contraints of the problem.
    It will also create the objective function.

    Args:
        demand (pd.DataFrame): demand dataframe
        fixed_variables (pd.DataFrame): fixed variables DataFrame

    Returns:
        dict: model_info (with the model created)
    """
    print("Creating the model...")

    monthly_demand_FPA = demand["Demand_Electronic_accessories"]
    monthly_demand_FPB = demand["Demand_Fashion_accessories"]

    nb_periods = len(monthly_demand_FPA)

    # creation of the model
    prob = LpProblem("Production_Planning", LpMinimize)

    # creation of the variables
    # for product A
    monthly_production_FPA = [
        LpVariable(f"Monthly_Production_FPA_{m}", 0) for m in range(nb_periods)
    ]
    monthly_stock_FPA = [
        LpVariable(f"Monthly_Stock_FPA_{m}", 0) for m in range(nb_periods)
    ]

    monthly_back_order_FPA = [
        LpVariable(f"Monthly_Back_Order_FPA_{m}", 0) for m in range(nb_periods)
    ]

    # for product B
    monthly_production_FPB = [
        LpVariable(f"Monthly_Production_FPB_{m}", 0) for m in range(nb_periods)
    ]
    monthly_stock_FPB = [
        LpVariable(f"Monthly_Stock_FPB_{m}", 0) for m in range(nb_periods)
    ]
    monthly_back_order_FPB = [
        LpVariable(f"Monthly_Back_Order_FPB_{m}", 0) for m in range(nb_periods)
    ]

    # for product 1
    monthly_purchase_RPone = [
        LpVariable(f"Monthly_Purchase_RPone_{m}", 0) for m in range(nb_periods)
    ]
    monthly_stock_RPone = [
        LpVariable(f"Monthly_Stock_RPone_{m}", 0) for m in range(nb_periods)
    ]
    monthly_stock_not_used_RPone = [
        LpVariable(f"Monthly_Stock_not_used_RPone{m}", 0) for m in range(nb_periods)
    ]
    monthly_stock_RPone_for_FPA = [
        LpVariable(f"Monthly_Stock_RPone_for_FPA{m}", 0) for m in range(nb_periods)
    ]
    monthly_stock_RPone_for_FPB = [
        LpVariable(f"Monthly_Stock_RPone_for_FPB{m}", 0) for m in range(nb_periods)
    ]

    # for product 2
    monthly_purchase_RPtwo = [
        LpVariable(f"Monthly_Purchase_RPtwo{m}", 0) for m in range(nb_periods)
    ]
    monthly_stock_RPtwo = [
        LpVariable(f"Monthly_Stock_RP{m}two", 0) for m in range(nb_periods)
    ]
    monthly_stock_not_used_RPtwo = [
        LpVariable(f"Monthly_Stock_not_used_RPtwo{m}", 0) for m in range(nb_periods)
    ]
    monthly_stock_RPtwo_for_FPA = [
        LpVariable(f"Monthly_Stock_RPtwo_for_FPA{m}", 0) for m in range(nb_periods)
    ]
    monthly_stock_RPtwo_for_FPB = [
        LpVariable(f"Monthly_Stock_RPtwo_for_FPB{m}", 0) for m in range(nb_periods)
    ]

    # creation of the constraints

    # Kirchoff's law for product A
    for m in range(1, nb_periods):
        prob += (
            monthly_production_FPA[m]
            - monthly_back_order_FPA[m - 1]
            + monthly_stock_FPA[m - 1]
            == monthly_demand_FPA[m] + monthly_stock_FPA[m] - monthly_back_order_FPA[m]
        )
    # Kirchoff's law for product B
    for m in range(1, nb_periods):
        prob += (
            monthly_production_FPB[m]
            - monthly_back_order_FPB[m - 1]
            + monthly_stock_FPB[m - 1]
            == monthly_demand_FPB[m] + monthly_stock_FPB[m] - monthly_back_order_FPB[m]
        )

    # Kirchoff's law for product 1
    for m in range(1, nb_periods):
        prob += (
            monthly_purchase_RPone[m - 1] + monthly_stock_not_used_RPone[m - 1]
            == monthly_stock_RPone[m]
        )
    # MS Fix for None issue
    prob += monthly_purchase_RPone[nb_periods - 1] == 0

    for m in range(1, nb_periods):
        prob += (
            monthly_purchase_RPtwo[m - 1] + monthly_stock_not_used_RPtwo[m - 1]
            == monthly_stock_RPtwo[m]
        )
    # MS Fix for None issue
    prob += monthly_purchase_RPtwo[nb_periods - 1] == 0

    for m in range(nb_periods):
        prob += monthly_production_FPA[m] <= fixed_variables["Max_Capacity_FPA"][0]

    prob += monthly_production_FPA[0] == fixed_variables["Initial_Production_FPA"][0]

    prob += monthly_back_order_FPA[0] == fixed_variables["Initial_Back_Order_FPA"][0]

    prob += monthly_stock_FPA[0] == fixed_variables["Initial_Stock_FPA"][0]

    # constraints on bill of materials for product A

    for m in range(1, nb_periods):
        prob += (
            monthly_production_FPA[m]
            == fixed_variables["number_RPone_to_produce_FPA"][0]
            * monthly_stock_RPone_for_FPA[m - 1]
            + fixed_variables["number_RPtwo_to_produce_FPA"][0]
            * monthly_stock_RPtwo_for_FPA[m - 1]
        )

    for m in range(nb_periods):
        prob += (
            fixed_variables["number_RPone_to_produce_FPA"][0]
            * monthly_stock_RPone_for_FPA[m]
            == fixed_variables["number_RPtwo_to_produce_FPA"][0]
            * monthly_stock_RPtwo_for_FPA[m]
        )

    # constraints on the variables : max and initial value for product A
    for m in range(nb_periods):
        prob += monthly_production_FPB[m] <= fixed_variables["Max_Capacity_FPB"][0]
    prob += monthly_production_FPB[0] == fixed_variables["Initial_Production_FPB"][0]

    prob += monthly_back_order_FPB[0] == fixed_variables["Initial_Back_Order_FPB"][0]
    prob += monthly_stock_FPB[0] == fixed_variables["Initial_Stock_FPB"][0]

    # constraints on bill of materials for product B

    for m in range(1, nb_periods):
        prob += (
            monthly_production_FPB[m]
            == fixed_variables["number_RPone_to_produce_FPB"][0]
            * monthly_stock_RPone_for_FPB[m - 1]
            + fixed_variables["number_RPtwo_to_produce_FPB"][0]
            * monthly_stock_RPtwo_for_FPB[m - 1]
        )

    for m in range(nb_periods):
        prob += (
            fixed_variables["number_RPone_to_produce_FPB"][0]
            * monthly_stock_RPone_for_FPB[m]
            == fixed_variables["number_RPtwo_to_produce_FPB"][0]
            * monthly_stock_RPtwo_for_FPB[m]
        )

    for m in range(nb_periods):
        prob += monthly_stock_RPone[m] <= fixed_variables["Max_Stock_RPone"][0]

    prob += monthly_stock_RPone[0] == fixed_variables["Initial_Stock_RPone"][0]

    prob += monthly_purchase_RPone[0] == fixed_variables["Initial_Purchase_RPone"][0]

    for m in range(nb_periods):
        prob += monthly_stock_RPone[m] == (
            monthly_stock_not_used_RPone[m]
            + monthly_stock_RPone_for_FPA[m]
            + monthly_stock_RPone_for_FPB[m]
        )
    # constraints on the variables : max and initial value for product 1

    for m in range(nb_periods):
        prob += monthly_stock_RPtwo[m] <= fixed_variables["Max_Stock_RPtwo"][0]

    prob += monthly_stock_RPtwo[0] == fixed_variables["Initial_Stock_RPtwo"][0]

    prob += monthly_purchase_RPtwo[0] == fixed_variables["Initial_Purchase_RPtwo"][0]
    # constraints that define what is a stock for product 1

    for m in range(nb_periods):
        prob += monthly_stock_RPtwo[m] == (
            monthly_stock_not_used_RPtwo[m]
            + monthly_stock_RPtwo_for_FPA[m]
            + monthly_stock_RPtwo_for_FPB[m]
        )
    # constraints on the variables : max value for product A and B (cumulative)

    for m in range(nb_periods):
        prob += (
            monthly_production_FPA[m] + monthly_demand_FPB[m]
            <= fixed_variables["Max_Capacity_of_FPA_and_FPB"][0]
        )

    # setting the objective function
    prob += lpSum(
        fixed_variables["Weight_of_Back_Order"][0]
        / 100
        * (
            fixed_variables["cost_FPA_Back_Order"][0] * monthly_back_order_FPA[m]
            + fixed_variables["cost_FPB_Back_Order"][0] * monthly_back_order_FPB[m]
        )
        + fixed_variables["Weight_of_Stock"][0]
        / 100
        * (
            fixed_variables["cost_FPA_Stock"][0] * monthly_stock_FPA[m]
            + fixed_variables["cost_FPB_Stock"][0] * monthly_stock_FPB[m]
            + fixed_variables["cost_RPone_Stock"][0] * monthly_stock_RPone[m]
            + fixed_variables["cost_RPtwo_Stock"][0] * monthly_stock_RPtwo[m]
        )
        for m in range(nb_periods)
    )

    # putting all the needed information in a dictionary
    model_info = {
        "model_created": prob,
        "model_solved": None,
        "Monthly_Production_FPA": monthly_production_FPA,
        "Monthly_Stock_FPA": monthly_stock_FPA,
        "Monthly_Back_Order_FPA": monthly_back_order_FPA,
        "Monthly_Production_FPB": monthly_production_FPB,
        "Monthly_Stock_FPB": monthly_stock_FPB,
        "Monthly_Back_Order_FPB": monthly_back_order_FPB,
        "Monthly_Stock_RPone": monthly_stock_RPone,
        "Monthly_Stock_RPtwo": monthly_stock_RPtwo,
        "Monthly_Purchase_RPone": monthly_purchase_RPone,
        "Monthly_Purchase_RPtwo": monthly_purchase_RPtwo,
    }

    print("Model created")
    return model_info


def solve_model(model_info: dict, solver_name):
    """This function solves the model and returns all the solutions in a dictionary.

    Args:
        model_info (dict): the model_info passed by the create_model function

    Returns:
        dict: the model solved and and the solutions
    """
    print("Solving the model...")
    prob = model_info["model_created"]

    nb_periods = len(model_info["Monthly_Production_FPA"])

    if solver_name != "Default":
        solver = getSolver(solver_name)
        # solving the model
        m_solved = prob.solve(solver)
    else:
        m_solved = prob.solve()
    
    # getting the solution in the right variables
    # for product A
    prod_sol_FPA = [
        value(model_info["Monthly_Production_FPA"][p]) for p in range(nb_periods)
    ]
    stock_sol_FPA = [
        value(model_info["Monthly_Stock_FPA"][p]) for p in range(nb_periods)
    ]
    bos_sol_FPA = [
        value(model_info["Monthly_Back_Order_FPA"][p]) for p in range(nb_periods)
    ]

    # for product B
    prod_sol_FPB = [
        value(model_info["Monthly_Production_FPB"][p]) for p in range(nb_periods)
    ]
    stock_sol_FPB = [
        value(model_info["Monthly_Stock_FPB"][p]) for p in range(nb_periods)
    ]
    bos_sol_FPB = [
        value(model_info["Monthly_Back_Order_FPB"][p]) for p in range(nb_periods)
    ]

    # for product 1
    stock_RPone_sol = [
        value(model_info["Monthly_Stock_RPone"][p]) for p in range(nb_periods)
    ]
    stock_RPtwo_sol = [
        value(model_info["Monthly_Stock_RPtwo"][p]) for p in range(nb_periods)
    ]

    # for product 2
    purchase_RPone_sol = [
        value(model_info["Monthly_Purchase_RPone"][p]) for p in range(nb_periods)
    ]
    purchase_RPtwo_sol = [
        value(model_info["Monthly_Purchase_RPtwo"][p]) for p in range(nb_periods)
    ]

    # put it in a dictionary
    model_info = {
        "model_created": prob,
        "model_solved": m_solved,
        "Monthly_Production_FPA": prod_sol_FPA,
        "Monthly_Stock_FPA": stock_sol_FPA,
        "Monthly_Back_Order_FPA": bos_sol_FPA,
        "Monthly_Production_FPB": prod_sol_FPB,
        "Monthly_Stock_FPB": stock_sol_FPB,
        "Monthly_Back_Order_FPB": bos_sol_FPB,
        "Monthly_Stock_RPone": stock_RPone_sol,
        "Monthly_Purchase_RPone": purchase_RPone_sol,
        "Monthly_Stock_RPtwo": stock_RPtwo_sol,
        "Monthly_Purchase_RPtwo": purchase_RPtwo_sol,
    }
    print("Model solved")
    return model_info


def create_results(model_info: dict, fixed_variables: pd.DataFrame, demand: pd.DataFrame):
    """This function creates the results of the model. The results dataframe is a concatenation of all the useful information.

    Args:
        model_info (dict): the dictionary created by the solve_model function
        fixed_variables (pd.DataFrame): the fixed variables of the problem
        demand (pd.DataFrame): the demand for A and B

    Returns:
        pd.DataFrame: dataframe that gathers all the useful information about the solution
    """
    print("Creating the results...")

    # getting the demand for A and B
    demand_series_FPA = demand["Demand_Electronic_accessories"]
    demand_series_FPB = demand["Demand_Fashion_accessories"]

    nb_periods = len(demand_series_FPA)

    # calculate the different costs
    cost_FPBO_FPA = fixed_variables["cost_FPA_Back_Order"][0] * np.array(
        model_info["Monthly_Back_Order_FPA"]
    )
    cost_stock_FPA = fixed_variables["cost_FPA_Stock"][0] * np.array(
        model_info["Monthly_Stock_FPA"]
    )
    cost_FPBO_FPB = fixed_variables["cost_FPB_Back_Order"][0] * np.array(
        model_info["Monthly_Back_Order_FPB"]
    )
    cost_stock_FPB = fixed_variables["cost_FPB_Stock"][0] * np.array(
        model_info["Monthly_Stock_FPB"]
    )
    cost_stock_RPone = fixed_variables["cost_RPone_Stock"][0] * np.array(
        model_info["Monthly_Stock_RPone"]
    )
    cost_stock_RPtwo = fixed_variables["cost_RPtwo_Stock"][0] * np.array(
        model_info["Monthly_Stock_RPtwo"]
    )
    cost_product_RPone = fixed_variables["cost_RPone_Purchase"][0] * np.array(
        model_info["Monthly_Purchase_RPone"]
    )
    cost_product_RPtwo = fixed_variables["cost_RPtwo_Purchase"][0] * np.array(
        model_info["Monthly_Purchase_RPtwo"]
    )

    # the total cost (sum of the costs)
    total_cost = (
        cost_FPBO_FPA
        + cost_stock_FPA
        + cost_FPBO_FPB
        + cost_stock_FPB
        + cost_stock_RPone
        + cost_product_RPone
        + cost_product_RPtwo
        + cost_stock_RPtwo
    )

    # creation of the dictionary that will be used to create the dataframe
    dict_for_dataframe = {
        "Monthly Production FPA": model_info["Monthly_Production_FPA"],
        "Monthly Stock FPA": model_info["Monthly_Stock_FPA"],
        "Monthly BO FPA": model_info["Monthly_Back_Order_FPA"],
        "Max Capacity FPA": [fixed_variables["Max_Capacity_FPA"][0]] * nb_periods,
        "Monthly Production FPB": model_info["Monthly_Production_FPB"],
        "Monthly Stock FPB": model_info["Monthly_Stock_FPB"],
        "Monthly BO FPB": model_info["Monthly_Back_Order_FPB"],
        "Max Capacity FPB": [fixed_variables["Max_Capacity_FPB"][0]] * nb_periods,
        "Monthly Stock RP1": model_info["Monthly_Stock_RPone"],
        "Monthly Stock RP2": model_info["Monthly_Stock_RPtwo"],
        "Monthly Purchase RP1": model_info["Monthly_Purchase_RPone"],
        "Monthly Purchase RP2": model_info["Monthly_Purchase_RPtwo"],
        "Demand FPA": demand_series_FPA,
        "Demand FPB": demand_series_FPB,
        "Stock FPA Cost": cost_stock_FPA,
        "Stock FPB Cost": cost_stock_FPB,
        "Stock RP1 Cost": cost_stock_RPone,
        "Stock RP2 Cost": cost_stock_RPtwo,
        "Purchase RP1 Cost": cost_product_RPone,
        "Purchase RP2 Cost": cost_product_RPtwo,
        "BO FPA Cost": cost_FPBO_FPA,
        "BO FPB Cost": cost_FPBO_FPB,
        "Total Cost": total_cost,
        "Index": range(nb_periods),
    }

    results = pd.DataFrame(dict_for_dataframe).round()
    print("Results created")

    # we erase the last two observations because of how the model is created,
    # their values don't have a meaning
    return results[:-2]