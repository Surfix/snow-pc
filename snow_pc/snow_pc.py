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
        self.add_LayerControl()

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
