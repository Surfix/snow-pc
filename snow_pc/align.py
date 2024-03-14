import os
import json
import subprocess
import geopandas as gpd
from os.path import join, dirname, exists

def clip_pc(laz_fp, align_shp, buffer_width = 3):
    """Clip the point cloud to a shapefile.

    Args:
        laz_fp (_type_): _description_
        buff_shp (_type_): _description_
        dem_is_geoid (_type_): _description_
        is_canopy (bool, optional): _description_. Defaults to False.

    Raises:
        Exception: _description_
    """
    #set the working directory
    in_dir = os.path.dirname(laz_fp)
    os.chdir(in_dir)

    #create a buffer around the shapefile to clip the point cloud
    gdf = gpd.read_file(align_shp)
    gdf['geometry'] = gdf.geometry.buffer(buffer_width / 2) #The buffer_width is the entire width. So, must divide by 2 here to get the right distance from centerline.
    gdf['CLS'] = 42 # Create a new attribute to be used for PDAL clip/overlay
    buff_shp = join(in_dir, 'buffered_area.shp')
    gdf.to_file(buff_shp)

    clipped_pc = join(in_dir, 'clipped_pc.laz')
    json_fp = join(in_dir, 'jsons', 'clip_align.json')


    # Create .json file for PDAL clip
    json_pipeline = {
        "pipeline": [
            laz_fp,
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