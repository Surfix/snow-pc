import logging
import os
import subprocess
from glob import glob
from os.path import abspath, basename, dirname, exists, isdir, join, expanduser


def replace_white_spaces(in_dir, replace = ''):
    """Remove any white space in the point cloud files. 

    Args:
        in_dir (_type_): in_dir directory of the point cloud files.
        replace (str, optional): Character to replace the white space. Defaults to ''.
    """
    assert isdir(in_dir), f'{in_dir} is not a directory'
    response = input(f'Warning! About to replace whitespaces with "{replace}"s in {os.path.abspath(in_dir)} \n Press y to continue...')
    if response.lower() == 'y':
        for path, folders, files in os.walk(in_dir):
            for f in files:
                os.rename(os.path.join(path, f), os.path.join(path, f.replace(' ', replace)))
            for i in range(len(folders)):
                new_name = folders[i].replace(' ', replace)
                os.rename(os.path.join(path, folders[i]), os.path.join(path, new_name))
                folders[i] = new_name
    else:
        print(f'Passing...')


def las2laz(in_dir: str):

    assert isdir(in_dir), f'{in_dir} is not a directory'

    # Get a list of all LAS files in the directory
    las_files = [file for file in os.listdir(in_dir) if file.endswith('.las')]

    # Iterate over each LAS file and convert it to LAZ
    for las_file in las_files:
        input_path = os.path.join(in_dir, las_file)
        output_path = os.path.join(in_dir, os.path.splitext(las_file)[0] + '.laz')
        subprocess.run(['pdal', 'translate', input_path, output_path])
        print(f"Converted {input_path} to {output_path}")

        
def merge_laz_files(in_dir, out_fp = 'unaligned_merged.laz'):
    assert isdir(in_dir), f'{in_dir} is not a directory'
    # out fp to save to
    mosaic_fp = join(in_dir, out_fp)
    # Get a list of all LAZ files in the directory
    laz_files = [file for file in os.listdir(in_dir) if file.endswith('.laz')]
    
    # Build the command to merge all LAZ files into a single file
    command = ['pdal', 'merge']
    for laz_file in laz_files:
        command.append(os.path.join(in_dir, laz_file))
    command.append(mosaic_fp)
    
    # Execute the merge command
    print(f'Running command: {command}')
    subprocess.run(command)
    print(f"Merged {len(laz_files)} LAZ files into {mosaic_fp}")