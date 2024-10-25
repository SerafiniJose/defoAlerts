# functions taken from https://github.com/sepal-contrib/alert_module/blob/main/component/scripts/alert.py

from datetime import date, datetime
import json
from pathlib import Path
from math import floor, ceil
from itertools import product
import requests
from math import pi, sqrt

import geopandas as gpd
import ee
import pandas as pd

from component.message import cm
from shapely.geometry import Point, Polygon


def date_range_check(
    start_date_str, end_date_str, start_time_collection, end_time_collection
):
    # Convert input strings to datetime objects
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    # Convert list of date strings to datetime objects
    x = datetime.strptime(start_time_collection, "%Y-%m-%d")
    y = datetime.strptime(end_time_collection, "%Y-%m-%d")

    # Combined list of dates
    all_dates = [x, y]

    # Check 1: start date must be older than end date
    if start_date >= end_date:
        return "Fail: Start date should be older than end date"

    # Check 2: end date must be equal to or more recent than any date on the first or second list
    if not any(end_date >= d for d in all_dates):
        return (
            "Fail: End date is not equal to or more recent than any date in the lists"
        )

    # Check 3: start date must be older than any date on the first or second list
    if not any(start_date < d for d in all_dates):
        return "Fail: Start date is not older than any date in the lists"

    return "Pass"


def get_alerts(collection, start, end, aoi, asset):
    """
    get the alerts restricted to the aoi and the specified dates.
    The Returned images will embed mandatory and optional bands:
    madatory:
        "alert": the alert value 1 for alerts,2 for potential, 0 for no_alerts
        "date": YYYY.julian_day

    Args:
        collection (str): the collection name
        start (str): the start of the analysis (YYYY-MM-DD)
        end (str): the end day of the analysis (YYYY-MM-DD)
        aoi (ee.FeatureCollection): the selected aoi
        asset (str): the asset Id of the Image

    Returns:
        (ee.Image) the alert Image
    """

    if collection == "GLAD-L":
        alerts = _from_glad_l(start, end, aoi)
    elif collection == "RADD":
        alerts = _from_radd(start, end, aoi)
    elif collection == "CCDC":
        #    alerts = _from_nrt(aoi, asset)
        alerts = asset
    elif collection == "GLAD-S2":
        alerts = _from_glad_s(start, end, aoi)
    else:
        raise Exception("Collection not supported")

    return alerts


def to_date(dates):
    """
    transform a date store as (int) number of days since 2018-12-31 to a date in YYYY.ddd
    adapted from https:#gis.stackexchange.com/a/428770/154945 to tackle the GLAD_S2 date format
    """

    reference_year = ee.Number(2018)

    # compute the approximate number of year
    years = dates.add(364).divide(365).floor().add(reference_year)

    # compute a leap year image
    leap_years = ee.Image(
        ee.Array(
            ee.List.sequence(reference_year, 2070)
            .map(
                lambda y: (
                    ee.Date.fromYMD(ee.Number(y).add(1), 1, 1)  # last of year
                    .advance(-1, "day")
                    .getRelative("day", "year")
                    .gt(364)  # got the extra day
                    .multiply(
                        ee.Number(y)
                    )  # return the actual year if a leap year else 0
                )
            )
            .filter(ee.Filter.neq("item", 0))
        )
    )

    # Mask out leap years after the year of the pixel
    # Results in an image where the pixel value represents the number of leap years
    nb_leap_years = leap_years.arrayMask(leap_years.lte(years)).arrayLength(0)

    # adjust the day with the number of leap year
    # and recompute the number of years
    adust_dates = dates.add(nb_leap_years)
    years = adust_dates.add(364).divide(365).floor().add(reference_year)

    # adapt the number of days if the current year is a leap year
    is_leap_year = leap_years.arrayMask(leap_years.eq(years)).arrayLength(0)
    jan_first = (
        years.subtract(reference_year)
        .multiply(365)
        .subtract(364)
        .add(nb_leap_years)
        .add(1)
        .subtract(is_leap_year)
    )
    dates = adust_dates.subtract(jan_first).add(1)
    is_before_leap_year = dates.lte(31 + 29)
    dates_adjustment = is_leap_year.And(is_before_leap_year)  # 1 if leap day else 0
    dates = dates.subtract(dates_adjustment)

    return years.add(dates.divide(1000))


