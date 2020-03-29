# -*- coding: utf-8 -*-

#******************************************************************************
#
# SREMPy-landsat
# ---------------------------------------------------------
# Python realization of SREM atmospheric correction method for Landsat imagery
#
# Copyright (C) 2019 Eduard Kazakov (ee.kazakov@gmail.com)
#
#******************************************************************************

from .SREMPyLandsat import SREMPyLandsat, InvalidInputs
from .LandsatMetadataReader import LandsatMetadataReader
import os

def process_full_landsat_dataset_with_usgs_util(metadata_file,
                                                angles_file,
                                                usgs_util_path,
                                                temp_dir,
                                                output_dir,
                                                cygwin_bash_exe_path=None):
                                                
    
    metadata_reader = LandsatMetadataReader(metadata_file)

    if metadata_reader.metadata['SPACECRAFT_ID'] == 'LANDSAT_8':
        bands_to_process = ['1', '2', '3', '4', '5', '6', '7']
    elif metadata_reader.metadata['SPACECRAFT_ID'] == 'LANDSAT_7':
        bands_to_process = ['1', '2', '3', '4', '5', '7']
    elif metadata_reader.metadata['SPACECRAFT_ID'] == 'LANDSAT_5' or metadata_reader.metadata['SPACECRAFT_ID'] == 'LANDSAT_4':
        bands_to_process = ['1', '2', '3', '4', '5', '7']
    else:
        raise InvalidInputs

    dataset_basedir = os.path.dirname(metadata_file)

    srem = SREMPyLandsat(mode='landsat-usgs-utils')

    for band in bands_to_process:
        band_file_name = metadata_reader.bands[band]['file_name']
        band_file_path = os.path.join(dataset_basedir,band_file_name)

        output_name = '%s_SREM_SR.TIF' % band_file_name.split('.')[0]

        data = {
                'band': band_file_path,
                'metadata': metadata_file,
                'angles_file': angles_file,
                'usgs_util_path': usgs_util_path,
                'temp_dir':temp_dir,
                'cygwin_bash_exe_path': cygwin_bash_exe_path
                }

        srem.set_data(data)

        print ('---------------')
        print ('Processing %s...' % band_file_name)

        sr = srem.get_srem_surface_reflectance_as_array()

        srem.save_array_as_gtiff(sr,
                                 os.path.join(output_dir,output_name))
