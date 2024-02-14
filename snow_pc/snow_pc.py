"""Main module."""

import os
import ipyleaflet

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
        
        
