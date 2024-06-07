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

from taipy import Config, Scope, Frequency
from algos.algos import *


Config.configure_job_executions(mode="standalone", max_nb_of_workers=5)

###############################################################################
# Data nodes
###############################################################################

initial_data_cfg = Config.configure_data_node(id="initial_data",
                                              storage_type="csv",
                                              path="data/modified_supermarkt_sales_plus.csv",
                                              scope=Scope.GLOBAL)


date_cfg = Config.configure_data_node(id="date", scope=Scope.GLOBAL)
final_data_cfg = Config.configure_data_node(id="final_data", scope=Scope.GLOBAL)
model_elect_cfg = Config.configure_data_node(id="model_xgboost_elect", scope=Scope.GLOBAL)
model_fash_cfg = Config.configure_data_node(id="model_xgboost_fash", scope=Scope.GLOBAL)

predictions_xgboost_cfg = Config.configure_data_node(id="predictions_xgboost", scope=Scope.GLOBAL)

demand_cfg = Config.configure_csv_data_node(id="demand",
                                            path="data/demand.csv",
                                            scope=Scope.GLOBAL,)


###############################################################################
# Tasks
###############################################################################

# intial_data_cfg > preprocess > final_data_cfg, date_cfg
...

# final_data_cfg > train_xgboost > model_elect_cfg, model_fash_cfg
...


# ...
...



###############################################################################
# Merged Scenario config
###############################################################################

scenario_cfg = Config.configure_scenario(id='merged_scenario', 
                                         task_configs=[...],
                                         frequency=Frequency.MONTHLY)

Config.export('configuration/merged_config.toml')
