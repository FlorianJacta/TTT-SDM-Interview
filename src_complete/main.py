from configuration.configuration import scenario_cfg

from taipy import Core, Gui
import taipy.gui.builder as tgb

temp_data_node = None
scenario = None
data_node = None
open_modal = False

def on_dag(state, entity):
    print("hey")
    state.temp_data_node = entity
    state.open_modal = True

with tgb.Page() as page:
    with tgb.layout("20 80"):
        tgb.scenario_selector("{scenario}")
        tgb.scenario("{scenario}")

    tgb.scenario_dag("{scenario}", on_action=on_dag)
    tgb.job_selector()

    with tgb.layout("20 80"):
        tgb.data_node_selector("{data_node}")
        tgb.data_node("{data_node}", width="100%")


    tgb.dialog(open="{open_modal}", on_action="{lambda s: s.assign('open_modal', False)}", page="modal")
        
with tgb.Page() as modal:  
    tgb.data_node("{temp_data_node}")

    
if __name__ == "__main__":
    core = Core()
    core.run()

    pages = {"home": page, "modal": modal}

    gui = Gui(pages=pages)
    gui.run(title="Sales Prediction", port=1221)
    