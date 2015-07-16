#!/usr/bin/env python


""" Reads a DIRSIG lidar "bin" file

Description:
    This file provides code to read a DIRSIG bin file and provides basic
    manipulation of that file.

Usage:
    To read a bin file:
        For most cases:
            import dirsig
            binfile = dirsig.lidar.DirsigBin()
            binfile.read(filename)

        If dirsig was compiled on a 32 bit system and the bin file is version
        0 or 1:
            import dirsig.lidar
            binfile = dirsig.lidar.DirsigBin()
            binfile.read(filename, True)

External Dependancies:
	numpy
	struct
	sys
	zlib

Warnings:
    This code has not been tested on a version 0 bin file.

Author(s):
	Paul Romanczyk      par4249 at rit dot edu

Copyright:
    (c) 2015 Rochester Institute of Technology

References:
	[1] http://www.dirsig.org/docs/new/bin.html (Accessed 2013-02-09).

"""


__author__ = "Paul Romanczyk"
__copyright__ = "Copyright 2015, Rochester Institute of Technology"
__credits__ = []
__license__ = "MIT"
#__version__ = "1.0.1"
__maintainer__ = "Paul Romanczyk"
__email__ = "par4249@rit.edu"
__status__ = "Production"


import sys     # stderr and command-line arguments
import numpy   # base data type for signals
import struct  # for convertint data types
import zlib    # for decompression

