import os
from os.path import dirname, join
import json
import subprocess
from snow_pc.common import download_dem, make_dirs

def return_filtering(laz_fp):
    """Use filters.mongo to filter out points with invalid returns.

    Args:
        laz_fp (_type_): Filepath to the point cloud file.

    Returns:
        _type_: Filepath to the filtered point cloud file.
    """
    #get the directory of the file
    results_dir = make_dirs(laz_fp)
    #create a filepath for the output las file
    out_fp = join(results_dir, "returns_filtered.laz")
    #create a json pipeline for pdal
    json_pipeline = {
        "pipeline": [
            {
                "type": "readers.las",
                "filename": laz_fp
            },
            {
                "type": "filters.mongo",\
                "expression": {"$and": [\
                {"ReturnNumber": {"$gt": 0}},\
                {"NumberOfReturns": {"$gt": 0}} ] }
            },
            {
                "type": "writers.las",
                "filename": out_fp
            }
        ]
    }
    #create a directory to save the json pipeline
    json_dir =  join(results_dir, 'jsons')
    os.makedirs(json_dir, exist_ok= True)
    json_name = 'return_filtering'
    json_to_use = join(json_dir, f'{json_name}.json')
    #write json pipeline to file
    with open(json_to_use, 'w') as f:
        json.dump(json_pipeline, f)
    #run the json pipeline
    subprocess.run(["pdal", "pipeline", json_to_use])

    return out_fp

def dem_filtering(laz_fp, dem_fp = '', dem_low = 20, dem_high = 50):
    """Use filters.dem to filter the point cloud to the DEM. 

    Args:
        laz_fp (_type_): Filepath to the point cloud file.
        dem_fp (str, optional): Filepath to the DEM file. Defaults to ''.
        dem_low (int, optional): Lower limit of the DEM. Defaults to 20.
        dem_high (int, optional): Upper limit of the DEM. Defaults to 50.

    Returns:
        _type_: Filepath to the filtered point cloud file.
    """
    #download dem using download_dem() if dem_fp is not provided
    if dem_fp == '':
        dem_fp, crs, project = download_dem(laz_fp)
    #get the directory of the file
    results_dir = make_dirs(laz_fp)
    #create a filepath for the output las file
    out_fp = join(results_dir, "dem_filtered.laz")
    #create a json pipeline for pdal
    json_pipeline = {
        "pipeline": [
            {
                "type": "readers.las",
                "filename": laz_fp
            },
            {
                "type": "filters.dem",
                "raster": dem_fp,
                "limits": f"Z[{dem_low}:{dem_high}]"
            },
            {
                "type": "writers.las",
                "filename": out_fp
            }
        ]
    }
    #create a directory to save the json pipeline
    json_dir =  join(results_dir, 'jsons')
    os.makedirs(json_dir, exist_ok= True)
    json_name = 'dem_filtering'
    json_to_use = join(json_dir, f'{json_name}.json')
    #write json pipeline to file
    with open(json_to_use, 'w') as f:
        json.dump(json_pipeline, f)
    #run the json pipeline
    subprocess.run(["pdal", "pipeline", json_to_use], shell=True)

    return out_fp

def elm_filtering(laz_fp):
    """Use filters.elm to filter the point cloud.

    Args:
        laz_fp (_type_): Filepath to the point cloud file.

    Returns:
        _type_: Filepath to the filtered point cloud file.
    """
    #get the directory of the file
    results_dir = make_dirs(laz_fp)
    #create a filepath for the output las file
    out_fp = join(results_dir, "elm_filtered.laz")
    #create a json pipeline for pdal
    json_pipeline = {
        "pipeline": [
            {
                "type": "readers.las",
                "filename": laz_fp
            },
            {
                "type": "filters.elm"
            },
            {
                "type": "writers.las",
                "filename": out_fp
            }
        ]
    }
    #create a directory to save the json pipeline
    json_dir =  join(results_dir, 'jsons')
    os.makedirs(json_dir, exist_ok= True)
    json_name = 'elm_filtering'
    json_to_use = join(json_dir, f'{json_name}.json')
    #write json pipeline to file
    with open(json_to_use, 'w') as f:
        json.dump(json_pipeline, f)
    #run the json pipeline
    subprocess.run(["pdal", "pipeline", json_to_use])

    return out_fp

