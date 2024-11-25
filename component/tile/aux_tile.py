from sepal_ui import sepalwidgets as sw
from sepal_ui import aoi
from sepal_ui.mapping import SepalMap
from component.message import cm
import ipyvuetify as v
from sepal_ui.scripts.utils import init_ee
from traitlets import Any, Unicode, link
from sepal_ui.planetapi import PlanetView

init_ee()


class AuxTile(sw.Layout):
    def __init__(self, aux_model):

        self._metadata = {"mount_id": "aux_tile"}
        self.aux_model = aux_model

        super().__init__()

        title1 = v.CardTitle(class_="pa-1 ma-1", children=["CCDC Alerts Asset"])
        ccdc_alerts_input = sw.inputs.AssetSelect(types=["IMAGE"])
        title2 = v.CardTitle(class_="pa-1 ma-1", children=["Mask Asset"])
        fnf_input = sw.inputs.AssetSelect(types=["IMAGE"])
        title3 = v.CardTitle(class_="pa-1 ma-1", children=["Auxiliary Asset"])
        aux_input = sw.inputs.AssetSelect(types=["IMAGE"])
        aux_viz = sw.TextField(
            label="Auxiliary Asset Visualization Parameters", v_model=None
        )
        title4 = v.CardTitle(class_="pa-1 ma-1", children=["Report template"])
        form_input = sw.inputs.FileInput()
        title5 = v.CardTitle(class_="pa-1 ma-1", children=["Planet Login Data"])
        planet_view = PlanetView()

        card1 = v.Card(
            class_="pa-3 ma-5", hover=True, children=[title1, ccdc_alerts_input]
        )
        card2 = v.Card(class_="pa-3 ma-5", hover=True, children=[title2, fnf_input])
        card3 = v.Card(
            class_="pa-3 ma-5", hover=True, children=[title3, aux_input, aux_viz]
        )
        card4 = v.Card(class_="pa-3 ma-5", hover=True, children=[title4, form_input])
        card5 = v.Card(class_="pa-3 ma-5", hover=True, children=[title5, planet_view])

        layout = sw.Row(
            children=[
                sw.Col(children=[card1, card2, card3, card4, card5]),
            ],
        )

        self.children = [layout]

        aux_model.bind(ccdc_alerts_input, "ccdc_layer").bind(
            fnf_input, "mask_layer"
        ).bind(aux_input, "aux_layer").bind(aux_viz, "aux_layer_vis").bind(
            form_input, "custom_report_template"
        )
