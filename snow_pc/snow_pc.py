"""Main module."""

import os
from os.path import abspath, basename, dirname, exists, isdir, join, expanduser
import ipyleaflet
import json
import logging
from glob import glob

from snow_pc.prepare import replace_white_spaces, las2laz, merge_laz_files



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

    #checks if there is atleast one file in the directory
    assert len(glob(join(in_dir, '*'))) > 0, f'No files found in {in_dir}'

    #change to the directory
    print(f"Working in directory: {in_dir}")
    os.chdir(in_dir)

    # set up sub directories
    ice_dir = join(in_dir, 'snow-pc')
    os.makedirs(ice_dir, exist_ok= True)
    results_dir = join(ice_dir, 'results')
    os.makedirs(results_dir, exist_ok= True)
    json_dir =  join(ice_dir, 'jsons')
    os.makedirs(json_dir, exist_ok=True)

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
        import geopandas as gpd
        gdf = gpd.read_file(data)
        geojson = gdf.__geo_interface__
        self.add_geojson(geojson, name = name, **kwargs)
        
        
