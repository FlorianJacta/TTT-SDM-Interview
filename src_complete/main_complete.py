# Copyright 2021-2024 Avaiga Private Limited
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
# an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
import taipy as tp
from taipy.gui import Gui

from configuration.configuration import scenario_cfg

from taipy import Core
from pages import *

import pandas as pd
import plotly.express as px
from plotly import graph_objects as go

from taipy.core import Scenario


def create_scenarios():
    scenario = tp.create_scenario(scenario_cfg, name="Orginal Scenario")
    fixed_variables: pd.DataFrame = scenario.fixed_variables.read()

    for i in range(80, 120, 5):
        fixed_variables.iloc[0, :] = (fixed_variables.iloc[0, :] * i/100).apply(int)
        scenario.fixed_variables.write(fixed_variables)
        tp.submit(scenario)
        scenario = tp.create_scenario(scenario_cfg, name=f"Scenario for {i/100:.0%}")



scenario = None
data_node = None

pages = {
    "/":"""
<|layout|columns=20 80|
<|{scenario}|scenario_selector|>

<|{scenario}|scenario|>
|>

<|job_selector|>

<|layout|columns=20 80|
<|{data_node}|data_node_selector|>

<|{data_node}|data_node|>
|>

<|chart|fig={total_cost_scenarios_fig}|rebuild|>


<|layout|columns=1 1|
<|chart|fig={fpa_summary_fig}|rebuild|>

<|chart|fig={fpb_summary_fig}|rebuild|>

<|chart|fig={rpone_fig}|rebuild|>

<|chart|fig={rptwo_fig}|rebuild|>
|>

<|chart|fig={total_cost_scenario_fig}|rebuild|>

""",
}

rpone_fig = None
rptwo_fig = None

fpa_summary_fig = None
fpb_summary_fig = None

total_cost_scenario_fig = None

total_cost_scenarios_fig = None

def on_change(state, var_name):
    if var_name == "scenario":
        on_update(state)

def on_init(state):
    scenarios = tp.get_scenarios()

    scenarios_results = [(s.name, s.results.read()) for s in scenarios]
    scenarios_results = [(s[0], s[1].dropna()) for s in scenarios_results if s[1] is not None]

    scenario_results_costs = pd.DataFrame({"Name": [s[0] for s in scenarios_results], "Total Cost": [s[1]["Total Cost"].sum() for s in scenarios_results]})
    state.total_cost_scenarios_fig = px.bar(scenario_results_costs, x="Name", y="Total Cost")

    on_update(state)


def on_update(state):
    if not isinstance(state.scenario, Scenario):
        return
    
    scenario_results = state.scenario.results.read()
    if scenario_results is None:
        return 
    
    state.rpone_fig = go.Figure(data=[go.Bar(x=scenario_results["Index"], y=scenario_results["Monthly Stock RP1"]), go.Bar(x=scenario_results["Index"], y=scenario_results["Monthly Purchase RP1"])])
    state.rptwo_fig = go.Figure(data=[go.Bar(x=scenario_results["Index"], y=scenario_results["Monthly Stock RP2"]), go.Bar(x=scenario_results["Index"], y=scenario_results["Monthly Purchase RP2"])])


    state.fpa_summary_fig = go.Figure(
        data=[go.Bar(x=scenario_results["Index"], y=scenario_results["Monthly Production FPA"]),
              go.Bar(x=scenario_results["Index"], y=scenario_results["Monthly Stock FPA"]),
              go.Bar(x=scenario_results["Index"], y=scenario_results["Monthly BO FPA"]),
              go.Bar(x=scenario_results["Index"], y=scenario_results["Max Capacity FPA"]),
              go.Bar(x=scenario_results["Index"], y=scenario_results["Demand FPA"])]
    )
    state.fpb_summary_fig = go.Figure(
        data=[go.Bar(x=scenario_results["Index"], y=scenario_results["Monthly Production FPB"]),
              go.Bar(x=scenario_results["Index"], y=scenario_results["Monthly Stock FPB"]),
              go.Bar(x=scenario_results["Index"], y=scenario_results["Monthly BO FPB"]),
              go.Bar(x=scenario_results["Index"], y=scenario_results["Max Capacity FPB"]),
              go.Bar(x=scenario_results["Index"], y=scenario_results["Demand FPB"])]
    )

    # all the costs
    state.total_cost_scenario_fig = go.Figure(
        data=[go.Bar(x=scenario_results["Index"], y=scenario_results["Total Cost"]),
              go.Bar(x=scenario_results["Index"], y=scenario_results["Stock FPA Cost"]),
              go.Bar(x=scenario_results["Index"], y=scenario_results["Stock FPB Cost"]),
              go.Bar(x=scenario_results["Index"], y=scenario_results["Stock RP1 Cost"]),
              go.Bar(x=scenario_results["Index"], y=scenario_results["Stock RP2 Cost"]),
              go.Bar(x=scenario_results["Index"], y=scenario_results["BO FPA Cost"]),
              go.Bar(x=scenario_results["Index"], y=scenario_results["BO FPB Cost"]),
              go.Bar(x=scenario_results["Index"], y=scenario_results["Purchase RP1 Cost"]),
              go.Bar(x=scenario_results["Index"], y=scenario_results["Purchase RP2 Cost"])]
    )

    print(state.total_cost_scenarios_fig, state.total_cost_scenario_fig, state.fpa_summary_fig, state.fpb_summary_fig, state.rpone_fig, state.rptwo_fig)

if __name__ == "__main__":
    core = Core()
    core.run()
    # #############################################################################
    # PLACEHOLDER: Create and submit your scenario here                           #
    #                                                                             #
    # Example:                                                                    #
    # from configuration import scenario_config                                   #
    # scenario = tp.create_scenario(scenario_config)                              #
    # scenario.submit()                                                           #
    # Comment, remove or replace the previous lines with your own use case        #
    # #############################################################################

    if tp.get_scenarios() == []:
        create_scenarios()

    gui = Gui(pages=pages)
    gui.run(title="Sales Prediction", port=1221)
    