class DirsigBinHeader(object):
    """ A class for the bin file header """
    def __init__(self, arg=None):
        try:
            if arg == None:
                self.file_format_version = None
            elif isinstance(arg, DirsigBinHeader):
                self.file_format_version = arg.file_format_version
                if self.file_format_version != None:
                    self.byte_ordering = arg.byte_ordering
                    self.file_creation_date_time = arg.file_creation_date_time
                    self.dirsig_version_string = arg.dirsig_version_string
                    self.simulation_description = arg.simulation_description
                    self.scene_origin_latitute = arg.scene_origin_latitute
                    self.scene_origin_longitude = arg.scene_origin_longitude
                    self.scene_origin_height = arg.scene_origin_height
                    self.transmitter_mount_type = arg.transmitter_mount_type
                    self.reciever_mount_type = arg.reciever_mount_type
                    self.x_pixel_count = arg.x_pixel_count
                    self.y_pixel_count = arg.y_pixel_count
                    self.x_pixel_pitch = arg.x_pixel_pitch
                    self.y_pixel_pitch = arg.y_pixel_pitch
                    if self.file_format_version > 0:
                        self.x_array_offset = arg.x_array_offset
                        self.y_array_offset = arg.y_array_offset
                        self.lens_distortion_k1 = arg.lens_distortion_k1
                        self.lens_distortion_k2 = arg.lens_distortion_k2
                    self.task_count = arg.task_count
                    if self.file_format_version > 1:
                        self.focal_plane_array_id = arg.focal_plane_array_id
        except Exception:
            raise

    def endian(self):
        """ Return the endian that python wants """
        if self.byte_ordering == 0:
            return '>'
        else:
            return '<'

    def endian_str(self):
        """ Return a string of the endian type """
        if self.byte_ordering == 0:
            return 'big'
        else:
            return 'little'

    def read(self, fid):
        """ Read a header """
        try:
            self.file_format_version = struct.unpack('B', fid.read(1))[0]
            _version = self.file_format_version
            self.byte_ordering = struct.unpack('B', fid.read(1))[0]
            if self.byte_ordering == 0:
                endian = '>'
            else:
                endian = '<'
            self.file_creation_date_time = fid.read(15)
            self.dirsig_version_string = fid.read(32).replace('\x00', '')
            self.simulation_description = fid.read(256).replace('\x00', '')
            self.scene_origin_latitute = struct.unpack(endian + 'd', \
                fid.read(8))[0]
            self.scene_origin_longitude = struct.unpack(endian + 'd', \
                fid.read(8))[0]
            self.scene_origin_height = struct.unpack(endian + 'd', fid.read(8))[0]
            self.transmitter_mount_type = fid.read(16).replace('\x00', '')
            self.reciever_mount_type = fid.read(16).replace('\x00', '')
            self.x_pixel_count = struct.unpack(endian + 'I', fid.read(4))[0]
            self.y_pixel_count = struct.unpack(endian + 'I', fid.read(4))[0]
            self.x_pixel_pitch = struct.unpack(endian + 'd', fid.read(8))[0]
            self.y_pixel_pitch = struct.unpack(endian + 'd', fid.read(8))[0]
            if _version > 0:
                self.x_array_offset = struct.unpack(endian + 'd', fid.read(8))[0]
                self.y_array_offset = struct.unpack(endian + 'd', fid.read(8))[0]
                self.lens_distortion_k1 = struct.unpack(endian + 'd', \
                    fid.read(8))[0]
                self.lens_distortion_k2 = struct.unpack(endian + 'd', \
                    fid.read(8))[0]
            self.task_count = struct.unpack(endian + 'I', fid.read(4))[0]
            if _version > 1:
                self.focal_plane_array_id = struct.unpack(endian + 'H', \
                    fid.read(2))[0]
            return self
        except Exception:
            raise

    def __str__(self):
        output = 'DIRSIGPROTO\n\n'
        output += 'File Format Version:      {0}\n'.format(self.file_format_version)
        output += 'Byte Ordering:            {0} endian\n'.format(self.endian_str())
        output += 'File Creation Date Time:  {0}\n'.format(self.file_creation_date_time)
        output += 'DIRSIG Version String:    {0}\n'.format(self.dirsig_version_string)
        output += 'Simulation Description:   {0}\n'.format(self.simulation_description)
        output += 'Scene Origin Latitude:    {0}\n'.format(self.scene_origin_latitute)
        output += 'Scene Origin Longitude:   {0}\n'.format(self.scene_origin_longitude)
        output += 'Scene Origin Height:      {0}\n'.format(self.scene_origin_height)
        output += 'Transmitter Mount Type:   {0}\n'.format(self.transmitter_mount_type)
        output += 'Receiver Mount Type:      {0}\n'.format(self.reciever_mount_type)
        output += 'X Pixel Count:            {0}\n'.format(self.x_pixel_count)
        output += 'Y Pixel Count:            {0}\n'.format(self.y_pixel_count)
        output += 'X Pixel Pitch:            {0}\n'.format(self.x_pixel_pitch)
        output += 'Y Pixel Pitch:            {0}\n'.format(self.y_pixel_pitch)
        if self.file_format_version > 0:
            output += 'X Array Offset:           {0}\n'.format(self.x_array_offset)
            output += 'Y Array Offset:           {0}\n'.format(self.y_array_offset)
            output += 'Lens Distortion K1:       {0}\n'.format(self.lens_distortion_k1)
            output += 'Lens Distortion K2:       {0}\n'.format(self.lens_distortion_k2)
        output += 'Task Count:               {0}\n'.format(self.task_count)
        if self.file_format_version > 1:
            output += 'Focal Plane Array ID:     {0}\n'.format(self.focal_plane_array_id)
        return output

    def __repr__(self):
        return self.__str__()


