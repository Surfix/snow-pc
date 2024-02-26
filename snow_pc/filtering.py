from snow_pc import download_dem
import subprocess

def dem_filtering(laz_fp, dem_fp = '', dem_low = 25, dem_high = 35):
    """Use filters.dem to filter the point cloud to the DEM."""
    #download dem using download_dem() if dem_fp is not provided
    if dem_fp == '':
        dem_fp, crs, project = download_dem(laz_fp)

    #create a filepath for the output las file
    out_fp = laz_fp.replace('.laz', '_dem_filtered.laz')

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
    #subprocess to run the json pipeline
    subprocess.run(["pdal", "pipeline", json_pipeline])
    
    return out_fp