def _from_glad_l(start, end, aoi):
    """reformat the glad alerts to fit the module expectation"""

    # glad is not compatible with multi year analysis so we cut the dataset into
    # yearly pieces and merge thm together in a second step
    # as it includes multiple dataset I'm not sure I can perform it without a python for loop

    # cut the interval into yearly pieces
    start = datetime.strptime(start, "%Y-%m-%d")
    end = datetime.strptime(end, "%Y-%m-%d")

    periods = [[start, end]]
    tmp = periods.pop()
    while tmp[0].year != tmp[1].year:
        year = tmp[0].year
        periods.append([tmp[0], date(year, 12, 31)])
        periods.append([date(year + 1, 1, 1), tmp[1]])
        tmp = periods.pop()
    periods.append(tmp)

    images = []
    for period in periods:
        year = period[0].year
        start = period[0].timetuple().tm_yday
        end = period[1].timetuple().tm_yday

        if year < 2024:
            source = f"projects/glad/alert/{year}final"
        else:
            source = "projects/glad/alert/UpdResult"

        # the number of bands throughout the ImageCollection is not consisitent
        # remove the extra useless one before any operation
        bands = [f"conf{year%100}", f"alertDate{year%100}", "obsCount", "obsDate"]

        # create the composit band alert_date.
        # cannot use the alertDateXX band directly because
        # they are not all casted to the same type
        alerts = (
            ee.ImageCollection(source)
            .select(bands)
            .map(lambda image: image.uint16())
            .filterBounds(aoi)
            .mosaic()
            .clip(aoi)
        )
        alerts = alerts.updateMask(
            alerts.select(f"alertDate{year%100}")
            .gt(start)
            .And(alerts.select(f"alertDate{year%100}").lt(end))
        )

        # create a unique alert band
        alert_band = (
            alerts.select(f"conf{year%100}")
            .remap([0, 1, 2, 3], [0, 0, 2, 1])
            .rename("alert")
        )

        # change the date format
        date_band = (
            alerts.select(f"alertDate{year%100}")
            .divide(1000)
            .add(ee.Image(year))
            .rename("date")
        )

        # create the composite
        composite = (
            alerts.select(["obsCount", "obsDate"])
            .addBands(date_band)
            .addBands(alert_band)
        )

        images += [composite]

    all_alerts = ee.ImageCollection.fromImages(images).mosaic()

    return all_alerts


def _from_radd(start, end, aoi):
    """reformat the radd alerts to fit the module expectation"""

    # extract dates from parameters
    start = datetime.strptime(start, "%Y-%m-%d")
    end = datetime.strptime(end, "%Y-%m-%d")

    # select the alerts and mosaic them as image
    source = "projects/radar-wur/raddalert/v1"
    alerts = (
        ee.ImageCollection(source)
        .filterBounds(aoi)
        .filterMetadata("layer", "contains", "alert")
        .mosaic()
        .uint16()
    )

    # filter the alerts dates
    # extract julian dates ()
    start = int(start.strftime("%y%j"))
    end = int(end.strftime("%y%j"))

    # masked all the images that are not between the limits dates
    alerts = alerts.updateMask(
        alerts.select("Date").gt(start).And(alerts.select("Date").lt(end))
    )

    # create a unique alert band
    alert_band = (
        alerts.select("Alert").remap([0, 1, 2, 3], [0, 0, 2, 1]).rename("alert")
    )

    # change the date format
    date_band = alerts.select("Date").divide(1000).add(2000).rename("date")

    # create the composit image
    all_alerts = alert_band.addBands(date_band)

    return all_alerts


