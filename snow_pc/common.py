import os
from glob import glob
import pyproj
import laspy
import py3dep
from shapely.geometry import box
from shapely.ops import transform
from rasterio.enums import Resampling


def download_dem(las_fp, dem_fp = 'dem.tif', cache_fp ='./cache/aiohttp_cache.sqlite'):
    """Download DEM within the bounds of the las file.

    Args:
        las_fp (_type_): Path to the las file.
        dem_fp (str, optional): Filename for the downloaded dem. Defaults to 'dem.tif'.
        cache_fp (str, optional): Cache filepath. Defaults to './cache/aiohttp_cache.sqlite'.

    Returns:
        _type_: The filepath to the downloaded DEM, the crs of the las file, and the transform from the las crs to wgs84. 
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