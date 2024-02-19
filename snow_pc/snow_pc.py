"""Main module."""

import os
from os.path import abspath, basename, dirname, exists, isdir, join, expanduser
import ipyleaflet
import shutil
import json
import logging
from glob import glob
import pyproj
import laspy
import py3dep
import subprocess
from shapely.geometry import box
from shapely.ops import transform
from rasterio.enums import Resampling
import geopandas as gpd


from snow_pc.prepare import replace_white_spaces, las2laz, merge_laz_files
from snow_pc.pipeline import dem1_pipeline, dem2_pipeline


def download_dem(las_fp, dem_fp = 'dem.tif', cache_fp ='./cache/aiohttp_cache.sqlite'):
    """
    Reads the crs and bounds of a las file and downloads a DEM from py3dep
    Must be in the CONUS.

    Parameters:
    las_fp (str): filepath to las file to get bounds and crs
    dem_fp (str) [optional]: filepath to save DEM at. [default = './dem.tif']

    Returns:
    crs (pyproj CRS): CRS object from las header
    project (shapely transform): shapely transform used in conversion
    """
    # read crs of las file
    with laspy.open(las_fp) as las:
        hdr = las.header
        crs = hdr.parse_crs()
    # log.debug(f"CRS used is {crs}")
    # create transform from wgs84 to las crs
    wgs84 = pyproj.CRS('EPSG:4326')
    project = pyproj.Transformer.from_crs(crs, wgs84 , always_xy=True).transform
    # calculate bounds of las file in wgs84
    utm_bounds = box(hdr.mins[0], hdr.mins[1], hdr.maxs[0], hdr.maxs[1])
    wgs84_bounds = transform(project, utm_bounds)
    # download dem inside bounds
    os.environ["HYRIVER_CACHE_NAME"] = cache_fp
    
    dem_wgs = py3dep.get_map('DEM', wgs84_bounds, resolution=1, crs='EPSG:4326')
    # log.debug(f"DEM bounds: {dem_wgs.rio.bounds()}. Size: {dem_wgs.size}")
    # reproject to las crs and save
    dem_utm = dem_wgs.rio.reproject(crs, resampling = Resampling.cubic_spline)
    dem_utm.rio.to_raster(dem_fp)
    # log.debug(f"Saved to {dem_fp}")
    return dem_fp, crs, project

def prepare_pc(in_dir: str, replace: str = ''):
    """Prepare point cloud data for processing.

    Args:
        in_dir (str): Path to the directory containing the point cloud files.
        replace (str, optional): Character to replace the white space. Defaults to ''.

    Returns:
        str: Path to the merged LAZ file.
    """

    # checks on directory and user update
    assert isdir(in_dir), f'Provided: {in_dir} is not a directory. Provide directory with .laz files.'

    #checks if there is at least one file in the directory
    assert len(glob(join(in_dir, '*'))) > 0, f'No files found in {in_dir}'

    #change to the directory
    print(f"Working in directory: {in_dir}")
    os.chdir(in_dir)

    # set up sub directories
    snowpc_dir = join(in_dir, 'snow-pc')
    os.makedirs(snowpc_dir, exist_ok= True)
    results_dir = join(snowpc_dir, 'results')
    os.makedirs(results_dir, exist_ok= True)

    #check and replace white spaces in file paths
    for file in glob(join(in_dir, '*')):
        if ' ' in file:
            print('White spaces found in file paths. Removing...')
            replace_white_spaces(in_dir, replace)
            break

    #check and convert all LAS files to LAZ
    for file in glob(join(in_dir, '*')):
        if file.endswith('.las'):
            print('LAS files found. Converting to LAZ...')
            las2laz(in_dir)
            break
    
    # mosaic
    mosaic_fp = join(results_dir, 'unfiltered_merge.laz')
    merge_laz_files(in_dir, out_fp= mosaic_fp)
    if exists(mosaic_fp):
        return mosaic_fp
    else:
        print(f"Error: Mosaic file not created")