def outlier_filtering(laz_fp, mean_k = 20, multiplier = 3):
    """Use filters.outlier to filter the point cloud.

    Args:
        laz_fp (_type_): Filepath to the point cloud file.
        mean_k (int, optional): _description_. Defaults to 20.
        multiplier (int, optional): _description_. Defaults to 3.

    Returns:
        _type_: Filepath to the filtered point cloud file.
    """
    #get the directory of the file
    results_dir = make_dirs(laz_fp)
    #create a filepath for the output las file
    out_fp = join(results_dir, "outlier_filtered.laz")
    #create a json pipeline for pdal
    json_pipeline = {
        "pipeline": [
            {
                "type": "readers.las",
                "filename": laz_fp
            },
            {
                "type": "filters.outlier",\
                "method": "statistical",\
                "mean_k": mean_k,\
                "multiplier": multiplier
            },
            {
                "type": "writers.las",
                "filename": out_fp
            }
        ]
    }
    #create a directory to save the json pipeline
    json_dir =  join(results_dir, 'jsons')
    os.makedirs(json_dir, exist_ok= True)
    json_name = 'outlier_filtering'
    json_to_use = join(json_dir, f'{json_name}.json')
    #write json pipeline to file
    with open(json_to_use, 'w') as f:
        json.dump(json_pipeline, f)
    #run the json pipeline
    subprocess.run(["pdal", "pipeline", json_to_use])

    return out_fp

def ground_segmentation(laz_fp):
    """Use filters.smrf and filters.range to segment ground points.

    Args:
        laz_fp (_type_): Filepath to the point cloud file.

    Returns:
        _type_: Filepath to the segmented point cloud file.
    """
    #get the directory of the file
    results_dir = make_dirs(laz_fp)
    #create a filepath for the output las file
    out_fp = join(results_dir, "ground_segmented.laz")
    out_fp2 = join(results_dir, "ground_segmented.tif")
    #create a json pipeline for pdal
    json_pipeline = {
        "pipeline": [
            {
                "type": "readers.las",
                "filename": laz_fp
            },
            {
                "type": "filters.smrf",\
                "ignore": "Classification[7:7], NumberOfReturns[0:0], ReturnNumber[0:0]"
            },
            {
                "type": "filters.range",
                "limits": "Classification[2:2]"
            },
            {
                "type": "writers.las",
                "filename": out_fp
            },
            {
                "type": "writers.gdal",
                "filename": out_fp2,
                "resolution": 1.0,
                "output_type": "idw"
            }
        ]
    }
    #create a directory to save the json pipeline
    json_dir =  join(results_dir, 'jsons')
    os.makedirs(json_dir, exist_ok= True)
    json_name = 'ground_segmentation'
    json_to_use = join(json_dir, f'{json_name}.json')
    #write json pipeline to file
    with open(json_to_use, 'w') as f:
        json.dump(json_pipeline, f)
    #run the json pipeline
    subprocess.run(["pdal", "pipeline", json_to_use])

    return out_fp, out_fp2

def surface_segmentation(laz_fp):
    """Use filters.range to segment the surface points.

    Args:
        laz_fp (_type_): Filepath to the point cloud file.

    Returns:
        _type_: Filepath to the segmented point cloud file.
    """
    #get the directory of the file
    results_dir = make_dirs(laz_fp)
    #create a filepath for the output las file
    out_fp = join(results_dir, "surface_segmented.laz")
    out_fp2 = join(results_dir, "surface_segmented.tif")
    #create a json pipeline for pdal
    json_pipeline = {
        "pipeline": [
            {
                "type": "readers.las",
                "filename": laz_fp
            },
            {
                "type": "filters.range",
                "limits": "returnnumber[1:1]"
            },
            {
                "type": "writers.las",
                "filename": out_fp
            },
            {
                "type": "writers.gdal",
                "filename": out_fp2,
                "resolution": 1.0,
                "output_type": "idw"
            }
        ]
    }
    #create a directory to save the json pipeline
    json_dir =  join(results_dir, 'jsons')
    os.makedirs(json_dir, exist_ok= True)
    json_name = 'surface_segmentation'
    json_to_use = join(json_dir, f'{json_name}.json')
    #write json pipeline to file
    with open(json_to_use, 'w') as f:
        json.dump(json_pipeline, f)
    #run the json pipeline
    subprocess.run(["pdal", "pipeline", json_to_use])

    return out_fp, out_fp2