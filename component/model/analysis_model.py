from sepal_ui import model
from traitlets import Any, Int, Float

from component import parameter as cp
from component.message import cm


class AlertAnalysisModel(model.Model):

    ############################################################################
    # selected alerts
    ############################################################################
    alerts_gdf = Any(None).tag(sync=True)
    "Geodataframe containing centroids of alerts to be reviewed"

    actual_alert_id = Int(-1).tag(sync=True)
    "ID of current alert being reviewed"

    max_alert_id = Int(-1).tag(sync=True)
    "ID of last alert"

    before_planet_monthly_images = Any(None).tag(sync=True)
    "List of available before images from planet monthly, just for current alert"

    after_planet_monthly_images = Any(None).tag(sync=True)
    "List of available after images from planet monthly, just for current alert"

    before_s2_images = Any(None).tag(sync=True)
    "List of available before images from sentinel 2, just for current alert"

    before_s2_images_time = Float(None).tag(sync=True)
    "Time when before images from sentinel 2 were set"

    after_s2_images = Any(None).tag(sync=True)
    "List of available after images from sentinel 2, just for current alert"

    after_s2_images_time = Float(None).tag(sync=True)
    "Time when after images from sentinel 2 were set"

    before_img = Any(None).tag(sync=True)
    "Path to downloaded before img"

    after_img = Any(None).tag(sync=True)
    "Path to downloaded after img"

    auto_alert_polygons = Any(None).tag(sync=True)
    "Alert polygons generated with DL model"

    user_alert_polygons = Any(None).tag(sync=True)
    "Alert polygons generated by the user"

    alert_report = Any(None).tag(sync=True)
    "Path to reach pdf/word report file generated"

    def export_dictionary(self):
        dictionary = {
            "actual_alert_id": 0 if self.actual_alert_id == -1 else self.actual_alert_id,
            "max_alert_id": 0 if self.actual_alert_id == -1 else self.actual_alert_id,
            # "before_planet_monthly_images": self.before_planet_monthly_images,
            # "after_planet_monthly_images": self.after_planet_monthly_images,           
            }
        return dictionary
    
    def import_from_dictionary(self, data):
        import json
        """
        Import class attributes from a JSON file.
        Args:
            data (str): Dcitionary JSON file.
        """
        try:
            # Update attributes
            self.actual_alert_id = data.get("actual_alert_id", self.actual_alert_id)
            self.max_alert_id = data.get("max_alert_id", self.max_alert_id)
            # self.before_planet_monthly_images = data.get("before_planet_monthly_images", self.before_planet_monthly_images)
            # self.after_planet_monthly_images = data.get("after_planet_monthly_images", self.after_planet_monthly_images)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading JSON file: {e}")