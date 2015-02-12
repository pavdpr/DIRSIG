#!/usr/bin/env python

"""This module provides tools for making parallel dirsig runs.

Public Repository:
    https://github.com/pavdpr/DIRSIG/

"""

__author__ = 'Paul Romanczyk'
__copyright__ = "Copyright 2015, Rochester Institute of Technology"
__credits__ = []
__license__ = "MIT"
#__version__ = "1.0"
__maintainer__ = "Paul Romanczyk"
__email__ = "par4249@rit.edu"
__status__ = "Production"

import multiprocessing
import os
import re

def find_sims_by_regex(regex, pth='.'):
    """Finds sim files in a directory tree by using regular expressions.

    Args:
        regex (_sre.SRE_Pattern): The regular expression to use. This should
        be compiled e.g., re.compile(r'.+sim') which will find all sim files.
        pth (str, optional): The path to search. The default is '.'.

    Returns:
        A list of all list of strings containing all files that match the regex.
            If no matches are found, the list will be empty.
    """

    output = []

    # search the directory tree starting with pth
    for root, _, files in os.walk(pth):
        for current_file in files:
            if regex.search(current_file):
                # check if the file alone matches the regex
                output.append(os.path.join(root, current_file))
            elif regex.search(os.path.join(root, current_file)):
                # check if the file and directory matches the regex
                output.append(os.path.join(root, current_file))

    return output


def clean_cmd(cmd):
    """Removes multiple spaces and whitespace at beginning or end of command.

    Args:
        cmd (str): A string containing the command to clean.

    Returns:
        A cleaned command string.
    """

    return re.sub(r'\s{2, }', ' ', cmd).strip(' \t\n\r')


def cd_for_run(cmd, pth='.', delim=';'):
    """Modifies the DIRSIG command to change directories.

    This will add add a cd command to execute before the dirsig call. After the
    dirsig call, it will add a second cd to change directories back to the
    original one. If the directory (pth) is '.', the original command will be
    returned.

    Args:
        cmd (str): The dirsig command to run in between the cd commands.
        pth (str, optional): A string containing the path to change to. The
            default is '.'.
        delim (str, optional): The deliminater betwen the cd's and command. The
            default is ';'.

    Notes:
        This should be run from the directory where the main call will be made
        to get the paths right.

    Exceptions:
        RuntimeError: If pth does not exist.

    Returns:
        A string with the new command including the cd commands.
    """

    if os.path.relpath(pth) == '.':
        return cmd
    try:
        if not os.path.isdir(pth):
            raise RuntimeError(pth + ' does not exist')

        return clean_cmd('cd ' + pth + delim + ' ' + cmd + delim + ' cd ' + \
            os.path.relpath(os.getcwd(), pth))
    except RuntimeError, error:
        raise error


def make_dirsig_command(sim, options=None, dirsig='dirsig', logfile='log'):
    """ Makes a command to rund dirsig.

    Args:
        sim (str): A string containing the name of the sim file.
        options (str, optional): A string contating options to pass to dirsig.
            The default is None.
        dirsig (str, optional): A string containing the executable to of dirsig
            to use. The default is 'dirsig'.
        logfile (str, optional): A string contating the name of the logfile to
            write to. The default is 'log'.

    Returns:
        A string for the dirsig command to call.
    """

    # which dirsig to use
    cmd = dirsig

    # set options
    if options:
        cmd += ' ' + options

    # add the sim
    cmd += ' ' + sim

    # add a log file.
    cmd += ' &> ' + logfile

    # clean the dirsig command
    return clean_cmd(cmd)


def parallel_run_dirsig(cmds, processes=2):
    """Executes dirsig runs in parallel.

    Args:
        cmds (str): A list of strings, where each string is a dirsig command to
            execute.
        processes (int, optional): The number of processes to run at a time. The
            default is 2.

    Returns:
        None
    """

    pool = multiprocessing.Pool(processes=processes)
    pool.map(os.system, cmds)

    return


if __name__ == '__main__':
    # find some sim files
    sims = find_sims_by_regex(re.compile(r'.+\.sim'))

    # make dirsig commands
    cmds = []
    for sim in sims:
        (d, simfile) = os.path.split(sim)
        cmds.append(cd_for_run(make_dirsig_command(simfile), pth=d))

    # run dirsig
    parallel_run_dirsig(cmds)

