import os
from os.path import abspath, exists, join
import json

def dem1_pipeline(in_fp, outlas, outtif, dem_fp, json_name = 'las2unaligned', json_dir = './jsons', canopy = False):
    """
    Creates JSON Pipeline for standard las point cloud to DTM.
    Filters include: dem, elm, outlier
    SMRF Classifier and writes ground classified points to las and tif

    Parameters:
    in_fp (str): filepath to las file to be run
    outlas (str): filepath to save dtm las
    outtif (str): filepath to save dtm tif
    json_name (str) [optional]: name of json to save [default: las2dem.json]
    json_dir (str) [optional]: name of json subdirectory to create [default: ./json]

    Returns:
    json_to_use (str): filepath of created json pipeline
    """
    ## make sure path is in format pdal likes
    in_fp = abspath(in_fp)
    outlas = abspath(outlas)
    outtif = abspath(outtif)

    assert exists(in_fp), f'In filepath {in_fp} does not exist'
    assert exists(dem_fp), f'DEM filepath {in_fp} does not exist'

    # good docs on types of filters used: https://pdal.io/stages/filters.html#ground-unclassified
    # check this for improvement: https://pdal.io/en/2.6.0/tutorial/ground-filters.html
    # Reads in mosaiced las file
    reader = {"type": "readers.las", "filename": in_fp
    }

    # Filters out points with 0 returns
    mongo_filter = {"type": "filters.mongo",\
        "expression": {"$and": [\
            {"ReturnNumber": {"$gt": 0}},\
                {"NumberOfReturns": {"$gt": 0}} ] } 
    }
    # Filter out points far away from our dem
    dem_filter = {
            "type":"filters.dem",
            "raster":dem_fp,
            "limits":"Z[25:35]"
    }
    # Extended Local Minimum filter
    elm_filter = {"type": "filters.elm"
    }
    # Outlier filter
    outlier_filter = {"type": "filters.outlier",\
        "method": "statistical",\
            "mean_k": 12,\
                "multiplier": 2.2
    }
    # SMRF classifier for ground
    smrf_classifier = {"type": "filters.smrf",\
        "ignore": "Classification[7:7], NumberOfReturns[0:0], ReturnNumber[0:0]"
    }
    # Select ground points only
    smrf_selecter = { 
            "type":"filters.range",
            "limits":"Classification[2:2]"
    }
    # Write las file
    las_writer = {"type": "writers.las",\
#     "where": "Classification[2:2]",\
        "filename":outlas
    }
    # Write tif file
    tif_writer = {"type": "writers.gdal",\
    #     "where": "Classification[2:2]",\
            "filename":outtif,
            "resolution":1.0,
            "output_type":"idw"
    }

    first_returns = {"type": "filters.range",\
            "limits":"returnnumber[1:1]"
    }

    # set up pipeline
    if canopy:
        pipeline = [reader, dem_filter, first_returns, las_writer]
    else:
        pipeline = [reader, mongo_filter, dem_filter, elm_filter, outlier_filter, smrf_classifier,smrf_selecter, las_writer, tif_writer]
    # make json dir and fp
    # log.debug(f"Making JSON dir at {json_dir}")
    os.makedirs(json_dir, exist_ok= True)
    json_name = json_name.replace('.json','')
    json_to_use = join(json_dir, f'{json_name}.json')
    # write json fp out
    with open(json_to_use,'w') as outfile:
        json.dump(pipeline, outfile, indent = 2)
    # add logging message for success #

    return json_to_use

def dem2_pipeline(in_fp, outlas, outtif, dem_fp, json_name = 'las2unaligned', json_dir = './jsons', canopy = False):
    # check this for improvement: https://pdal.io/en/2.6.0/tutorial/ground-filters.html
    pass    

def clip_laz(input_laz, shape_file):
    pass