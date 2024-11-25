import pandas as pd
import geopandas as gpd
import ee
import geemap
import os
import pathlib
import zipfile
import ast
import numpy as np
from datetime import datetime
import json
from component.parameter import directory


def generate_recipe_string():
    # Get the current date and time
    current_time = datetime.now()
    # Format the string as 'recipe_YYYY-MM-DD-HHMMSS'
    recipe_string = current_time.strftime("recipe_%Y-%m-%d-%H%M%S")
    return recipe_string


def create_directory(folder_name):
    """
    Creates a directory with the given folder name.
    If the directory already exists, it will notify the user.

    Args:
        folder_name (str): The name of the directory to create.

    Returns:
        str: The path of the created or existing directory.
    """

    try:
        folder = directory.module_dir / folder_name
        folder_temp = directory.module_dir / "temp"
        folder.mkdir(parents=True, exist_ok=True)
        folder_temp.mkdir(parents=True, exist_ok=True)
        # print(f"Directory '{folder_name}' created successfully.")
    except Exception as e:
        print(f"An error occurred while creating the directory: {e}")

    return os.path.abspath(folder)


def save_model_parameters_to_json(
    file_name,
    aux_model,
    aoi_date_model,
    alert_filter_model,
    selected_alerts_model,
    analyzed_alerts_model,
    app_tile_model,
):
    """
    Saves the variables (parameters) of models to a JSON file.

    Args:
        file_name (str): The name of the JSON file to save the parameters.

    Returns:
        str: The path of the created JSON file.
    """
    a = aux_model.export_dictionary()  # .update(model_parameters)
    b = aoi_date_model.export_dictionary()  # .update(model_parameters)
    c = selected_alerts_model.export_dictionary()  # .update(model_parameters)
    d = analyzed_alerts_model.export_dictionary()  # .update(model_parameters)
    e = app_tile_model.export_dictionary()  # .update(model_parameters)

    model_parameters = a | b | c | d | e
    # model_parameters = {key: value for d in (a, b, c, d, e) for key, value in d.items()}

    print(a, b, c, d, e, model_parameters)

    ##File path to save the JSON file
    file_path = file_name

    # Save dictionary to JSON file
    with open(file_path, "w") as json_file:
        json.dump(model_parameters, json_file)

    return file_path


def load_parameters_from_json(
    file_name,
    aux_model,
    aoi_date_model,
    selected_alerts_model,
    analyzed_alerts_model,
    app_tile_model,
    aoi_tile,
    alert_filter_tile,
):
    """
    Loads variables (parameters) from a JSON file and applies them to the models.

    Args:
        models (dict): A dictionary where keys are model names (str) and values are model objects.
        file_name (str): The name of the JSON file to load parameters from.

    Returns:
        None
    """

    # Read JSON file
    with open(file_name, "r") as json_file:
        model_parameters = json.load(json_file)

    recipe_directory = model_parameters.get("recipe_folder", self.recipe_folder)
    aux_model.import_from_dictionary(model_parameters)
    aoi_tile.load_saved_parameters(model_parameters)
    aoi_tile.process_alerts()
    alert_filter_tile.load_saved_parameters(model_parameters)
    (
        alert_source,
        user_min_alert_size,
        alert_area_selection,
        alert_sorting_method,
        user_max_number_alerts,
        user_selection_polygon,
    ) = check_alert_filter_inputs(alert_filter_tile)
    alert_filter_tile.create_filtered_alert_raster(
        alert_source,
        user_min_alert_size,
        alert_area_selection,
        alert_sorting_method,
        user_max_number_alerts,
        user_selection_polygon,
    )
    analyzed_alerts_model.alerts_gdf = gpd.reaf_file(
        recipe_directory + "/alert_db.gpkg"
    )
    analyzed_alerts_model.actual_alert_id = model_parameters.get(
        "actual_alert_id", self.actual_alert_id
    )
    app_tile_model.load_saved_parameters(model_parameters)
    app_tile_model.current_page_view = "analysis_tile"