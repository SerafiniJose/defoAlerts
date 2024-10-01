from sepal_ui import model
from traitlets import Any, Int, Float

from component import parameter as cp
from component.message import cm


class AlertFilterModel(model.Model):

    ############################################################################
    # alert filter section files
    ############################################################################
    available_alerts_list = Any("").tag(sync=True)
    "List of alert collections that has alerts in the aoi and dates selected by the users"

    available_alerts_raster_list = Any("").tag(sync=True)
    "List of alert collections that has alerts in the aoi and dates selected by the users"

    alert_selection_polygons = Any(None).tag(sync=True)
    "User drawn polygons used for filtering alerts in case this method of filtering is selected"

    min_area = Any(None).tag(sync=True)
    "Minimum area for alerts set by user"

    max_number_alerts = Any(None).tag(sync=True)
    "Max number of alerts set by user"

    alert_selection_method = Any(None).tag(sync=True)
    "User alerts selection methond for selecting alerts"


class SelectedAlertsModel(model.Model):

    ############################################################################
    # selected alerts
    ############################################################################
    alerts_centroids = Any(None).tag(sync=True)
    "Feature Collection that cointains centroid of alerts filtered, they may or may not have a priority field"
    "List of needed fields, valid, before_img, after_img, min_date, max_date, alert_polygon_dir, area, description"

    actual_alert_id = Any(None).tag(sync=True)
    "ID of current alert being reviewed"

    before_planet_monthly_images = Any(None).tag(sync=True)
    "List of available before images from planet monthly, just for current alert"

    before_sentinel2_images = Any(None).tag(sync=True)
    "List of available before images from sentinel 2 img, just for current alert"

    before_planet_daily_images = Any(None).tag(sync=True)
    "List of available before images from planet daily, just for current alert"

    after_planet_monthly_images = Any(None).tag(sync=True)
    "List of available after images from planet monthly, just for current alert"

    after_sentinel2_images = Any(None).tag(sync=True)
    "List of available after images from sentinel 2 img, just for current alert"

    after_planet_daily_images = Any(None).tag(sync=True)
    "List of available after images from planet daily, just for current alert"

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


class ReviewAlertsModel(model.Model):

    ############################################################################
    # selected alerts
    ############################################################################
    nTotalAlerts = Int(None).tag(sync=True)
    "Total Alerts Number"

    nReviewedAlerts = Int(None).tag(sync=True)
    "Reviewed Alerts Number"

    nConfirmedAlerts = Int(None).tag(sync=True)
    "Confirmed Alerts Number"

    nFalseAlerts = Int(None).tag(sync=True)
    "False positive Alerts Number"