def _from_nrt(aoi, asset):
    "reformat andreas alert sytem to be compatible with the rest of the apps"

    # read the image
    alerts = ee.Image(asset)

    # create a alert mask
    mask = alerts.select("detection_count").neq(0)

    # create a unique alert band
    # only confirmed alerts are taken into account
    # we split confirmed from potential by looking at the number of observations
    alert_band = (
        alerts.select("detection_count").updateMask(mask).rename("alert").uint16()
    )
    alert_band = alert_band.where(alert_band.gte(1).And(alert_band.lt(3)), 2).where(
        alert_band.gte(3), 1
    )

    # create a unique date band
    date_band = alerts.select("first_detection_date").mask(mask)
    year = date_band.floor()
    day = date_band.subtract(year).multiply(365)
    date_band = year.add(day.divide(1000)).rename("date")

    # create the composit image
    all_alerts = alert_band.addBands(date_band)

    return all_alerts


def _from_glad_s(start, end, aoi):
    """reformat the glad-s alerts to fit the module expectation"""

    # extract dates from parameters
    start = datetime.strptime(start, "%Y-%m-%d")
    end = datetime.strptime(end, "%Y-%m-%d")

    # the sources are now stored in a folder like system
    init = "projects/glad/S2alert"

    # select the alerts and mosaic them as image
    alert_band = ee.Image(init + "/alert").selfMask().uint16().rename("alert")
    date_band = ee.Image(init + "/obsDate").selfMask().rename("date")

    # alerts are stored in int : number of days since 2018-12-31
    origin = datetime.strptime("2018-12-31", "%Y-%m-%d")
    start = (start - origin).days
    end = (end - origin).days
    date_band = date_band.updateMask(date_band.gt(start).And(date_band.lt(end)))

    # remap the alerts and mask the alerts
    alert_band = (
        alert_band.remap([0, 1, 2, 3, 4], [0, 2, 2, 1, 1]).updateMask(date_band.mask())
    ).rename("alert")

    # change the date format
    date_band = to_date(date_band).rename("date")

    # create the composit image
    all_alerts = alert_band.addBands(date_band)

    return all_alerts


def convert_to_geopandas(data_list):
    # Extract geometry (coordinates) and properties into separate lists
    geometries = [Point(item["geometry"]["coordinates"]) for item in data_list]
    properties = [item["properties"] for item in data_list]
    gee_ids = [item["id"] for item in data_list]

    # Create a pandas DataFrame from the properties
    df = pd.DataFrame(properties)
    df["gee_id"] = gee_ids
    df["status"] = pd.Series()
    df["before_img"] = pd.Series()
    df["after_img"] = pd.Series()
    df["alert_polygon_dir"] = pd.Series()
    df["area"] = pd.Series()
    df["description"] = pd.Series()
    df["status"] = "Not reviewed"

    # Create a GeoDataFrame by combining the properties with the geometries
    gdf = gpd.GeoDataFrame(df, geometry=geometries)

    # Set the coordinate reference system (CRS) if needed
    gdf.set_crs(epsg=4326, inplace=True)  # Assuming WGS84 (EPSG:4326)

    return gdf


def convert_to_geopandas_old(point_features, polygon_features):
    # Create dictionaries to store the matching points and polygons by id
    point_dict = {f["id"]: f for f in point_features}
    polygon_dict = {f["id"]: f for f in polygon_features}

    # Combine features by id
    combined_features = []

    for feature_id in point_dict.keys():
        if feature_id in polygon_dict:
            point = Point(point_dict[feature_id]["geometry"]["coordinates"])
            polygon = Polygon(polygon_dict[feature_id]["geometry"]["coordinates"][0])

            # Use the common properties
            properties = point_dict[feature_id]["properties"]
            properties["gee_id"] = feature_id
            properties["point"] = point
            properties["bounding_box"] = polygon

            combined_features.append(properties)

    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(combined_features, geometry="point")

    # Add columns
    gdf["status"] = pd.Series()
    gdf["before_img"] = pd.Series()
    gdf["before_img_info"] = pd.Series()
    gdf["after_img"] = pd.Series()
    gdf["after_img_info"] = pd.Series()
    gdf["alert_polygon"] = pd.Series()
    gdf["area_ha"] = pd.Series()
    gdf["description"] = pd.Series()
    gdf["status"] = "Not reviewed"

    # Check result
    return gdf


