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

"""
Contain the application's configuration including the scenario configurations.

The configuration is run by the Core service.
"""

from algos.algos import *

from taipy import Config, Scope, Frequency

import json


Config.configure_job_executions(mode="standalone", max_nb_of_workers=5)

###############################################################################
# Data nodes
###############################################################################

initial_data_cfg = Config.configure_csv_data_node(id="initial_data",
                                                  path="data/modified_supermarkt_sales_plus.csv",
                                                  scope=Scope.GLOBAL)

date_cfg = Config.configure_data_node(id="date", scope=Scope.GLOBAL)
final_data_cfg = Config.configure_data_node(id="final_data", scope=Scope.GLOBAL)
model_elect_cfg = Config.configure_data_node(id="model_xgboost_elect", scope=Scope.GLOBAL)
model_fash_cfg = Config.configure_data_node(id="model_xgboost_fash", scope=Scope.GLOBAL)
predictions_xgboost_cfg = Config.configure_data_node(id="predictions_xgboost", scope=Scope.GLOBAL)

demand_cfg = Config.configure_csv_data_node(id="demand", scope=Scope.GLOBAL, default_path="data/demand.csv")


with open('data/fixed_variables_default.json') as f:
    fixed_variables_default = json.load(f)

fixed_variables_cfg = Config.configure_csv_data_node(id="fixed_variables", default_data=fixed_variables_default)
solver_name_cfg = Config.configure_data_node(id="solver_name", default_data="Default")
model_created_cfg = Config.configure_data_node(id="model_created")
model_solved_cfg = Config.configure_data_node(id="model_solved")

results_cfg = Config.configure_data_node(id="results")

###############################################################################
# Tasks
###############################################################################

task_preprocess_cfg = Config.configure_task(id="task_preprocess_data",
                                            function=preprocess,
                                            input=[initial_data_cfg],
                                            output=[final_data_cfg, date_cfg], 
                                            skippable=True)

task_train_xgboost_cfg = Config.configure_task(id="task_train",
                                               function=train_xgboost,
                                               input=final_data_cfg,
                                               output=[model_elect_cfg, model_fash_cfg],
                                               skippable=True) 

task_forecast_xgboost_cfg = Config.configure_task(id="task_forecast",
                                                function=forecast_xgboost,
                                                input=[model_elect_cfg, model_fash_cfg, date_cfg],
                                                output=predictions_xgboost_cfg,
                                                skippable=True)

task_convert_to_demand_cfg = Config.configure_task(id="task_convert_to_demand",
                                        function=convert_to_demand,
                                        input=[date_cfg, 
                                               predictions_xgboost_cfg],
                                        output=demand_cfg,
                                        skippable=True)

create_model_task = Config.configure_task(id="create_model",
                                          input=[demand_cfg, fixed_variables_cfg],
                                          function=create_model,
                                          output=[model_created_cfg],
                                          skippable=True)

solve_model_cfg = Config.configure_task(id="solve_model",
                                        input=[model_created_cfg, solver_name_cfg],
                                        function=solve_model,
                                        output=[model_solved_cfg],
                                        skippable=True)

create_results_cfg = Config.configure_task(id="create_results",
                                           input=[model_solved_cfg, fixed_variables_cfg, demand_cfg],
                                           function=create_results,
                                           output=[results_cfg],
                                           skippable=True)

###############################################################################
# Merged Scenario config
###############################################################################

scenario_cfg = Config.configure_scenario(id='merged_scenario', 
                                         task_configs=[task_preprocess_cfg,
                                                       task_train_xgboost_cfg,
                                                       task_forecast_xgboost_cfg,
                                                       task_convert_to_demand_cfg,
                                                       create_model_task, 
                                                       solve_model_cfg, 
                                                       create_results_cfg],
                                         frequency=Frequency.MONTHLY)

Config.export('configuration/merged_config.toml')