class DirsigBinTaskHeader(object):
    """ A class for the task header """
    def __init__(self, arg=None):
        try:
            if arg == None:
                self.version = None
            elif isinstance(arg, DirsigBinTaskHeader):
                self.version = arg.version
                if self.version != None:
                    self.task_description = arg.task_description
                    self.task_start_date_time = arg.task_start_date_time
                    self.task_stop_date_time = arg.task_stop_date_time
                    self.focal_length = arg.focal_length
                    self.pulse_repition_frequency = arg.pulse_repition_frequency
                    self.pulse_duration = arg.pulse_duration
                    self.pulse_energy = arg.pulse_energy
                    self.laser_spectral_center = arg.laser_spectral_center
                    self.laser_spectral_width = arg.laser_spectral_width
                    self.pulse_count = arg.pulse_count
        except Exception:
            raise

    def __nonzero__(self):
        return self.version != None

    def __str__(self):
        if not self:
            return ''
        else:
            line = '*' * 80 + '\n'
            output = line + '\t\tTASK HEADER\n' + line
            output += 'Task Description:         {0}\n'.format(self.task_description)
            output += 'Task Start Datetime:      {0}\n'.format(self.task_start_date_time)
            output += 'Task Stop Datetime:       {0}\n'.format(self.task_stop_date_time)
            output += 'Focal Length:             {0}\n'.format(self.focal_length)
            output += 'Pulse Repition Frequency: {0}\n'.format(self.pulse_repition_frequency)
            output += 'Pulse Duration:           {0}\n'.format(self.pulse_duration)
            output += 'Pulse Energy:             {0}\n'.format(self.pulse_energy)
            output += 'Laser Spectral Center:    {0}\n'.format(self.laser_spectral_center)
            output += 'Laser Spectral Width:     {0}\n'.format(self.laser_spectral_width)
            output += 'Pulse Count:              {0}\n'.format(self.pulse_count)
            output += line
            return output

    def __repr__(self):
        return self.__str__()


    def read(self, fid, version, endian):
        """ Read a task header """
        try:
            self.version = version
            self.task_description = fid.read(64).replace('\x00', '')
            self.task_start_date_time = fid.read(15)
            self.task_stop_date_time = fid.read(15)
            self.focal_length = struct.unpack(endian + 'd', fid.read(8))[0]
            self.pulse_repition_frequency = struct.unpack(endian + 'd', \
                fid.read(8))[0]
            self.pulse_duration = struct.unpack(endian + 'd', fid.read(8))[0]
            self.pulse_energy = struct.unpack(endian + 'd', fid.read(8))[0]
            self.laser_spectral_center = struct.unpack(endian + 'd', \
                fid.read(8))[0]
            self.laser_spectral_width = struct.unpack(endian + 'd', fid.read(8))[0]
            self.pulse_count = struct.unpack(endian + 'I', fid.read(4))[0]
            return self
        except Exception:
            raise


