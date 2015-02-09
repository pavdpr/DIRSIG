#!/usr/bin/python


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


def printbinfile(data, tab=0):
    """Prints a bin file

    Keyword arguments:
    data -- the bin file to print
    tab  -- the number of tabs to use

    Returns:
    None

    """

    def printmatrix(matrix, tab):
        """Prints a numpy.matrix with tabs

        Keyword arguments:
        matrix -- the matrix to print
        tab    -- the number of tabs to use

        Returns:
        None

        """

        for i in range(matrix.shape[0]):
            print tab * '\t', matrix[i, :]
        return

    if type(data) is dict:
        keys = data.keys()
        for key in sorted(keys):
            if type(data[key]) is dict:
                print tab * '\t' + key + ':'
                printbinfile(data[key], tab + 1)
            elif type(data[key]) is list:
                print tab * '\t' + key + ':'
                printbinfile(data[key], tab + 1)
            elif type(data[key]) is numpy.matrixlib.defmatrix.matrix:
                print tab * '\t' + key + ':'
                printmatrix(data[key], tab + 1)
            elif type(data[key]) is numpy.ndarray:
                print tab * '\t' + key + ':', type(data[key]), 'shape:', \
                    data[key].shape
                #print data[key]
            else:
                print tab * '\t' + key + ':', data[key]
    elif type(data) is list:
        for item in data:
            printbinfile(item, tab)
    else:
        print type(data)
    return



def readDirsigBin(filename, isMac32=False):
    """Reads a DIRSIG bin file

    Keyword arguments:
    filename -- a string containing the file to read
    isMac32  -- a bool if DIRSIG was compiled on a 32 bit system. (default = False).
                flag to tell the code to use 32 long longs for the pulse data bytes
                field. In version 2 or later of the bin file, this was guarrenteed
                to be 64 bits in of the bin file and will have no effect on the
                data parsing.

    Returns:
    dict

    """

    def readPulse(fid, version, endian, xPixelCt, yPixelCt, isMac32):
        """Reads a pulse from a DIRSIG bin file

        Keyword arguments:
        fid      -- the file id to read a pulse from
        version  -- the version of the bin file
        endian   -- the endian of the data
        xPixelCt -- the number of pixels in the x direction
        yPixelCt -- the number of pixels in the y direction
        isMac32  -- a bool if DIRSIG was compiled on a 32 bit system. (default = False)

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
            # todo: Check reshaping was done right
            header['transmitter to mount affine'] = \
                numpy.mat(struct.unpack(endian + 16 * 'd', \
                fid.read(128))).reshape((4, 4))
        else:
            header['transmitter mount pointing offset'] = \
                numpy.mat(struct.unpack(endian + 3 * 'd', \
                fid.read(24)))
            header['tranmitter orientation angle order'] = fid.read(3)
        header['transmitter mount pointing rotation'] = \
                numpy.mat(struct.unpack(endian + 3 * 'd', \
                fid.read(24)))
        if version > 1:
            header['transmitter mount to platform affine'] = \
                numpy.mat(struct.unpack(endian + 16 * 'd', \
                fid.read(128))).reshape((4, 4))
            header['receiver to mount affine'] = \
                numpy.mat(struct.unpack(endian + 16 * 'd', \
                fid.read(128))).reshape((4, 4))
        else:
            header['receiver mount pointing offset'] = \
                numpy.mat(struct.unpack(endian + 3 * 'd', \
                fid.read(24)))
            header['receiver orientation angle order'] = fid.read(3)
        header['receiver mount pointing rotation'] = \
                numpy.mat(struct.unpack(endian + 3 * 'd', \
                fid.read(24)))
        if version > 1:
            header['receiver mount to platform affine'] = \
                numpy.mat(struct.unpack(endian + 16 * 'd', \
                fid.read(128))).reshape((4, 4))
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
        if isMac32 and (version < 2):
            header['pulse data bytes'] = struct.unpack(endian + 'I', \
                fid.read(4))[0]
        else:
            header['pulse data bytes'] = struct.unpack(endian + 'Q', \
                fid.read(8))[0]
        if version > 1:
            header['system transmit mueller matrix'] = \
                numpy.mat(struct.unpack(endian + 16 * 'd', \
                fid.read(128))).reshape((4, 4))
            header['system receive mueller matrix'] = \
                numpy.mat(struct.unpack(endian + 16 * 'd', \
                fid.read(128))).reshape((4, 4))
        output['header'] = header

        # read the data
        tmp = fid.read(header['pulse data bytes'])
        if header['data compression type'] == 1:
            tmp = zlib.decompress(tmp)

        tmp = struct.unpack(xPixelCt * yPixelCt * header['samples per time bin'] * \
            (header['time gate bin count'] + 1) * 'd', tmp)

        output['data'] = numpy.reshape(numpy.array(tmp), (xPixelCt, \
            yPixelCt, header['samples per time bin'] * \
            (header['time gate bin count'] + 1)))

        return output


    def readTask(fid, version, endian, xPixelCt, yPixelCt, isMac32):
        """Reads a pulse from a DIRSIG bin file

        Keyword arguments:
        fid      -- the file id to read a pulse from
        version  -- the version of the bin file
        endian   -- the endian of the data
        xPixelCt -- the number of pixels in the x direction
        yPixelCt -- the number of pixels in the y direction
        isMac32  -- a bool if DIRSIG was compiled on a 32 bit system. (default = False)

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
        for p in range(header['pulse count']):
            output['pulses'].append(readPulse(fid, version, endian, xPixelCt, \
                yPixelCt, isMac32))
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

        for t in range(header['task count']):
            output['tasks'].append(readTask(fid, _version, endian, \
                header['x pixel count'], header['y pixel count'], isMac32))

    except RuntimeError, e:
        sys.stderr.write('ERROR: #s\n' % str(e))
    finally:
        fid.close()

    return output


