from sepal_ui import model
from traitlets import Any

from component import parameter as cp
from component.message import cm


class AuxModel(model.Model):

    ############################################################################
    # optional auxiliary files that advanced users can input
    ############################################################################
    ccdc_layer = Any(None).tag(sync=True)
    "ccdc alerts generated by the users"

    mask_layer = Any(None).tag(sync=True)
    "layer to mask out alerts, for example, forest no forest"

    aux_layer = Any(None).tag(sync=True)
    "auxiliary layer that the user can visualize during alert analysis, for example, forest plantation or forest management areas"

    custom_report_template = Any(None).tag(sync=True)
    "User custom template for reports"

    ############################################################################
    # planet credentials
    ############################################################################
