from configuration.configuration import scenario_cfg

from taipy import Core, Gui
import taipy.gui.builder as tgb


scenario = None
data_node = None

with tgb.Page() as page:
    with tgb.layout("20 80"):
        tgb.scenario_selector("{scenario}")
        tgb.scenario("{scenario}")

    tgb.scenario_dag("{scenario}")
    tgb.job_selector()

    with tgb.layout("20 80"):
        tgb.data_node_selector("{data_node}")
        tgb.data_node("{data_node}", width="100%")

    
if __name__ == "__main__":
    core = Core()
    core.run()

    gui = Gui(page)
    gui.run(title="Sales Prediction", port=1221)
    