from snow_pc import download_dem
import os
from os.path import dirname, join
import json
import subprocess


#combine the filters into a single function
def terrain_models(laz_fp, outlas = '', outtif = '', dem_fp = '', dem_low = 20, dem_high = 50, mean_k = 20, multiplier = 3):
    """Use filters.dem, filters.mongo, filters.elm, filters.outlier, filters.smrf, and filters.range to filter the point cloud"""
    #get the directory of the file
    results_dir = dirname(laz_fp)
    #create a filepath for the output las and tif file
    if outlas == '':
        outlas = join(results_dir, "dtm.laz")
    if outtif == '':
        outtif = join(results_dir, "dtm.tif")    
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
                "type": "filters.mongo",\
                "expression": {"$and": [\
                {"ReturnNumber": {"$gt": 0}},\
                {"NumberOfReturns": {"$gt": 0}} ] }
            },
            {
                "type": "filters.elm"
            },
            {
                "type": "filters.outlier",\
                "method": "statistical",\
                "mean_k": mean_k,\
                "multiplier": multiplier
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
                "filename": outlas
            },
            {
                "type": "writers.gdal",
                "filename": outtif,
                "resolution": 1.0,
                "output_type": "idw"
            }
        ]
    }
    #create a directory to save the json pipeline
    json_dir =  join(results_dir, 'jsons')
    os.makedirs(json_dir, exist_ok= True)
    json_name = 'dtm_pipeline'
    json_to_use = join(json_dir, f'{json_name}.json')
    #write json pipeline to file
    with open(json_to_use, 'w') as f:
        json.dump(json_pipeline, f)
    #run the json pipeline
    subprocess.run(["pdal", "pipeline", json_to_use])

    return outlas, outtif

def surface_models(laz_fp, outlas = '', outtif = '', dem_fp = '', dem_low = 20, dem_high = 50, mean_k = 20, multiplier = 3):
    """Use filters.dem, filters.mongo, filters.elm, filters.outlier, filters.smrf, and filters.range to filter the point cloud"""
    #get the directory of the file
    results_dir = dirname(laz_fp)
    #create a filepath for the output las and tif file
    if outlas == '':
        outlas = join(results_dir, "dsm.laz")
    if outtif == '':
        outtif = join(results_dir, "dsm.tif")    
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
            {"type": "filters.range",\
            "limits":"returnnumber[1:1]"
            },
            {
                "type": "writers.las",
                "filename": outlas
            },
            {
                "type": "writers.gdal",
                "filename": outtif,
                "resolution": 1.0,
                "output_type": "idw"
            }
        ]
    }
    #create a directory to save the json pipeline
    json_dir =  join(results_dir, 'jsons')
    os.makedirs(json_dir, exist_ok= True)
    json_name = 'dsm_pipeline'
    json_to_use = join(json_dir, f'{json_name}.json')
    #write json pipeline to file
    with open(json_to_use, 'w') as f:
        json.dump(json_pipeline, f)
    #run the json pipeline
    subprocess.run(["pdal", "pipeline", json_to_use])