class DirsigBinPulseHeader(object):
    """ A class for the pulse header """
    def __init__(self, arg=None):
        try:
            if arg == None:
                self.version = None
            elif isinstance(arg, DirsigBinPulseHeader):
                self.version = arg.version
                if self.version != None:
                    version = self.version
                    self.pulse_time = arg.pulse_time
                    self.time_gate_start = arg.time_gate_start
                    self.time_gate_stop = arg.time_gate_stop
                    self.time_gate_bin_count = arg.time_gate_bin_count
                    self.samples_per_time_bin = arg.samples_per_time_bin
                    self.platform_location = arg.platform_location
                    if version < 2:
                        self.platform_orientation_angle_order = \
                            arg.platform_orientation_angle_order
                    self.platform_rotation = arg.platform_rotation
                    if version > 1:
                        self.transmitter_to_mount_affine = \
                            arg.transmitter_to_mount_affine
                    else:
                        self.transmitter_mount_pointing_offset = \
                            arg.transmitter_mount_pointing_offset
                        self.tranmitter_orientation_angle_order = \
                            arg.tranmitter_orientation_angle_order
                    self.transmitter_mount_pointing_rotation = \
                        arg.transmitter_mount_pointing_rotation
                    if version > 1:
                        self.transmitter_mount_to_platform_affine = \
                            arg.transmitter_mount_to_platform_affine
                        self.receiver_to_mount_affine = \
                            arg.receiver_to_mount_affine
                    else:
                        self.receiver_mount_pointing_offset = \
                            arg.receiver_mount_pointing_offset
                        self.receiver_orientation_angle_order = \
                            arg.receiver_orientation_angle_order
                    self.receiver_mount_pointing_rotation = \
                        arg.receiver_mount_pointing_rotation
                    if version > 1:
                        self.receiver_mount_to_platform_affine = \
                            arg.receiver_mount_to_platform_affine
                    self.pulse_data_type = arg.pulse_data_type
                    self.data_compression_type = arg.data_compression_type
                    if version > 1:
                        self.pulse_index = arg.pulse_index
                    else:
                        self.delta_histogram_flag = arg.delta_histogram_flag
                    self.pulse_data_bytes = arg.pulse_data_bytes
                    if version > 1:
                        self.system_transmit_mueller_matrix = \
                            arg.system_transmit_mueller_matrix
                        self.system_receive_mueller_matrix = \
                            arg.system_receive_mueller_matrix
        except Exception:
            raise

    def __nonzero__(self):
        return self.version != None

    def __str__(self):
        line = '-' * 80 + '\n'
        output = '{0}\t\t\tPulse Header\n{0}'.format(line)
        if self.version == None:
            output += 'Empty Pulse Header'
        else:
            output += 'pulse time:                  {0}\n'.format(self.pulse_time)
            output += 'time gate start:             {0}\n'.format(self.time_gate_start)
            output += 'time gate stop:              {0}\n'.format(self.time_gate_stop)
            output += 'time gate bin count:         {0}\n'.format(self.time_gate_bin_count)
            output += 'samples per time bin:        {0}\n'.format(self.samples_per_time_bin)
            output += 'platform location:\n{0}\n'.format(self.platform_location)
            if self.version < 2:
                output += 'platform orientation angle order: {0}\n'.format(self.platform_orientation_angle_order)
            output += 'platform rotation:\n{0}\n'.format(self.platform_rotation)
            if self.version > 1:
                output += 'transmitter to mount affine:\n{0}\n'.format(self.transmitter_to_mount_affine)
            else:
                output += 'transmitter mount pointing offset: {0}\n'.format(self.transmitter_mount_pointing_offset)
                output += 'tranmitter orientation angle order: {0}\n'.format(self.tranmitter_orientation_angle_order)
            output += 'transmitter mount pointing rotation:\n{0}\n'.format(self.transmitter_mount_pointing_rotation)
            if self.version > 1:
                output += 'transmitter mount to platform affine:\n{0}\n'.format(self.transmitter_mount_to_platform_affine)
                output += 'receiver to mount affine:\n{0}\n'.format(self.receiver_to_mount_affine)
            else:
                output += 'receiver mount pointing offset: {0}\n'.format(self.receiver_mount_pointing_offset)
                output += 'receiver orientation angle order: {0}\n'.format(self.receiver_orientation_angle_order)
            output += 'receiver mount pointing rotation: {0}\n'.format(self.receiver_mount_pointing_rotation)
            if self.version > 1:
                output += 'receiver mount to platform affine:\n{0}\n'.format(self.receiver_mount_to_platform_affine)
            output += 'pulse data type:             {0}\n'.format(self.pulse_data_type)
            output += 'data compression type:       {0}\n'.format(self.data_compression_type)
            if self.version > 1:
                output += 'pulse index:                 {0}\n'.format(self.pulse_index)
            else:
                output += 'delta histogram flag:    {0}\n'.format(self.delta_histogram_flag)
            output += 'pulse data bytes:            {0}\n'.format(self.pulse_data_bytes)
            if self.version > 1:
                output += 'system transmit mueller matrix:\n{0}\n'.format(self.system_transmit_mueller_matrix)
                output += 'system receive mueller matrix:\n{0}\n'.format(self.system_receive_mueller_matrix)
        output += line
        return output

    def read(self, fid, version, endian, is32bit=False):
        """ Read a pulse header """
        try:
            self.version = version
            self.pulse_time = struct.unpack(endian + 'd', fid.read(8))[0]
            self.time_gate_start = struct.unpack(endian + 'd', fid.read(8))[0]
            self.time_gate_stop = struct.unpack(endian + 'd', fid.read(8))[0]
            self.time_gate_bin_count = struct.unpack(endian + 'I', \
                fid.read(4))[0]
            if version > 0:
                self.samples_per_time_bin = struct.unpack(endian + 'I', \
                    fid.read(4))[0]
            else:
                # Just make a guess
                self.samples_per_time_bin = 1
            self.platform_location = numpy.mat(struct.unpack(endian + 3 * 'd', \
                fid.read(24)))
            if version < 2:
                self.platform_orientation_angle_order = fid.read(3)
            self.platform_rotation = numpy.mat(struct.unpack(endian + 3 * 'd', \
                fid.read(24)))
            if version > 1:
                self.transmitter_to_mount_affine = \
                    numpy.mat(struct.unpack(endian + 16 * 'd', \
                    fid.read(128))).reshape((4, 4))
            else:
                self.transmitter_mount_pointing_offset = \
                    numpy.mat(struct.unpack(endian + 3 * 'd', \
                    fid.read(24)))
                self.tranmitter_orientation_angle_order = fid.read(3)
            self.transmitter_mount_pointing_rotation = \
                    numpy.mat(struct.unpack(endian + 3 * 'd', \
                    fid.read(24)))
            if version > 1:
                self.transmitter_mount_to_platform_affine = \
                    numpy.mat(struct.unpack(endian + 16 * 'd', \
                    fid.read(128))).reshape((4, 4))
                self.receiver_to_mount_affine = \
                    numpy.mat(struct.unpack(endian + 16 * 'd', \
                    fid.read(128))).reshape((4, 4))
            else:
                self.receiver_mount_pointing_offset = \
                    numpy.mat(struct.unpack(endian + 3 * 'd', \
                    fid.read(24)))
                self.receiver_orientation_angle_order = fid.read(3)
            self.receiver_mount_pointing_rotation = \
                    numpy.mat(struct.unpack(endian + 3 * 'd', \
                    fid.read(24)))
            if version > 1:
                self.receiver_mount_to_platform_affine = \
                    numpy.mat(struct.unpack(endian + 16 * 'd', \
                    fid.read(128))).reshape((4, 4))
            self.pulse_data_type = struct.unpack(endian + 'I', \
                fid.read(4))[0] # should always be 5 (double)
            self.data_compression_type = struct.unpack(endian + 'B', \
                fid.read(1))[0]
            if version > 1:
                self.pulse_index = struct.unpack(endian + 'I', fid.read(4))[0]
            else:
                self.delta_histogram_flag = struct.unpack(endian + 'B', \
                    fid.read(1))[0]
            # check for bug where a long may be 32 bits on some systems and 64 on others
            if is32bit and (version < 2):
                self.pulse_data_bytes = struct.unpack(endian + 'I', \
                    fid.read(4))[0]
            else:
                self.pulse_data_bytes = struct.unpack(endian + 'Q', \
                    fid.read(8))[0]
            if version > 1:
                self.system_transmit_mueller_matrix = \
                    numpy.mat(struct.unpack(endian + 16 * 'd', \
                    fid.read(128))).reshape((4, 4))
                self.system_receive_mueller_matrix = \
                    numpy.mat(struct.unpack(endian + 16 * 'd', \
                    fid.read(128))).reshape((4, 4))
            return self
        except Exception:
            raise


