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

try:
    import gdal
except:
    from osgeo import gdal
import numpy as np
from .LandsatMetadataReader import LandsatMetadataReader
from .CalibrateLandsatBand import CalibrateLandsatBand
import os

class InvalidMode(Exception):
    pass

class InvalidInputs(Exception):
    pass

class SREMPyLandsat():

    modes = ['landsat-auto', 'landsat-manual', 'landsat-usgs-utils']
    modes_data = {'landsat-manual':{'band':'','metadata':'','solar_azimuth':'','sensor_azimuth':'','solar_zenith':'','sensor_zenith':'','angles_coef':0.01},
                  'landsat-auto':{'band':'','metadata':'','temp_dir':''},
                  'landsat-usgs-utils': {'band': '', 'metadata': '', 'angles_file':'', 'usgs_util_path':'', 'temp_dir': '', 'cygwin_bash_exe_path': ''}}

    mode = None

    def __init__(self, mode):
        if mode not in self.modes:
            raise InvalidMode
        else:
            self.mode = mode

    def set_data(self, data):
        if self.mode == None:
            raise InvalidMode('mode must be one of: %s' % self.modes)
        if data.keys() != self.modes_data[self.mode].keys():
            raise InvalidInputs('Inputs model must be %s' % self.modes_data[self.mode])
        self.data = data

    def get_srem_surface_reflectance_as_array(self):
        if self.mode == 'landsat-manual':
            self.metadata_file = self.data['metadata']
            self.metadata_reader = LandsatMetadataReader(self.data['metadata'])
            self.band_file = self.data['band']
            self.band_metadata = self.metadata_reader.get_band_metadata_by_file_name(self.band_file)
            self.band_dataset = gdal.Open(self.band_file)
            self.angles_coef = self.data['angles_coef']

            self.solar_zenith_dataset = gdal.Open(self.data['solar_zenith'])
            self.solar_zenith_array = np.deg2rad(self.solar_zenith_dataset.GetRasterBand(1).ReadAsArray() * self.angles_coef)

            self.solar_azimuth_dataset = gdal.Open(self.data['solar_azimuth'])
            self.solar_azimuth_array = np.deg2rad(self.solar_azimuth_dataset.GetRasterBand(1).ReadAsArray() * self.angles_coef)

            self.sensor_zenith_dataset = gdal.Open(self.data['sensor_zenith'])
            self.sensor_zenith_array = np.deg2rad(self.sensor_zenith_dataset.GetRasterBand(1).ReadAsArray() * self.angles_coef)

            self.sensor_azimuth_dataset = gdal.Open(self.data['sensor_azimuth'])
            self.sensor_azimuth_array = np.deg2rad(self.sensor_azimuth_dataset.GetRasterBand(1).ReadAsArray() * self.angles_coef)

            calibrator = CalibrateLandsatBand(self.band_file, self.metadata_file)
            toa_reflectance = calibrator.get_reflectance_as_array()

        if self.mode == 'landsat-auto':

            import landsatangles

            self.metadata_file = self.data['metadata']
            self.metadata_reader = LandsatMetadataReader(self.data['metadata'])
            self.band_file = self.data['band']
            self.band_metadata = self.metadata_reader.get_band_metadata_by_file_name(self.band_file)
            self.band_dataset = gdal.Open(self.band_file)

            if not os.path.exists(self.data['temp_dir']):
                os.makedirs(self.data['temp_dir'])

            angles_file = os.path.join(self.data['temp_dir'],'angles.tif')

            landsatangles.makeAngles_(self.metadata_file,
                                      self.band_file,
                                      angles_file)

            angeles_dataset = gdal.Open(angles_file)

            self.solar_zenith_array = np.deg2rad(angeles_dataset.GetRasterBand(4).ReadAsArray())
            self.solar_azimuth_array = np.deg2rad(angeles_dataset.GetRasterBand(3).ReadAsArray())
            self.sensor_zenith_array = np.deg2rad(angeles_dataset.GetRasterBand(2).ReadAsArray())
            self.sensor_azimuth_array = np.deg2rad(angeles_dataset.GetRasterBand(1).ReadAsArray())

            calibrator = CalibrateLandsatBand(self.band_file, self.metadata_file)
            toa_reflectance = calibrator.get_reflectance_as_array()

        if self.mode == 'landsat-usgs-utils':
            self.metadata_file = self.data['metadata']
            self.metadata_reader = LandsatMetadataReader(self.data['metadata'])
            self.band_file = self.data['band']
            self.band_metadata = self.metadata_reader.get_band_metadata_by_file_name(self.band_file)
            self.band_dataset = gdal.Open(self.band_file)

            if not os.path.exists(self.data['temp_dir']):
                os.makedirs(self.data['temp_dir'])

            util_path = self.data['usgs_util_path']
            angles_path = self.data['angles_file']
            band_bumber = self.band_metadata['number']

            # Generate angles for band
            if self.data['cygwin_bash_exe_path'] == None:
                cmd = '%s %s BOTH 1 -b %s' % (util_path, angles_path, band_bumber)
                os.chdir(self.data['temp_dir'])
            else:
                cmd = '%s --login -c \"cd %s && %s %s BOTH 1 -b %s\"' % (self.data['cygwin_bash_exe_path'], self.data['temp_dir'], util_path, angles_path, band_bumber)
            
            os.system(cmd)

            solar_path = os.path.join(self.data['temp_dir'],
                                      self.metadata_reader.metadata['LANDSAT_PRODUCT_ID'] + '_solar_B' + str(band_bumber).zfill(2)+'.img')
            sensor_path = os.path.join(self.data['temp_dir'],
                                      self.metadata_reader.metadata['LANDSAT_PRODUCT_ID'] + '_sensor_B' + str(band_bumber).zfill(2)+'.img')

            solar_dataset = gdal.Open(solar_path)
            sensor_dataset = gdal.Open(sensor_path)

            self.solar_zenith_array = np.deg2rad(solar_dataset.GetRasterBand(2).ReadAsArray() * 0.01)
            self.solar_azimuth_array = np.deg2rad(solar_dataset.GetRasterBand(1).ReadAsArray() * 0.01)
            self.sensor_zenith_array = np.deg2rad(sensor_dataset.GetRasterBand(2).ReadAsArray() * 0.01)
            self.sensor_azimuth_array = np.deg2rad(sensor_dataset.GetRasterBand(1).ReadAsArray() * 0.01)

            calibrator = CalibrateLandsatBand(self.band_file, self.metadata_file)
            toa_reflectance = calibrator.get_reflectance_as_array()

        # SREM logic
        rayleigh_reflectance = self.get_rayleigh_reflectance()
        Satm = self.get_atmospheric_backscattering_ratio()
        T = self.get_total_transmission()

        surface_reflectance = (toa_reflectance - rayleigh_reflectance) / (((toa_reflectance - rayleigh_reflectance) * Satm) + T)

        return surface_reflectance


    def get_relative_azimuth_angle(self):
        relative_azimuth_angle = np.abs(self.solar_azimuth_array - self.sensor_azimuth_array)

        relative_azimuth_angle = np.where(relative_azimuth_angle > np.pi, 2.0 * np.pi - relative_azimuth_angle, relative_azimuth_angle)

        relative_azimuth_angle = np.where(relative_azimuth_angle <= np.pi, np.pi - relative_azimuth_angle, relative_azimuth_angle)
        return relative_azimuth_angle

    def get_scattering_angle(self):
        relative_azimuth_angle = self.get_relative_azimuth_angle()
        CRA = np.cos(relative_azimuth_angle)
        CVZ = np.cos(self.sensor_zenith_array)
        CSZ = np.cos(self.solar_zenith_array)
        SVZ = np.sin(self.sensor_zenith_array)
        SSZ = np.sin(self.solar_zenith_array)

        scattering_angle = np.arccos((-1.0 * CSZ * CVZ) + ((SSZ * SVZ) * CRA))

        return scattering_angle

    def get_rayleigh_optical_depth(self):
        l = self.band_metadata['wavelength']
        rayleigh_optical_depth = 0.008569 * pow(l,-4) * (1 + 0.0113*pow(l,-2) + 0.0013*pow(l,-4))
        return rayleigh_optical_depth

    def get_rayleigh_phase_function(self):
        A = 0.9587256
        B = 1.0 - A
        O = self.get_scattering_angle()
        rayleigh_phase_function = (3.0*A)/(4.0+B) * (1.0+np.cos(O)*np.cos(O))
        return rayleigh_phase_function

    def get_air_mass(self):
        air_mass = (1.0 / np.cos(self.solar_zenith_array)) + (1.0 / np.cos(self.sensor_zenith_array))
        return air_mass

    def get_rayleigh_reflectance(self):
        rayleigh_phase_function = self.get_rayleigh_phase_function()
        air_mass = self.get_air_mass()
        rayleigh_optical_depth = self.get_rayleigh_optical_depth()
        u_solar = np.cos(self.solar_zenith_array)
        u_sensor = np.cos(self.sensor_zenith_array)

        rayleigh_reflectance = (rayleigh_phase_function * (1-pow(np.e,-1.0*air_mass*rayleigh_optical_depth))) / (4*(u_solar+u_sensor))

        return rayleigh_reflectance

    def get_atmospheric_backscattering_ratio(self):
        rayleigh_optical_depth = self.get_rayleigh_optical_depth()
        Satm = (0.92*rayleigh_optical_depth)*pow(np.e,-1.0*rayleigh_optical_depth)
        return Satm

    def get_transmission_on_sun_surface_path(self):
        rayleigh_optical_depth = self.get_rayleigh_optical_depth()
        u_solar = np.cos(self.solar_zenith_array)
        transmission_on_sun_surface_path = pow(np.e,-1.0*rayleigh_optical_depth/u_solar) + pow(np.e,-1.0*rayleigh_optical_depth/u_solar) * (pow(np.e,0.52*rayleigh_optical_depth/u_solar)-1)
        return transmission_on_sun_surface_path

    def get_transmission_on_surface_sensor_path(self):
        rayleigh_optical_depth = self.get_rayleigh_optical_depth()
        u_sensor = np.cos(self.solar_zenith_array)
        transmission_on_surface_sensor_path = pow(np.e,-1.0*rayleigh_optical_depth/u_sensor) + pow(np.e,-1.0*rayleigh_optical_depth/u_sensor) * (pow(np.e,0.52*rayleigh_optical_depth/u_sensor)-1)
        return transmission_on_surface_sensor_path

    def get_total_transmission(self):
        transmission_on_surface_sensor_path = self.get_transmission_on_surface_sensor_path()
        transmission_on_sun_surface_path = self.get_transmission_on_sun_surface_path()
        return transmission_on_surface_sensor_path * transmission_on_sun_surface_path

    def save_array_as_gtiff(self, array, new_file_path):
        driver = gdal.GetDriverByName("GTiff")
        dataType = gdal.GDT_Float32
        dataset = driver.Create(new_file_path, self.band_dataset.RasterXSize, self.band_dataset.RasterYSize, self.band_dataset.RasterCount, dataType)
        dataset.SetProjection(self.band_dataset.GetProjection())
        dataset.SetGeoTransform(self.band_dataset.GetGeoTransform())
        dataset.GetRasterBand(1).WriteArray(array)
        del dataset
