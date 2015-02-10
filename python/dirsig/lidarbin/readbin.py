#!/usr/bin/env python


""" Reads a DIRSIG lidar "bin" file

Description:
    This file provides code to read a DIRSIG bin file and provides basic
    manipulation of that file.

Usage:
    To read a bin file:
        binfile = readDirsigBin(filename)
        binfile = readDirsigBin(filename, True)
    To get the true signals:
        signal = getSignal( binfile )
    To get the range of each time bin for each pulse:
    	range = getBinRange( binfile )

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
#__license__ = "GPL"
#__version__ = "1.0.1"
__maintainer__ = "Paul Romanczyk"
__email__ = "par4249@rit.edu"
__status__ = "Production"


import sys     # stderr and command-line arguments
import numpy   # base data type for signals
import struct  # for convertint data types
import zlib    # for decompression


def readbin(filename, is32bit=False):
    """Reads a DIRSIG bin file

    Keyword arguments:
    filename -- a string containing the file to read
    is32bit  -- a bool if DIRSIG was compiled on a 32 bit system. (default =
                False). Tells the code to use 32 long longs for the pulse data
                bytes field. In version 2 or later of the bin file, this was
                guarrenteed to be 64 bits in of the bin file and this flag will
                have no effect on the data parsing.

    Returns:
    dict

    """

    # define helper functions
    def readpulse(fid, version, endian, xpixelct, ypixelct, is32bit):
        """Reads a pulse from a DIRSIG bin file

        Keyword arguments:
        fid      -- the file id to read a pulse from
        version  -- the version of the bin file
        endian   -- the endian of the data
        xpixelct -- the number of pixels in the x direction
        ypixelct -- the number of pixels in the y direction
        is32bit  -- a bool if DIRSIG was compiled on a 32 bit system.

        Returns:
        dict

        """

        output = {}
        header = {}
        header['pulse time'] = struct.unpack(endian + 'd', fid.read(8))[0]
        header['time gate start'] = struct.unpack(endian + 'd', fid.read(8))[0]
        header['time gate stop'] = struct.unpack(endian + 'd', fid.read(8))[0]
        header['time gate bin count'] = struct.unpack(endian + 'I', \
            fid.read(4))[0]
        if version > 0:
            header['samples per time bin'] = struct.unpack(endian + 'I', \
                fid.read(4))[0]
        else:
            # Just make a guess
            header['samples per time bin'] = 1
        header['platform location'] = numpy.mat(struct.unpack(endian + 3 * 'd', \
            fid.read(24)))
        if version < 2:
            header['platform orientation angle order'] = fid.read(3)
        header['platform rotation'] = numpy.mat(struct.unpack(endian + 3 * 'd', \
            fid.read(24)))
        if version > 1:
            # pylint: disable=E1103
            header['transmitter to mount affine'] = \
                numpy.mat(struct.unpack(endian + 16 * 'd', \
                fid.read(128))).reshape((4, 4))
            # pylint: enable=E1103
        else:
            header['transmitter mount pointing offset'] = \
                numpy.mat(struct.unpack(endian + 3 * 'd', \
                fid.read(24)))
            header['tranmitter orientation angle order'] = fid.read(3)
        header['transmitter mount pointing rotation'] = \
                numpy.mat(struct.unpack(endian + 3 * 'd', \
                fid.read(24)))
        if version > 1:
            # pylint: disable=E1103
            header['transmitter mount to platform affine'] = \
                numpy.mat(struct.unpack(endian + 16 * 'd', \
                fid.read(128))).reshape((4, 4))
            header['receiver to mount affine'] = \
                numpy.mat(struct.unpack(endian + 16 * 'd', \
                fid.read(128))).reshape((4, 4))
            # pylint: enable=E1103
        else:
            header['receiver mount pointing offset'] = \
                numpy.mat(struct.unpack(endian + 3 * 'd', \
                fid.read(24)))
            header['receiver orientation angle order'] = fid.read(3)
        header['receiver mount pointing rotation'] = \
                numpy.mat(struct.unpack(endian + 3 * 'd', \
                fid.read(24)))
        if version > 1:
            # pylint: disable=E1103
            header['receiver mount to platform affine'] = \
                numpy.mat(struct.unpack(endian + 16 * 'd', \
                fid.read(128))).reshape((4, 4))
            # pylint: enable=E1103
        header['pulse data type'] = struct.unpack(endian + 'I', \
            fid.read(4))[0] # should always be 5 (double)
        header['data compression type'] = struct.unpack(endian + 'B', \
            fid.read(1))[0]
        if version > 1:
            header['pulse index'] = struct.unpack(endian + 'I', fid.read(4))[0]
        else:
            header['delta histogram flag'] = struct.unpack(endian + 'B', \
                fid.read(1))[0]
        # check for bug where a long may be 32 bits on some systems and 64 on others
        if is32bit and (version < 2):
            header['pulse data bytes'] = struct.unpack(endian + 'I', \
                fid.read(4))[0]
        else:
            header['pulse data bytes'] = struct.unpack(endian + 'Q', \
                fid.read(8))[0]
        if version > 1:
            # pylint: disable=E1103
            header['system transmit mueller matrix'] = \
                numpy.mat(struct.unpack(endian + 16 * 'd', \
                fid.read(128))).reshape((4, 4))
            header['system receive mueller matrix'] = \
                numpy.mat(struct.unpack(endian + 16 * 'd', \
                fid.read(128))).reshape((4, 4))
            # pylint: enable=E1103
        output['header'] = header

        # read the data
        tmp = fid.read(header['pulse data bytes'])
        if header['data compression type'] == 1:
            tmp = zlib.decompress(tmp)

        tmp = struct.unpack(xpixelct * ypixelct * header['samples per time bin'] * \
            (header['time gate bin count'] + 1) * 'd', tmp)

        # pylint: disable=E1103
        output['data'] = numpy.reshape(numpy.array(tmp), (xpixelct, \
            ypixelct, header['samples per time bin'] * \
            (header['time gate bin count'] + 1)))
        # pylint: enable=E1103

        return output


    def readtask(fid, version, endian, xpixelct, ypixelct, is32bit):
        """Reads a pulse from a DIRSIG bin file

        Keyword arguments:
        fid      -- the file id to read a pulse from
        version  -- the version of the bin file
        endian   -- the endian of the data
        xpixelct -- the number of pixels in the x direction
        ypixelct -- the number of pixels in the y direction
        is32bit  -- a bool if DIRSIG was compiled on a 32 bit system.

        Returns:
        dict

        """
        output = {}
        output['pulses'] = []
        header = {}
        header['task description'] = fid.read(64).replace('\x00', '')
        header['task start date time'] = fid.read(15)
        header['task stop date time'] = fid.read(15)
        header['focal length'] = struct.unpack(endian + 'd', fid.read(8))[0]
        header['pulse repition frequency'] = struct.unpack(endian + 'd', \
            fid.read(8))[0]
        header['pulse duration'] = struct.unpack(endian + 'd', fid.read(8))[0]
        header['pulse energy'] = struct.unpack(endian + 'd', fid.read(8))[0]
        header['laser spectral center'] = struct.unpack(endian + 'd', \
            fid.read(8))[0]
        header['laser spectral width'] = struct.unpack(endian + 'd', \
            fid.read(8))[0]
        header['pulse count'] = struct.unpack(endian + 'I', fid.read(4))[0]
        output['header'] = header
        for dummypulse in range(header['pulse count']):
            output['pulses'].append(readpulse(fid, version, endian, xpixelct, \
                ypixelct, is32bit))
        return output


    # start reading the bin file
    fid = open(filename, "rb")
    output = {}
    output['tasks'] = []
    header = {}
    try:
        byte = fid.read(11)
        if byte != "DIRSIGPROTO":
            raise RuntimeError("'" + filename + \
                "' is not valid DIRSIG bin file.")
        header['file format revision'] = struct.unpack('B', fid.read(1))[0]
        _version = header['file format revision']
        header['byte ordering'] = struct.unpack('B', fid.read(1))[0]
        if header['byte ordering'] == 0:
            endian = '>'
        else:
            endian = '<'
        header['file creation date time'] = fid.read(15)
        header['dirsig version string'] = fid.read(32).replace('\x00', '')
        header['simulation description'] = fid.read(256).replace('\x00', '')
        header['scene origin latitude'] = struct.unpack(endian + 'd', \
            fid.read(8))[0]
        header['scene origin longitude'] = struct.unpack(endian + 'd', \
            fid.read(8))[0]
        header['scene origin height'] = struct.unpack(endian + 'd', \
            fid.read(8))[0]
        header['transmitter mount type'] = fid.read(16).replace('\x00', '')
        header['reciever mount type'] = fid.read(16).replace('\x00', '')
        header['x pixel count'] = struct.unpack(endian + 'I', \
            fid.read(4))[0]
        header['y pixel count'] = struct.unpack(endian + 'I', \
            fid.read(4))[0]
        header['x pixel pitch'] = struct.unpack(endian + 'd', \
            fid.read(8))[0]
        header['y pixel pitch'] = struct.unpack(endian + 'd', \
            fid.read(8))[0]
        if _version > 0:
            header['x array offset'] = struct.unpack(endian + 'd', \
                fid.read(8))[0]
            header['y array offset'] = struct.unpack(endian + 'd', \
                fid.read(8))[0]
            header['lens distortion k1'] = struct.unpack(endian + 'd', \
                fid.read(8))[0]
            header['lens distortion k2'] = struct.unpack(endian + 'd', \
                fid.read(8))[0]
        header['task count'] = struct.unpack(endian + 'I', fid.read(4))[0]
        if _version > 1:
            header['focal plane array id'] = struct.unpack(endian + 'H', \
                fid.read(2))[0]

        output['header'] = header

        for dummytask in range(header['task count']):
            output['tasks'].append(readtask(fid, _version, endian, \
                header['x pixel count'], header['y pixel count'], is32bit))

    except RuntimeError, error:
        sys.stderr.write('ERROR: #s\n' % str(error))
    finally:
        fid.close()

    return output



if __name__ == '__main__':
    ARGS = sys.argv[1:]
    if ARGS:
        FILENAME = "\\ ".join(ARGS)

        BINFILE = readbin(FILENAME)

        TASKCT = 0
        PULSECT = 0

        for dummytask in BINFILE['tasks']:
            TASKCT += 1
            for dummypulse in dummytask['pulses']:
                PULSECT += 1

        print FILENAME + ' contains:'
        print '\t' + str(TASKCT) + ' tasks'
        print '\t' + str(PULSECT) + ' pulses'