class DirsigBinTask(object):
    """ A class for a dirsig bin task """
    def __init__(self, arg=None):
        try:
            if arg == None:
                self.header = None
                self.pulses = []
            elif isinstance(arg, DirsigBinTask):
                self.header = DirsigBinTaskHeader(arg.header)
                for pulse in arg.pulses:
                    self.pulses.append(DirsigBinPulse(pulse))
        except Exception:
            raise

    def __len__(self):
        return len(self.pulses)

    def __getitem__(self, pulseindex):
        try:
            return self.pulses[pulseindex]
        except Exception:
            raise

    def __iter__(self):
        for pulse in self.pulses:
            yield pulse

    def __str__(self):
        output = '{0}\n'.format(self.header)
        for pulse in self.pulses:
            output += '{0}\n'.format(pulse)
        return output

    def __repr__(self):
        return "Task contains {0} pulses".format(len(self.pulses))

    def npulses(self):
        """ Returns the number of pulses """
        return self.header.pulse_count

    def read(self, fid, version, endian, x_pix_ct, y_pix_ct, is32bit=False):
        """ Read a task """
        try:
            self.header = DirsigBinTaskHeader()
            self.header.read(fid, version, endian)

            for dummypulse in range(self.header.pulse_count):
                pulse = DirsigBinPulse()
                pulse.read(fid, version, endian, x_pix_ct, y_pix_ct, \
                    is32bit=is32bit)
                self.pulses.append(DirsigBinPulse(pulse))
        except Exception:
            raise



