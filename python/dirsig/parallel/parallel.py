#!/usr/bin/env python

"""This module provides tools for making parallel dirsig runs.

Public Repository:
    https://github.com/pavdpr/DIRSIG/

USAGE:
    python parallel.py [options]    or
    parallel.py [options]           If execute permissions on parallel.py and it is
                                    in the path.

    [options] are:
    --path=<path>               Set the path to search for sim files from. The
                                default is the path where this command is executed
                                from.
    --processes=<number>        Set the number of processes to run simultaneously.
                                The default is 2.
    --regex=<regex>             Set the regular expression to search for sim files.
                                Quotes may be needed around the regular expression
                                to properly pass it to python. The default is
                                r'.+\.sim' (all sim files)
    --dirsig=<dirsig version>   Set the dirsig executable name. The default is
                                dirsig.
    --logfile=<log file name>   Set the logfile name. The default is log.
    --option=<option>           Set an option to pass to the dirsig executable.
                                Multiple options need to be passed independantly.

    Notes:
    - The angle brackets after each of the above options should NOT be included.
    - There should be NO spaces on either side of the equals.

SAMPLE USAGE:
    parallel.py
        Runs with all defaults.

    parallel.py --path=/some/path --dirsig=dirsig-4.7.0 --processes=8
        Searches for all sim files in /some/path and executes dirsig-4.7.0 on 8
        cores.

    parallel.py --option=--mode=preview --option=--output_prefix=foobar
        Runs dirsig in preview mode and with an output prefix of foobar. This runs
        dirsig --mode=preview --output_prefix=foobar sim.sim &> log

    parallel.py --regex="simulation.*\.sim'
        Searches for all simulations that match simulation.*\.sim
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


def cd_for_run(cmd, pth='.', delim=';', basepath=None):
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
        basepath (str, optional): A string containing the refence path. If none,
            basepath will default to os.getcwd().

    Notes:
        This should be run from the directory where the main call will be made
        to get the paths right.

    Exceptions:
        RuntimeError: If pth does not exist.

    Returns:
        A string with the new command including the cd commands.
    """

    try:
        if not os.path.isdir(pth):
            raise RuntimeError("The sim path '" + pth + "' does not exist")
        if not basepath:
            basepath = os.getcwd()
        elif not os.path.isdir(basepath):
            raise RuntimeError("The base path '" + basepath + "' does not exist")

        if os.path.relpath(basepath, pth) == '.':
            return cmd

        return clean_cmd('cd ' + os.path.relpath(pth, basepath) + delim + ' ' + \
            cmd + delim + ' cd ' + os.path.relpath(basepath, pth))
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
    # set defaults
    REGEX = r'.+\.sim'
    DIRSIG = 'dirsig'
    PATH = '.'
    BASEPATH = None
    PROCESSES = 2
    LOGFILE = 'log'
    OPTIONS = None

    import sys
    ARGS = sys.argv[1:]

    REGEXREGEX1 = re.compile(r'regex="(.*)"', re.IGNORECASE)
    REGEXREGEX2 = re.compile(r"regex='(.*)'", re.IGNORECASE)

    I = 0
    while I < len(ARGS):
        ARG = ARGS[I]
        if ARG.lower().startswith('--path='):
            PATH = ARG[7:]
        # elif ARG.lower().startswith('--basepath='):
        #     BASEPATH = ARG[11:]
        elif ARG.lower().startswith('--processes='):
            PROCESSES = int(ARG[12:])
        elif ARG.lower().startswith('--regex='):
            REGEX = ARG[8:]#.decode('string_escape')
        elif ARG.lower().startswith('--dirsig='):
            DIRSIG = ARG[9:]
        elif ARG.lower().startswith('--logfile='):
            LOGFILE = ARG[10:]
        elif ARG.lower().startswith('--option='):
            if OPTIONS:
                OPTIONS += ' ' + ARG[9:]
            else:
                OPTIONS = ARG[9:]
        else:
            sys.exit("'" + ARG + "' is an unexpected command line option.")
        I += 1

    # find some sim files
    SIMS = find_sims_by_regex(re.compile(REGEX), pth=PATH)

    # make dirsig commands
    CMDS = []
    for SIM in SIMS:
        (DIR, SIMFILE) = os.path.split(SIM)
        CMDS.append(\
            cd_for_run(\
                make_dirsig_command(SIMFILE, options=OPTIONS, logfile=LOGFILE), \
                pth=DIR, basepath=BASEPATH))

    # run dirsig
    parallel_run_dirsig(CMDS, processes=PROCESSES)

