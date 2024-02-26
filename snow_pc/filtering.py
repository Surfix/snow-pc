from snow_pc import download_dem
import os
from os.path import dirname, join
import json
import subprocess

def dem_filtering(laz_fp, dem_fp = '', dem_low = 25, dem_high = 35):
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
    subprocess.run(["pdal", "pipeline", json_to_use])

    return out_fp