def convert_to_geopandas(polygon_features):
    # Convert polygon features into GeoDataFrame and calculate centroids
    combined_features = []

    for feature in polygon_features:
        polygon = Polygon(feature["geometry"]["coordinates"][0])

        # Extract properties and add relevant information
        properties = feature["properties"]
        properties["gee_id"] = feature["id"]
        properties["bounding_box"] = polygon
        properties["point"] = polygon.centroid  # Add centroid as 'point'

        combined_features.append(properties)

    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(combined_features, geometry="point")

    # Add additional columns with default values
    gdf["status"] = "Not reviewed"
    gdf["before_img"] = pd.Series(dtype="object")
    gdf["before_img_info"] = pd.Series(dtype="object")
    gdf["after_img"] = pd.Series(dtype="object")
    gdf["after_img_info"] = pd.Series(dtype="object")
    gdf["alert_polygon"] = pd.Series(dtype="object")
    gdf["area_ha"] = pd.Series(dtype="float")
    gdf["description"] = pd.Series(dtype="object")

    # Save gdf to file
    # gdf.set_crs(epsg = '4326', allow_override=True, inplace=True).to_file(gpkg_name, driver='GPKG')

    # Check result
    return gdf


def obtener_datos_gee_parcial(
    aoi_grid,
    alert_raster,
    ee_reducer,
    pixel_size,
    min_alert_size_pixels,
    max_elementos=20,
):
    def get_bb(feature, min_alert_size_pixels):
        grid_geometry = ee.Feature(feature).geometry()
        bounding_boxes = alert_raster.clip(grid_geometry).reduceToVectors(
            ee_reducer,
            grid_geometry,
            pixel_size,
            "bb",
            True,
            None,
            None,
            None,
            True,
            1e13,
            1,
        )
        # Eliminar cluster con menos de x cantidad de pixels
        bb_cleaned = bounding_boxes.filter(
            ee.Filter.gte("count", min_alert_size_pixels)
        )
        return bb_cleaned

    resultados = []

    def procesar_elemento(elemento):
        bb = get_bb(elemento, min_alert_size_pixels)
        # Aquí puedes definir la función de conteo de elementos
        conteo = bb.size().getInfo()
        print(conteo)

        # Si hay elementos, llamar a getInfo() para almacenar los datos
        if conteo > 0:
            info = bb.toList(conteo).getInfo()
            resultados.extend(info)
            print("conteo fue mayor a 0, reusltados es ", len(resultados))

    # Procesar cada elemento en el FeatureCollection hasta que alcancemos max_elementos
    elementos = aoi_grid.toList(aoi_grid.size())
    for i in range(elementos.size().getInfo()):
        if len(resultados) >= max_elementos:
            # print( 'resultado es ', len(resultados))
            break
        elemento = ee.FeatureCollection(elementos.get(i))
        procesar_elemento(elemento)
    # print('Out of loop')
    return resultados


def obtener_datos_gee_total(
    aoi, alert_raster, ee_reducer, pixel_size, min_alert_size_pixels, max_elementos
):

    bounding_boxes = alert_raster.reduceToVectors(
        ee_reducer, aoi, pixel_size, "bb", True, None, None, None, True, 1e13, 1
    )

    # Eliminar cluster con menos de x cantidad de pixels
    bb_cleaned = bounding_boxes.filter(ee.Filter.gte("count", min_alert_size_pixels))

    # Calcular el numero de alertas detectadas
    bb_number_elements = bb_cleaned.size().getInfo()

    if bb_number_elements <= 5000:
        number_export = bb_number_elements
    else:
        number_export = 5000

    if max_elementos > 0:
        number_export = max_elementos
    else:
        number_export = number_export

    # Sort by size, date, etc
    bb_sorted = bb_cleaned.sort("count", False)

    bb_sorted_list = bb_sorted.toList(number_export).getInfo()

    return bb_sorted_list
