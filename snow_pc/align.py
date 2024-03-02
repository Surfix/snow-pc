import os
import json
from os.path import join, dirname, exists

def clip_pc(in_laz, buff_shp, dem_is_geoid, is_canopy = False):

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

        #cl_call(f'pdal pipeline {json_path}', log)               

        # Check to see if output clipped point cloud was created
        if not exists(clipped_pc):
            raise Exception('Output point cloud not created')

        print('Point cloud clipped to area')