import taipy as tp

from configuration.configuration import initial_data_cfg, demand_cfg

from taipy import Core, Gui
import taipy.gui.builder as tgb

data_node = None

with tgb.Page() as page:
    with tgb.layout("20 80"):
        tgb.data_node_selector("{data_node}")
        tgb.data_node("{data_node}")
    

if __name__ == "__main__":
    core = Core()
    core.run()

    tp.create_global_data_node(initial_data_cfg)
    tp.create_global_data_node(demand_cfg)

    gui = Gui(page=page)
    gui.run(title="Sales Prediction", port=1221)
    