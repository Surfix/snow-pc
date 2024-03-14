import os
import json
import subprocess
import geopandas as gpd
from os.path import dirname, join, exists, basename, abspath 

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
    in_dir = dirname(laz_fp)
    os.chdir(in_dir)

    #create a buffer around the shapefile to clip the point cloud
    gdf = gpd.read_file(align_shp)
    gdf['geometry'] = gdf.geometry.buffer(buffer_width / 2) #The buffer_width is the entire width. So, must divide by 2 here to get the right distance from centerline.
    gdf['CLS'] = 22 # Create a new attribute to be used for PDAL clip/overlay
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
                "limits":"Classification[22:22]"
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

def clip_align(laz_fp, buff_shp, align_path, asp_dir, dem_is_geoid = False):
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
    in_dir = dirname(laz_fp)

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
                "limits":"Classification[22:22]"
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
    
    # set the dem file path
    dem_fp = join(in_dir, 'dem.tif')
    ref_dem = dem_fp

    #There is need to convert the dem to ellipsoid if it is in geoid


    #call asp pc_align function on road and DEM and output translation/rotation matrix
    align_pc = join(in_dir,'pc-align',basename(align_path)) #set the align files name format
    pc_align_func = join(asp_dir, 'pc_align') #set the path to the pc_align function
    subprocess.run([pc_align_func, '--max-displacement', 5, '--highest-accuacy', ref_dem, clipped_pc, '-o', align_pc]) #run the pc_align function

    # Apply transformation matrix to the entire laz and output points
    initial_tansform = join(align_pc, '-transform.txt') #set the transform files name format
    transform_pc = join(in_dir,'pc-transform',basename(align_path))
    subprocess.run([pc_align_func, '--max-displacement', -1, '--num-iterations', 0, '--initial-transform', initial_tansform, '--save-transformed-source-points', ref_dem, laz_fp,'-o', transform_pc])

    # Grid the output to a 0.5 meter tif (NOTE: this needs to be changed to 1m if using py3dep)
    transform_laz = join(transform_pc, '-transformed.laz')
    point2dem_func = join(asp_dir, 'point2dem')
    subprocess.run([point2dem_func, transform_laz,'--dem-spacing', 0.5, '--search-radius-factor', 2, '-o', align_path])

    return align_path + '-DEM.tif'

def laz_align(laz_fp, align_shp, asp_dir, buffer_width = 3, dem_is_geoid = False):
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
    in_dir = dirname(laz_fp)

    #create a buffer around the shapefile to clip the point cloud
    gdf = gpd.read_file(align_shp)
    gdf['geometry'] = gdf.geometry.buffer(buffer_width / 2) #The buffer_width is the entire width. So, must divide by 2 here to get the right distance from centerline.
    gdf['CLS'] = 22 # Create a new attribute to be used for PDAL clip/overlay
    buff_shp = join(in_dir, 'buffered_area.shp')
    gdf.to_file(buff_shp)

    #remove .tif of the laz_fp path and add -align to the end
    align_path = laz_fp.replace('.laz', '-align')

    #set asp_dir
    asp_dir = abspath(asp_dir)
    if basename(asp_dir) != 'bin':
        asp_dir = join(asp_dir, 'bin')

    align_tif = clip_align(laz_fp, buff_shp=buff_shp, align_path= align_path,  asp_dir = asp_dir, dem_is_geoid = False)

    return align_tif






    