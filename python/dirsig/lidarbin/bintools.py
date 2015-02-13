#!/usr/bin/env python

"""This module provides basic manipulation of a dirsig bin file.

Usage:
    To read a bin file:
        binfile = readDirsigBin(filename)
    To get the true signals:
        signal = getSignal( binfile )
    To get the range of each time bin for each pulse:
        range = getBinRange( binfile )

External Dependancies:
    numpy

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

import numpy



def print_bin_file(data, tab=0):
    """Prints a bin file.

    This prints the contents of a bin file. This is mostly used for debugging.

    Args:
        data (dict): The bin file to print.
        tab (int, optional): the number of tabs to use. The default is 0.

    Returns:
        None

    Warning:
        You may not want to use this on bin files with many pulses as it will
        print alot.

    """

    def print_matrix(matrix, tab):
        """Prints a numpy.matrix with tabs.

        Args:
            matrix (numpy.matrix): The matrix to print.
            tab  (int): the number of tabs to use.

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
                print_bin_file(data[key], tab + 1)
            elif type(data[key]) is list:
                print tab * '\t' + key + ':'
                print_bin_file(data[key], tab + 1)
            elif type(data[key]) is numpy.matrixlib.defmatrix.matrix:
                print tab * '\t' + key + ':'
                print_matrix(data[key], tab + 1)
            elif type(data[key]) is numpy.ndarray:
                print tab * '\t' + key + ':', type(data[key]), 'shape:', \
                    data[key].shape
                #print data[key]
            else:
                print tab * '\t' + key + ':', data[key]
    elif type(data) is list:
        for item in data:
            print_bin_file(item, tab)
    else:
        print type(data)
    return


def get_passive_term(bin_data):
    """Returns the passive term for each pulse of a bin file.

    Args:
        bin_data (dict): The bin file.

    Returns:
        A list containing tasks. Each task is a list containing a numpy.array
        with the passive term.

    """

    output = []
    for task in bin_data['tasks']:
        task_data = []
        for pulse in task['pulses']:
            task_data.append(pulse['data'][:, :, 0])
        output.append(task_data)
    return output


def get_active_term(bin_data):
    """Returns the active term for each pulse of a bin file.

    Args:
        bin_data (dict): The bin file.

    Returns:
        A list containing tasks. Each task is a list containing a numpy.array
        with the active term.

    """
    output = []
    for task in bin_data['tasks']:
        task_data = []
        for pulse in task['pulses']:
            task_data.append(pulse['data'][:, :, 1:])
        output.append(task_data)
    return output


def get_time_bin_width(time_gate_start, time_gate_stop, time_gate_bin_count):
    """Returns the width of a time bin in seconds.

    Args:
        time_gate_start (float): The time in seconds to open the range gate.
        time_gate_stop (float): The time in seconds to close the range gate.
        time_gate_bin_count (int): The number of time bins.

    Returns:
        A float containing thw width of a time bin in seconds.

    """
    if time_gate_bin_count == 1:
        return time_gate_stop - time_gate_start
    else:
        return (time_gate_stop - time_gate_start) / float(time_gate_bin_count - 1)


def packed_bin_to_signal(active, passive, time_bin_width):
    """Computes the signal for a waveform.

    Combines the passive and active terms to compute the signal. The units of the
    active term are photons, the passive term are photons/second, and the time
    bin width is in seconds. The singal can be computed using:
        signal = active + passive * time_bin_width

    Args:
        active (numpy.array): The active term (n x m x p). The units are photons.
        passive (numpy.array): The passive term (n x m x 1 numpy.array). The
            units are photons/second.
        time_bin_width (float): The width of a time bin. The units are seconds.

    Returns:
        A numpy.array of size n x m x p (same as the active compontent)
        containing the signal.

    """
    shape = active.shape

    # normalize the passive term by the time bin width in seconds
    passive = numpy.repeat(numpy.reshape(passive, (shape[0], shape[1], 1)), \
        shape[2], axis=2) * time_bin_width

    return active + passive


def get_signal(bin_data):
    """Returns the signal (in photons) for each pulse of a bin file.

    Args:
        bin_data (dict): The bin file.

    Returns:
        A list containing tasks. Each task is a list containing a numpy.array
        with the signal.

    """
    output = []
    for task in bin_data['tasks']:
        task_data = []
        for pulse in task['pulses']:
            time_bin_width = get_time_bin_width(pulse['header']['time gate start'], \
                pulse['header']['time gate stop'], \
                pulse['header']['time gate bin count'])
            task_data.append(packed_bin_to_signal(pulse['data'][:, :, 1:], \
                pulse['data'][:, :, 0], time_bin_width))
        output.append(task_data)
    return output


def get_bin_range(bin_data):
    """Returns the range in meters for each pulse.

    Args:
        bin_data (dict): The bin file.

    Returns:
        A list containing tasks. Each task is a list containing a numpy.array
        of size 1 x 1 x p (same number of time bins as the active part of the
        signal) contating the range in meters to each time bin.

    """

    cd2 = 299792458. / 2.0 # speed of light over 2
    output = []
    for task in bin_data['tasks']:
        task_data = []
        for pulse in task['pulses']:
            task_data.append(numpy.linspace(\
                pulse['header']['time gate start'] * cd2, \
                pulse['header']['time gate stop'] * cd2, \
                pulse['header']['time gate bin count']))

    return output
