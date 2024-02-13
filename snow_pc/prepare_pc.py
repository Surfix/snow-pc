import json
import logging
import os
import shlex
import subprocess
import sys
import time
from datetime import datetime
from glob import glob
from os.path import abspath, basename, dirname, exists, isdir, join, expanduser

import laspy
import py3dep
import pyproj
import rioxarray as rxa
from docopt import docopt
from rasterio.enums import Resampling
from shapely.geometry import box
from shapely.ops import transform

log = logging.getLogger(__name__)


def cl_call(command, log):
    """
    Runs shell commands in python and returns output
    Got this from a stack overflow but can't find it now...

    Parameters:
    command (str or list): list of commands. if string is passed we will try and
    parse to list using shelex
    """
    if type(command) == str:
        command = shlex.split(command)
    log.info('Subprocess: "' + ' '.join(command) + '"')

    process = subprocess.Popen(command, 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)

    while True:
        output = process.stdout.readline()
        log.info(output.strip())
        # Do something else
        return_code = process.poll()
        if return_code is not None:
            log.info(f'RETURN CODE {return_code}')
            # Process has finished, read rest of the output 
            for output in process.stdout.readlines():
                log.info(output.strip())
            break

def replace_white_spaces(parent, replace = ''):
    """Remove any white space in the point cloud files. 

    Args:
        parent (_type_): Parent directory of the point cloud files.
        replace (str, optional): Character to replace the white space. Defaults to ''.
    """
    response = input(f'Warning! About to replace whitespaces with "{replace}"s in {os.path.abspath(parent)} \n Press y to continue...')
    if response.lower() == 'y':
        for path, folders, files in os.walk(parent):
            for f in files:
                os.rename(os.path.join(path, f), os.path.join(path, f.replace(' ', replace)))
            for i in range(len(folders)):
                new_name = folders[i].replace(' ', replace)
                os.rename(os.path.join(path, folders[i]), os.path.join(path, new_name))
                folders[i] = new_name
    else:
        print(f'Passing...')


def las2laz(parent: str):

    # Get a list of all LAS files in the directory
    las_files = [file for file in os.listdir(parent) if file.endswith('.las')]

    # Iterate over each LAS file and convert it to LAZ
    for las_file in las_files:
        input_path = os.path.join(parent, las_file)
        output_path = os.path.join(parent, os.path.splitext(las_file)[0] + '.laz')
        subprocess.run(['pdal', 'translate', input_path, output_path])
        print(f"Converted {input_path} to {output_path}")


def mosaic_laz(in_dir, las_extra_byte_format, log, out_fp = 'unaligned_merged.laz', laz_prefix = ''):
    """
    Generates and run PDAL mosaic command.

    Parameters:
    in_dir (str): fp to directory full of .laz files to mosaic
    out_fp (str) [optional]: out filepath to save [default: ./merge.laz]
    laz_prefix (str) [optional]: prefix to append in case there are .laz files 
    to avoid mosaicing [default: ""]
    Returns:
    mosaic_fp (str): filepath to mosaic output file
    """
    assert isdir(in_dir), f'{in_dir} is not a directory'
    # generate searching command
    if las_extra_byte_format is True:
        in_str = ' '.join(glob(join(in_dir, f'{laz_prefix}*.las')))
    else:
        in_str = ' '.join(glob(join(in_dir, f'{laz_prefix}*.laz')))
    # out fp to save to
    mosaic_fp = join(in_dir, out_fp)
    # set up mosaic command
    mosaic_cmd = f'pdal merge {in_str} {mosaic_fp}'
    log.debug(f"Using mosaic command: {mosaic_cmd}")
    # run mosaic command
    cl_call(mosaic_cmd, log)
    
    return mosaic_fp

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
    log.debug(f"CRS used is {crs}")
    # create transform from wgs84 to las crs
    wgs84 = pyproj.CRS('EPSG:4326')
    project = pyproj.Transformer.from_crs(crs, wgs84 , always_xy=True).transform
    # calculate bounds of las file in wgs84
    utm_bounds = box(hdr.mins[0], hdr.mins[1], hdr.maxs[0], hdr.maxs[1])
    wgs84_bounds = transform(project, utm_bounds)
    # download dem inside bounds
    os.environ["HYRIVER_CACHE_NAME"] = cache_fp
    
    dem_wgs = py3dep.get_map('DEM', wgs84_bounds, resolution=1, crs='EPSG:4326')
    log.debug(f"DEM bounds: {dem_wgs.rio.bounds()}. Size: {dem_wgs.size}")
    # reproject to las crs and save
    dem_utm = dem_wgs.rio.reproject(crs, resampling = Resampling.cubic_spline)
    dem_utm.rio.to_raster(dem_fp)
    log.debug(f"Saved to {dem_fp}")
    return dem_fp, crs, project
