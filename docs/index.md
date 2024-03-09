# Welcome to snow_pc


[![image](https://img.shields.io/pypi/v/snow_pc.svg)](https://pypi.python.org/pypi/snow_pc)


**A python package for automated processing of point clouds to simplify elevation creation, co-registration and differencing to facilitate the production of snow depth and vegetation products.**


-   Free software: MIT license
-   Documentation: <https://Surfix.github.io/snow_pc>
    

## Introduction and statement of Need
Light Detection and Ranging (LiDAR) and Structure from Motion (SfM) photogrammetry currently provide the most advanced and accurate approaches for monitoring snow distribution across a range of platforms, scales, and repeat intervals. These techniques generate high-resolution digital elevation models (DEMs) by producing georeferenced point clouds from overlapping imagery in the case of photogrammetry or from high frequency laser pulses in the case of LiDAR. However, post-processing of point clouds for generation of snow depth rasters remains complex compared to many other earth science applications such as topographic mapping, vegetation monitoring, geomorphology and landform analysis. Existing point cloud processing software suite such as [Point Data Abstraction Library (PDAL)](https://pypi.org/project/pdal/) and LAStools provide general purpose tools for pre-processing, filtering and analyzing large point cloud data. Yet, there is a lack of tool that leveraged these capacities for optimized automated workflows specifically tailored for snow and ice applications. Consequently, complex manual interventions are often required for tasks like merging point cloud files from different flight lines or acquisitions, point clouds filtering, construction of (DTMs), aligning the DTMs and generation of products. This hinders efficient production of snow depth and limits full utilization of rich information in point clouds datasets.  

snow_pc addresses this challenge by leveraging pdal and Stereo Pipeline (ASP) to automate point clouds management in a standardized workflow for generating elevation models, snow depths and vegetation products. This allows diverse users of developers, data processors and snow scientists to automate core point clouds processing tasks like merging, coordinate transformations, classification, co-registration and rasterization to simplify effort and facilitate multi-temporal analysis.


## Usage
To learn more about snow_pc, check out the snow_pc [api reference](https://surfix.github.io/snow-pc/snow_pc/) on the documentation website- https://Surfix.github.io/snow-pc

![code usage](/usage_code.png)

## Key Features

##  TODO

- [x] Add ground segmentation module
- [] Figure out which dtm pipeline is most optimal
- [] Implement separate dem pipeline for LiDAR and photogrammetry
- [] Add interactive map feature to allow users draw control surface for coregistration
- [] Implement coregistration using points
