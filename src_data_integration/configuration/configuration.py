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
from taipy import Config, Scope


###############################################################################
# Data nodes
###############################################################################
initial_data_cfg = Config.configure_csv_data_node(id="initial_data",
                                                  path="data/modified_supermarkt_sales_plus.csv",
                                                  scope=Scope.GLOBAL)

demand_cfg = Config.configure_csv_data_node(id="demand", 
                                            path="data/demand.csv",
                                            scope=Scope.GLOBAL)