class DirsigBinPulse(object):
    """ A class for a dirsig bin pulse """
    def __init__(self, arg=None):
        try:
            if arg == None:
                self.header = None
                self.passive = numpy.empty([])
                self.active = numpy.empty([])
            elif isinstance(arg, DirsigBinPulse):
                self.header = DirsigBinPulseHeader(arg.header)
                self.passive = arg.passive
                self.active = arg.active
        except Exception:
            raise

    def __str__(self):
        # output = '{0}'.format(self.header)
        # return output
        if self.header == None:
            return "Empty Pulse\n"
        output = 'Pulse statistics:\n'
        output += 'Number of Time Bins:  {0}\n'.format(self.header.time_gate_bin_count)
        output += 'Samples per Time Bin: {0}\n'.format(self.header.samples_per_time_bin)
        output += 'Array size            {0}x{0}\n'.format(self.array_size()[0], \
            self.array_size()[1])
        output += 'Range Gate Open:      {0} [s] ({1} [m])\n'.format(self.header.time_gate_start, \
            self.time_to_range(self.header.time_gate_start))
        output += 'Range Gate Close:     {0} [s] ({1} [m])\n'.format(self.header.time_gate_stop, \
            self.time_to_range(self.header.time_gate_stop))
        output += 'Max Passive Signal:   {0} [phot/bin]\n'.format(numpy.max(self.passive))
        output += 'Min Passive Singal:   {0} [phot/bin]\n'.format(numpy.min(self.passive))
        output += 'Max Active Signal:    {0} [phot/bin]\n'.format(numpy.max(self.active))
        output += 'Min Active Singal:    {0} [phot/bin]\n'.format(numpy.min(self.active))
        return output

    def __repr__(self):
        if self.header == None:
            return "Empty Pulse\n"
        output = 'Pulse statistics:\n'
        output += 'Number of Time Bins:  {0}\n'.format(self.header.time_gate_bin_count)
        output += 'Samples per Time Bin: {0}\n'.format(self.header.samples_per_time_bin)
        output += 'Array size            {0}x{0}\n'.format(self.array_size()[0], \
            self.array_size()[1])
        output += 'Max Passive Signal:   {0} [phot/bin]\n'.format(numpy.max(self.passive))
        output += 'Min Passive Singal:   {0} [phot/bin]\n'.format(numpy.min(self.passive))
        output += 'Max Active Signal:    {0} [phot/bin]\n'.format(numpy.max(self.active))
        output += 'Min Active Singal:    {0} [phot/bin]\n'.format(numpy.min(self.active))
        return output

    def time_to_range(self, time, index_of_refraction=1.0):
        speed_of_light = 299792458.
        return time * speed_of_light / (2.0 * index_of_refraction)

    def clear(self):
        """ Clear the pulse """
        self.header = None
        self.active = numpy.empty([])
        self.passive = numpy.empty([])
        return self

    def shape(self):
        """ Get the shape of the active part of the signal """
        return self.active.shape

    def array_size(self):
        s = self.shape()
        if len(s) == 3:
            return s[0:2]
        elif len(s) == 1:
            return (1, 1)
        # no other cases should be possible

    def shape_triplet(self):
        s = self.shape()
        if len(s) == 3:
            return s
        elif len(s) == 1:
            return (1, 1, s[0])
        # no other cases should be possible

    def num_time_bins(self):
        """ Gets the number of time bins """
        return self.header.time_gate_bin_count * self.header.samples_per_time_bin

    def time_bin_width(self):
        """ get the width of a time bin in seconds """
        return (self.header.time_gate_stop - self.header.time_gate_start) / \
            self.num_time_bins()

    def range_gate_width(self):
        return self.header.time_gate_stop - self.header.time_gate_start

    def get_signal(self):
        """ Get the Singal """
        s = self.passive.shape
        return self.active + numpy.reshape(self.passive, (s[0], s[1], 1))

    def get_time(self):
        """ Get the time to the bins """
        return numpy.linspace(self.header.time_gate_start, \
            self.header.time_gate_stop, self.num_time_bins())

    def get_range(self):
        """ Get the range to the time bins """
        return time_to_range(self.get_time())

    def read(self, fid, version, endian, xpixelct, ypixelct, is32bit=False):
        """ reads a pulse """

        # read the header
        self.clear()
        self.header = DirsigBinPulseHeader()
        self.header.read(fid, version, endian, is32bit=is32bit)

        tmp = fid.read(self.header.pulse_data_bytes)
        if self.header.data_compression_type == 1:
            tmp = zlib.decompress(tmp)

        # How many active bins do we have?
        active_bin_ct = self.header.samples_per_time_bin * \
            self.header.time_gate_bin_count

        # convert to doubles
        tmp = struct.unpack(xpixelct * ypixelct * (active_bin_ct + 1) * 'd', tmp)

        # store in numpy.array
        tmp = numpy.reshape(numpy.array(tmp), \
            (xpixelct, ypixelct, active_bin_ct + 1))

        # separate into active and passive terms
        if xpixelct == 1 and ypixelct == 1:
            # make a 1D array
            self.active = numpy.squeeze(tmp[:, :, 1:])
            self.passive = numpy.squeeze(tmp[:, :, 0]) * self.range_gate_width()
        else:
            self.active = tmp[:, :, 1:]
            self.passive = numpy.squeeze(tmp[:, :, 0], axis=2) * \
                self.range_gate_width()
        return self


