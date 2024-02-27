from snow_pc import download_dem
import os
from os.path import dirname, join
import json
import subprocess

def dem_filtering(laz_fp, dem_fp = '', dem_low = 20, dem_high = 50):
    """Use filters.dem to filter the point cloud to the DEM."""
    #download dem using download_dem() if dem_fp is not provided
    if dem_fp == '':
        dem_fp, crs, project = download_dem(laz_fp)
    #get the directory of the file
    results_dir = dirname(laz_fp)
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

def return_filtering(laz_fp):
    """Use filters.range to filter the point cloud ......"""
    #get the directory of the file
    results_dir = dirname(laz_fp)
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

def elm_filtering(laz_fp):
    """Use filters.elm to filter low points as noise"""
    #get the directory of the file
    results_dir = dirname(laz_fp)
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
    """Use filters.outlier to filter out noise"""
    #get the directory of the file
    results_dir = dirname(laz_fp)
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
    """Use filters.smrf and filters.range to segment ground points"""
    #get the directory of the file
    results_dir = dirname(laz_fp)
    #create a filepath for the output las file
    out_fp = join(results_dir, "ground_segmented.laz")
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

    return out_fp
