import os
import json
import subprocess
from os.path import join, dirname, exists

def clip_pc(in_laz, buff_shp, dem_is_geoid, is_canopy = False):
    """Clip the point cloud to a shapefile.

    Args:
        in_laz (_type_): _description_
        buff_shp (_type_): _description_
        dem_is_geoid (_type_): _description_
        is_canopy (bool, optional): _description_. Defaults to False.

    Raises:
        Exception: _description_
    """

    if is_canopy is False:
        clipped_pc = join(dirname(in_laz), 'clipped_pc.laz')
        json_fp = join(dirname(in_laz), 'jsons', 'clip_align.json')

        # create json pipeline for PDAL clip
            # Create .json file for PDAL clip
        json_pipeline = {
            "pipeline": [
                in_laz,
                {
                    "type":"filters.overlay",
                    "dimension":"Classification",
                    "datasource":buff_shp,
                    "layer":"buffered_area",
                    "column":"CLS"
                },
                {
                    "type":"filters.range",
                    "limits":"Classification[42:42]"
                },
                clipped_pc
            ]
        }
        with open(json_fp,'w') as outfile:
            json.dump(json_pipeline, outfile, indent = 2)

        subprocess.run(['pdal', 'pipeline', json_fp])               

        # Check to see if output clipped point cloud was created
        if not exists(clipped_pc):
            raise Exception('Output point cloud not created')

        print('Point cloud clipped to area')