class DirsigBin(object):
    """ A DIRSIG lidar bin file """
    def __init__(self, arg=None):
        if arg == None:
            self.header = None
            self.tasks = []
        elif isinstance(arg, DirsigBin):
            self.header = DirsigBinHeader(arg.header)
            for task in tasks:
                self.tasks.append(DirsigBinTask(task))

    def __str__(self):
        output = '{0}\n'.format(self.header)
        for task in self.tasks:
            output += '{0}\n\n'.format(task)
        return output

    def __repr__(self):
        return "DIRSIG LiDAR File"

    def __iter__(self):
        for task in self.tasks:
            yield task

    def __getitem__(self, taskindex):
        try:
            return self.tasks[taskindex]
        except Exception:
            raise

    def ntasks(self):
        """ returns the number of tasks """
        return len(self.tasks)

    def clear(self):
        """ Clears a bin file """
        self.header = None
        self.tasks = []
        return self

    def read(self, filename, is32bit=False):
        """ Reads a bin file """
        self.clear()
        fid = open(filename, 'r')
        try:
            byte = fid.read(11)
            if byte != "DIRSIGPROTO":
                raise RuntimeError("'" + filename + \
                    "' is not valid DIRSIG bin file.")

            # read the header
            self.header = DirsigBinHeader()
            self.header.read(fid)

            for dummytask in range(self.header.task_count):
                task = DirsigBinTask()
                task.read(fid, self.header.file_format_version, \
                    self.header.endian(), self.header.x_pixel_count, \
                    self.header.y_pixel_count, is32bit=is32bit)
                self.tasks.append(task)

            return self

        except RuntimeError, error:
            sys.stderr.write('ERROR: {0}s\n'.format(error))
        finally:
            fid.close()

if __name__ == "__main__":
    import os
    ARGS = sys.argv

    # SET DEFAULTS
    TASK = None
    PULSE = None

    if len(ARGS) == 1:
        MSG = 'Usage: dirsigbin.py filename'
        sys.exit(MSG)

    FILENAME = ARGS[-1]
    if not os.path.exists(FILENAME):
        sys.exit('"{0}" does not exist'.format(filename))

    try:
        for ARG in ARGS[1:-1]:
            if ARG.lower().startswith('task='):
                TASK = int(ARG[5:])
            elif ARG.lower().startswith('pulse='):
                PULSE =int(ARG[6:])
            else:
                sys.exit('Unexpected command-line argument: {0}'.format(ARG))

        BINFILE = DirsigBin()
        BINFILE.read(FILENAME)

        if TASK:
            if PULSE:
                print BINFILE[TASK][PULSE]
            else:
                print BINFILE[TASK]
        elif PULSE:
            print BINFILE[0][TASK]
        else:
            print BINFILE

    except Exception, EXCEPTION:
        sys.exit('{0}'.format(EXCEPTION))
  