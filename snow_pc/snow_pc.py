"""Main module."""

import os

def replace_white_spaces(parent, replace = ''):
    """Remove any white space in the point cloud files. 

    Args:
        parent (_type_): Parent directory of the point cloud files.
        replace (str, optional): Character to replace the white space. Defaults to ''.
    """
    ans = input(f'Warning! About to replace whitespaces with "{replace}"s in {os.path.abspath(parent)} \n Press y to continue...')
    if ans.lower() == 'y':
        for path, folders, files in os.walk(parent):
            for f in files:
                os.rename(os.path.join(path, f), os.path.join(path, f.replace(' ', replace)))
            for i in range(len(folders)):
                new_name = folders[i].replace(' ', replace)
                os.rename(os.path.join(path, folders[i]), os.path.join(path, new_name))
                folders[i] = new_name
    else:
        print(f'Passing...')