def getPassiveTerm(binData):
    """Returns the passive term for each pulse of a bin file

    Keyword arguments:
    binData -- the bin file

    Returns:
    dict

    """

    output = []
    for task in binData['tasks']:
        taskData = []
        for pulse in task['pulses']:
            taskData.append(pulse['data'][:, :, 0])
        output.append(taskData)
    return output


def getActiveTerm(binData):
    """Returns the active term for each pulse of a bin file

    Keyword arguments:
    binData -- the bin file

    Returns:
    dict

    """
    output = []
    for task in binData['tasks']:
        taskData = []
        for pulse in task['pulses']:
            taskData.append(pulse['data'][:, :, 1:])
        output.append(taskData)
    return output


def getTimeBinWidth(timeGateStart, timeGateStop, timeGateBinCount):
    """returns the width of a time bin in seconds

    Keyword arguments:
    timeGateStart    -- the time in seconds to open the range gate
    timeGateStop     -- the time in seconds to close the range gate
    timeGateBinCount -- the number of time bins

    Returns:
    float

    """
    if timeGateBinCount == 1:
        return timeGateStop - timeGateStart
    else:
        return (timeGateStop - timeGateStart) / float(timeGateBinCount - 1)


def packedBin2Signal(active, passive, timeBinWidth):
    """returns the waveform signal for a single waveform

    Keyword arguments:
    active       -- the active term (n x m x p numpy.array)
    passive      -- the passive term (n x m x 1 numpy.array)
    timeBinWidth -- the width of a time bin in seconds

    Returns:
    numpy.array

    """
    shape = active.shape

    # normalize the passive term by the time bin width in seconds
    passive = numpy.repeat(numpy.reshape(passive, (shape[0], shape[1], 1)), \
        shape[2], axis=2) * timeBinWidth

    return active + passive


def getSignal(bindata):
    """Returns the signal for all waveforms

    Keyword arguments:
    binData -- the bin file

    Returns:
    dict

    """
    output = []
    for task in bindata['tasks']:
        taskdata = []
        for pulse in task['pulses']:
            timebinwidth = getTimeBinWidth(pulse['header']['time gate start'], \
                pulse['header']['time gate stop'], \
                pulse['header']['time gate bin count'])
            taskdata.append(packedBin2Signal(pulse['data'][:, :, 1:], \
                pulse['data'][:, :, 0], timebinwidth))
        output.append(taskdata)
    return output


def getBinRange(bindata):
    """Returns the range in meters for each bin of each pulse

    Keyword arguments:
    binData -- the bin file

    Returns:
    dict

    """

    cd2 = 299792458. / 2.0 # speed of light over 2
    output = []
    for task in bindata['tasks']:
        taskdata = []
        for pulse in task['pulses']:
            taskdata.append(numpy.linspace(\
                pulse['header']['time gate start'] * cd2, \
                pulse['header']['time gate stop'] * cd2, \
                pulse['header']['time gate bin count']))

    return output

if __name__ == '__main__':
    Args = sys.argv[1:]
    if Args:
        filename = "\\ ".join(Args)

        printbinfile(readDirsigBin(filename))