def pc2uncorrectedDEM(laz_fp, dem= '', debug= False):
    """
    Takes a input directory of laz files. Mosaics them, downloads DEM within their bounds,
    builds JSON pipeline, and runs PDAL pipeline of filter, classifying and saving DTM.

    Parameters:
    laz_file (str): filepath to laz file to be run
    debug (bool): lots of yakety yak or not?

    Returns:
    outtif (str): filepath to output DTM tiff
    outlas (str): filepath to output DTM laz file
    """

    #checks that file exists
    assert exists(laz_fp), f'Provided: {laz_fp} does not exist. Provide directory with .laz files.'
    
    #get the directory of the file
    results_dir = dirname(laz_fp)

    # # set up sub directories
    # ice_dir = join(in_dir, 'ice-road')
    # os.makedirs(ice_dir, exist_ok= True)
    # results_dir = join(ice_dir, 'results')
    # os.makedirs(results_dir, exist_ok= True)
    # json_dir =  join(ice_dir, 'jsons')
    # os.makedirs(json_dir, exist_ok= True)

    # check for overwrite
    outtif = join(results_dir, f'unaligned.tif')
    outlas = join(results_dir, f'unaligned.laz')
    canopy_laz = join(results_dir, f'_canopy_unaligned.laz')
    if exists(outtif):
        while True:
            ans_ = input("Uncorrected tif already exists. Enter y to overwrite and n to use existing:")
            if ans_.lower() == 'n':
                return outtif, outlas, canopy_laz
            elif ans_.lower() == 'y':
                break

    # Allowing the code to use user input DEM
    dem_fp = join(results_dir, 'dem.tif')

    if not dem:
        print("Starting DEM download...")
        _, crs, project = download_dem(laz_fp, dem_fp = dem_fp, cache_fp= join(results_dir, 'py3dep_cache', 'aiohttp_cache.sqlite'))
        # log.debug(f"Downloaded dem to {dem_fp}")
    else:
        print("User DEM specified. Skipping DEM download...")
        #copy the user specified dem to the results directory as dem_fp
        shutil.copy(dem, dem_fp)
    if not exists(join(results_dir, 'dem.tif')):
        print('No DEM downloaded')
        return -1
    
    # DTM creation
    print("Creating DTM Pipeline...")
    json_dir =  join(results_dir, 'jsons')
    os.makedirs(json_dir, exist_ok= True)
    json_to_use = dem1_pipeline(in_fp = laz_fp, outlas = outlas, outtif = outtif, dem_fp = dem_fp, json_dir = json_dir)
    # log.debug(f"JSON to use is {json_to_use}")

    print("Running DTM pipeline")
    if debug == True:
        pipeline_cmd = f'pdal pipeline -i {json_to_use} -v 8'
    else:
        pipeline_cmd = f'pdal pipeline -i {json_to_use}'
    subprocess.run(pipeline_cmd, shell=True)
    # cl_call(pipeline_cmd, log)

    # DSM creation
    print("Creating Canopy Pipeline...")
    json_to_use = dem1_pipeline(in_fp = laz_fp, outlas = canopy_laz, \
        outtif = canopy_laz.replace('laz','tif'), dem_fp = dem_fp, json_dir = json_dir, canopy = True,\
        json_name='canopy')
    # log.debug(f"JSON to use is {json_to_use}")
    print("Running Canopy pipeline")
    if debug == True:
        pipeline_cmd = f'pdal pipeline -i {json_to_use} -v 8'
    else:
        pipeline_cmd = f'pdal pipeline -i {json_to_use}'
    subprocess.run(pipeline_cmd, shell=True)

    # log.info("Running Canopy pipeline")
    # if debug:
    #     pipeline_cmd = f'pdal pipeline -i {json_to_use} -v 8'
    # else:
    #     pipeline_cmd = f'pdal pipeline -i {json_to_use}'
    # cl_call(pipeline_cmd, log)


    # end_time = datetime.now()
    # log.info(f"Completed! Run Time: {end_time - start_time}")

    return outtif, outlas, canopy_laz

# def clip_align(input_laz, buff_shp, result_dir, json_dir, dem_is_geoid, asp_dir, final_tif, is_canopy=False, las_extra_byte_format=False):
        

#         # Have is_canopy flag to avoid running twice...
#         if is_canopy is False:     
#             # Clip clean_PC to the transform_area using PDAL
#             # input_laz = join(result_dir, basename(in_dir)+'_unaligned.laz')
#             clipped_pc = join(result_dir, 'clipped_PC.laz')
#             json_path = join(json_dir, 'clip_to_shp.json')

#             # Create .json file for PDAL clip
#             json_pipeline = {
#                 "pipeline": [
#                     input_laz,
#                     {
#                         "type":"filters.overlay",
#                         "dimension":"Classification",
#                         "datasource":buff_shp,
#                         "layer":"buffered_area",
#                         "column":"CLS"
#                     },
#                     {
#                         "type":"filters.range",
#                         "limits":"Classification[42:42]"
#                     },
#                     clipped_pc
#                 ]
#             }
#             with open(json_path,'w') as outfile:
#                 json.dump(json_pipeline, outfile, indent = 2)

#             #cl_call(f'pdal pipeline {json_path}', log)               

#             # Check to see if output clipped point cloud was created
#             if not exists(clipped_pc):
#                 raise Exception('Output point cloud not created')

#             print('Point cloud clipped to area')

#         # Define paths for next if statement
#         in_dem = join(result_dir, 'dem.tif')
        
#         if dem_is_geoid is True:
#             # ASP needs NAVD88 conversion to be in NAD83 (not WGS84)
#             nad83_dem = join(result_dir, 'demNAD_tmp.tif')
#             gdal_func = join(asp_dir, 'gdalwarp')

#             subprocess.run([gdal_func, '-t_srs', 'EPSG:26911', in_dem, nad83_dem])
#             # Use ASP to convert from geoid to ellipsoid
#             ellisoid_dem = join(result_dir, 'dem_wgs')
#             geoid_func = join(asp_dir, 'dem_geoid')
#             cl_call(f'{geoid_func} --nodata_value -9999 {nad83_dem} \
#                     --geoid NAVD88 --reverse-adjustment -o {ellisoid_dem}', log)
#             # Set it back to WGS84
#             ref_dem = join(result_dir, 'ellipsoid_DEM.tif')
#             cl_call(f'{gdal_func} -t_srs EPSG:32611 {ellisoid_dem}-adj.tif {ref_dem}', log)

#             # check for success
#             if not exists(ref_dem):
#                 raise Exception('Conversion to ellipsoid failed')

#             log.info('Merged DEM converted to ellipsoid per user input')

#         else:
#             # cl_call('cp '+ in_dem +' '+ ref_dem, log)
#             ref_dem = in_dem
#             log.info('Merged DEM was kept in original ellipsoid form...')

#         # Call ASP pc_align function on road and DEM and output translation/rotation matrix
#         align_pc = join(result_dir,'pc-align',basename(final_tif))
#         pc_align_func = join(asp_dir, 'pc_align')

#         # Have is_canopy flag to avoid running twice...
#         if is_canopy is False:     
#             log.info('Beginning pc_align function...')
#             cl_call(f'{pc_align_func} --max-displacement 5 --highest-accuracy \
#                         {ref_dem} {clipped_pc} -o {align_pc}', log)
        
#         # Since there are issues in transforming the point cloud and retaining reflectance,
#         # the best I can do is translation only and no rotation..
#         # Therefore, in this section, if the mode is set to calc SSA, an additional pc_align 
#         # will be called in order to save the X,Y,Z translation only. This will not be applied
#         # to the snow depth products, so there may be some subtle differences when comparing between the two. 
#         # However, this is in hopes to retain the higher information where we can..
#         # --compute-translation-only
#         if las_extra_byte_format is True and is_canopy is False:
#             transform_pc_temp = join(result_dir,'pc-align-translation-only','temp')
#             cl_call(f'{pc_align_func} --max-displacement 5 --highest-accuracy \
#                     --compute-translation-only   \
#                         {ref_dem} {clipped_pc}   \
#                         -o {transform_pc_temp}', log)     
            

#         # Apply transformation matrix to the entire laz and output points
#         # https://groups.google.com/g/ames-stereo-pipeline-support/c/XVCJyXYXgIY/m/n8RRmGXJFQAJ
#         transform_pc = join(result_dir,'pc-transform',basename(final_tif))
#         cl_call(f'{pc_align_func} --max-displacement -1 --num-iterations 0 \
#                     --initial-transform {align_pc}-transform.txt \
#                     --save-transformed-source-points                            \
#                     {ref_dem} {input_laz}   \
#                     -o {transform_pc}', log)

#         # Grid the output to a 0.5 meter tif (NOTE: this needs to be changed to 1m if using py3dep)
#         point2dem_func = join(asp_dir, 'point2dem')
#         # final_tif = join(ice_dir, 'pc-grid', 'run')
#         cl_call(f'{point2dem_func} {transform_pc}-trans_source.laz \
#                     --dem-spacing 0.5 --search-radius-factor 2 -o {final_tif}', log)
    
#         return final_tif + '-DEM.tif'

# def dem_align(input_laz, 
#               canopy_laz, 
#               laz_fp, 
#               align_shp = 'transform_area/hwy_21/hwy_21_utm_edit_v2.shp', 
#               buffer_meters = 3.0, 
#               dem_is_geoid = False):
    
#     #get the directory of the file
#     results_dir = dirname(laz_fp)
#     json_dir =  join(results_dir, 'jsons')
#     os.makedirs(json_dir, exist_ok= True)

#     print('Starting ASP Alignment...\n Loading in shapefile')
#     gdf = gpd.read_file(align_shp)
#     #check that gdf is in UTM
#     assert gdf.crs.is_projected, f'Provided shapefile is not in a projected coordinate system. Please provide a shapefile in a projected coordinate system.'
#     #check that gdf crs is same as las crs
#     with laspy.open(laz_fp) as las:
#         hdr = las.header
#         crs = hdr.parse_crs()
#     assert gdf.crs == crs, f'Provided shapefile is not in the same coordinate system as the las file. Please provide a shapefile in the same coordinate system as the las file.'
    
#     # Buffer geom based on user input. NOTE: we assume buffer_meters is the entire width. 
#     # So, must divide by 2 here to get the right distance from centerline.
#     print(f'Buffer width of {buffer_meters} m is used. This is {buffer_meters / 2} m from centerline.')
#     gdf['geometry'] = gdf.geometry.buffer(buffer_meters / 2)

#     # Create a new attribute to be used for PDAL clip/overlay
#     gdf['CLS'] = 42

#     # Save buffered shpfile to directory we just made
#     buff_shp = join(results_dir, 'buffered_area.shp')
#     gdf.to_file(buff_shp)

#     #make a subdirectory for the products in the results directory
#     products_dir = join(results_dir, 'products')
#     os.makedirs(products_dir, exist_ok= True)

#     # create a file path for the aligned snow and canopy products
#     snow_final_tif = join(products_dir, 'snow')
#     canopy_final_tif = join(products_dir, 'canopy')

#     if exists(snow_final_tif + '.tif') and exists(canopy_final_tif + '.tif'):
#         while True:
#             ans_ = input("Aligned tif already exists. Enter y to overwrite and n to use existing:")
#             if ans_.lower() == 'n':
#                 return snow_final_tif + '.tif', canopy_final_tif+ '.tif'
#             elif ans_.lower() == 'y':
#                 break

#     snow_tif = clip_align(input_laz=input_laz, buff_shp=buff_shp, result_dir=products_dir,\
#         json_dir=json_dir, dem_is_geoid=dem_is_geoid, asp_dir=asp_dir,\
#         final_tif = snow_final_tif, is_canopy=False)

#     canopy_tif = clip_align(input_laz=canopy_laz, buff_shp=buff_shp, result_dir=products_dir,\
#         json_dir=json_dir, dem_is_geoid=dem_is_geoid, asp_dir=asp_dir,\
#         final_tif = canopy_final_tif, is_canopy=True)

#     # For some reason this is returning 1 when a product IS created..
#     if not exists(snow_tif):
#        print(f'Can not find {snow_tif}')
#        raise Exception('No final product created')

#     return snow_tif, canopy_tif



def laz2uncorectedDEM(in_dir, dem_fp = '', debug = False):
    """Converts laz files to uncorrected DEM.

    Args:
        in_dir (str): Path to the directory containing the point cloud files.
        dem_fp (str, optional): Path to the DEM file. Defaults to ''.
        debug (bool, optional): Debug mode. Defaults to False.

    Returns:
    outtif (str): filepath to output DTM tiff
    outlas (str): filepath to output DTM laz file
    """

    # prepare point cloud
    laz_fp = prepare_pc(in_dir)

    # create uncorrected DEM
    outtif, outlas, canopy_laz = pc2uncorrectedDEM(laz_fp, dem_fp, debug)

    return outtif, outlas, canopy_laz

def laz2correctedDEM(in_dir, align_shp, dem_fp = '', debug = False):
    """Converts laz files to corrected DEM.

    Args:
        in_dir (str): Path to the directory containing the point cloud files.
        align_shp (str): Path to the shapefile to align the point cloud to.
        dem_fp (str, optional): Path to the DEM file. Defaults to ''.
        debug (bool, optional): Debug mode. Defaults to False.

    Returns:
    outtif (str): filepath to output DTM tiff
    outlas (str): filepath to output DTM laz file
    """

    # prepare point cloud
    laz_fp = prepare_pc(in_dir)

    # create uncorrected DEM
    outtif, outlas, canopy_laz = pc2uncorrectedDEM(laz_fp, dem_fp, debug)

    # # align the point cloud
    # snow_tif, canopy_tif = dem_align(laz_fp, align_shp, dem_fp, debug)

    # return snow_tif, canopy_tif


class Map(ipyleaflet.Map):
    """Custom map class that inherits from ipyleaflet.Map.
    """
    def __init__(self, *args, **kwargs):

        if "scroll_wheel_zoom" not in kwargs:
            kwargs["scroll_wheel_zoom"] = True
        super().__init__(*args, **kwargs)

        if "layers_control" not in kwargs:
            kwargs["layers_control"] = True

        if kwargs["layers_control"]:
            self.add_LayerControl()

        if "fullscreen_control" not in kwargs:
            kwargs["fullscreen_control"] = True

        if kwargs["fullscreen_control"]:
            self.add_fullscreen_control()            

    def add_search_control(self, position = "topleft", **kwargs):
        """Add a search control to the map.

        Args:
            position (str, optional): Position of the search control. Defaults to "topleft".

        Returns:
            _type_: SearchControl object.
        """
        if "url" not in kwargs:
            kwargs["url"] = "https://nominatim.openstreetmap.org/search?format=json&q={s}"
        search = ipyleaflet.SearchControl(position = position, **kwargs)
        self.add_control(search)
        return search

    def add_LayerControl(self, position = "topright"):
        """Add a layer control to the map.

        Args:
            position (str, optional): Position of the layer control. Defaults to "topright".

        Returns:
            _type_: LayerControl object.
        """
        layer_control = ipyleaflet.LayersControl(position = position)
        self.add_control(layer_control)
        return layer_control
    
    def add_fullscreen_control(self, position = "topright"):
        """Add a fullscreen control to the map.

        Args:
            position (str, optional): Position of the fullscreen control. Defaults to "topright".

        Returns:
            _type_: FullscreenControl object.
        """
        fullscreen = ipyleaflet.FullScreenControl(position = position)
        self.add_control(fullscreen)
        return fullscreen
    
    def add_tile_layer(self, url, name, **kwargs):
        """Add a tile layer to the map.

        Args:
            url (str): URL of the tile layer.

        Returns:
            _type_: TileLayer object.
        """
        tile_layer = ipyleaflet.TileLayer(url = url, name=name, **kwargs)
        self.add_layer(tile_layer)
        return tile_layer
    
    def add_basemap(self, basemap, **kwargs):
        """Add a basemap to the map.

        Args:
            basemap (_type_): A string representing the basemap to add.

        Raises:
            ValueError: If the basemap is not recognized.
        """
        import xyzservices.providers as xyz
        if basemap.lower() == "openstreetmap":
            url = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            self.add_tile_layer(url, name = basemap,**kwargs)
        elif basemap.lower() == "stamen terrain":
            url = "https://stamen-tiles-{s}.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png"
            self.add_tile_layer(url, name = basemap,**kwargs)
        elif basemap.lower() == "opentopomap":
            url = "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"
            self.add_tile_layer(url, name = basemap,**kwargs)
        elif basemap.lower() == "satellite":
            url = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            self.add_tile_layer(url, name = basemap,**kwargs)

        else:
            try:
                basemap = eval(f"xyz.{basemap}")
                url = basemap.build_url()
                name = basemap["name"]
                attribute = basemap["attribution"]
                print(url, name)
                self.add_tile_layer(url, name, attribution = attribute, **kwargs)
            except:
                raise ValueError(f"Basemap {basemap} not recognized.")

    def add_geojson(self, data, name = "geojson", **kwargs):
        """Add a GeoJSON layer to the map.

        Args:
            data (_type_): A GeoJSON object.

        Returns:
            _type_: GeoJSON object.
        """

        if isinstance(data, str):
            import json
            with open(data, 'r') as f:
                data = json.load(f)
        geojson = ipyleaflet.GeoJSON(data = data, name = name, **kwargs)
        self.add_layer(geojson)
        return geojson
    
    def add_shp(self, data, name = "shapefile", **kwargs):
        """Add a shapefile to the map.

        Args:
            data (_type_): A shapefile object.

        Returns:
            _type_: GeoData object.
        """
        gdf = gpd.read_file(data)
        geojson = gdf.__geo_interface__
        self.add_geojson(geojson, name = name, **kwargs)
        
        
