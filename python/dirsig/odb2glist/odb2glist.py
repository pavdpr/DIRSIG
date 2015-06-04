#!/usr/bin/env python

""" Code for converting a DIRSIG odb file to a DIRSIG glist file.

DESCRIPTION:
    This provides a python script for converting a DIRSIG [1] odb file [2]
    into a DIRSIG glist file [3]. This is to help facilitate the transition
    to the newer file type and make it easier to access the functionality
    that is now present in a glist file.

PUBLIC REPOSITORY:
    https://github.com/pavdpr/DIRSIG/

USE:
    To use as a stand-alone executable:
    Run either
        odb2glist.py [options] filename.odb
        python odb2glist.py [options] filename.odb
    This assumes that odb2glist.py is in your PATH. The default output will be
    a glist file in the same directory as the odb file.

HISTORY:
    2014-06-01: Paul Romanczyk
    - Initial version.

    2014-06-04: Paul Romanczyk
    - Fixed a bug in the box base geometry.
    - Fixed a bug where centimeters would be treated as meters.
    - Fixed a bug caused by a stray i += 1.
    - Fixed a bug caused by a comma separated affine matrix instance.
    - Added ability to handle comments.
    - Added CURVED_FRUSTUM support.
    - Added line numbers of input file to help with debugging.
    - Updated documentation.

    2014-06-05: Paul Romanczyk
    - I can't spell: "rotation" not "rotatation".
    - Updated documentation.

    2014-06-11: Paul Romanczyk
    - Switched to failure cases returning False (instead of NULL).
    - Updated documentation.
    - Fixed some more spelling.

    2014-06-12: Paul Romanczyk
    - Allowed for negative scales. This will be turned on again in 4.6.0 [4].

    2015-06-01: Paul Romanczyk
    - Updated syntax.
    - Cleaned up command-line interface.
    - Updated documentation.

    2015-06-03: Paul Romanczyk
    - Updated engine.
    - Separated components into separate functions.
    - Added exceptions.

    2015-06-04: Paul Romanczyk
    - Added ability to change options from command line.
    - Changed case of variables in __main__ to make pylint happier.
    - Added a comment say which file this was made from to help track down any
      bugs.
    - Added an exception if DIRSIG_ODB is not the first line of the odb file.
    - Fixed a few bugs from the refactoring of the code.
    - Added more usefull exception messages.

    TODO:
    - Add recursive functionality to convert any sub-odb files to glists.

KNOWN ISSUES:
    - This will not work if there are spaces in the filename.
    - This will not work if the units appear before the (gdb|obj|etc) name.

WARNINGS:
    - DIRSIG before 4.6.0 will not allow a negative scale on a glist [4].
    - This does not (currently) recursively change included odb files to
    glist files.

LICENSE:
    The MIT License (MIT)

    Copyright 2014-2015 Rochester Institute of Technology

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.

REFERENCES:
    [1] http://www.dirsig.org/
    [2] http://www.dirsig.org/docs/new/odb.html
    [3] http://www.dirsig.org/docs/new/glist.html
    [4] http://www.dirsig.org/bugzilla/show_bug.cgi?id=1103

"""


# import other packages
import datetime
import os
import re
import sys
import xml.etree.ElementTree
import xml.dom.minidom


def prettify(elem, indent="  "):
    """ Returns a pretty-printed XML string.

    DESCRIPTION:
        Returns a pretty-printed (human-readable) string of the element.

    KEYWORD ARGUMENTS:
        elem (xml.etree.ElementTree.Element): the element (and any children of
            it) to convert.
        indent (str, optional): the string containing the indent syntax.

    RETURNS:
        A str containing the formatted XML element (and its children).

    NOTES:
        The first line will be "<?xml version="1.0" ?>".

    TODO:
        Write my own version to ommit the xml version line and allow for
        DIRSIG-friendly formatting.

    REFERENCES:
        http://pymotw.com/2/xml/etree/ElementTree/create.html
    """

    rough_string = xml.etree.ElementTree.tostring(elem, "utf-8")
    reparsed = xml.dom.minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent=indent)


def get_right_of_equals(line):
    """ Returns the text to the right of an equals.

    DESCRIPTION:
        Get the text to the right of an equals sign.

    KEYWORD ARGUMENTS:
        line (str): the line to search.

    RETURNS:
        str: the text to the right of an equals sign.

    """
    tmpline = line.split("=")
    tmpline = tmpline[-1]
    tmpline = tmpline.strip()
    return tmpline


def xyz2point(x_loc, y_loc, z_loc):
    """ Makes a point triplet out of x, y, and z data.

    DESCRIPTION:

    KEYWORD ARGUMENTS:
        x_loc: the 1st coordinate
        y_loc: the 2nd coordinate
        z_loc: the 3rd coordinate

    RETURNS:
        xml.etree.ElementTree.Element with the name "point" and sub-elements "x",
        "y", and "z".

    NOTES:
        x_loc, y_loc, and z_loc only need to be convertable to a str. There are
        not any checks to see that they are valid point values.

    REFERENCES:

    """
    point = xml.etree.ElementTree.Element("point")
    xelem = xml.etree.ElementTree.SubElement(point, "x")
    xelem.text = str(x_loc).strip()
    yelem = xml.etree.ElementTree.SubElement(point, "y")
    yelem.text = str(y_loc).strip()
    zelem = xml.etree.ElementTree.SubElement(point, "z")
    zelem.text = str(z_loc).strip()
    return point


def xyz2cartesiantriple(x_loc, y_loc, z_loc):
    """ Makes a cartesiantriple triplet out of x, y, and z data.

    DESCRIPTION:

    KEYWORD ARGUMENTS:
        x_loc: the 1st coordinate
        y_loc: the 2nd coordinate
        z_loc: the 3rd coordinate

    RETURNS:
        xml.etree.ElementTree.Element with the name "cartesiantriple" and
        sub-elements "x", "y", and "z".

    NOTES:
        x_loc, y_loc, and z_loc only need to be convertable to a str. There are
        not any checks to see that they are valid cartesiantriple values.

    REFERENCES:

    """
    cartesiantriple = xml.etree.ElementTree.Element("cartesiantriple")
    xelem = xml.etree.ElementTree.SubElement(cartesiantriple, "x")
    xelem.text = str(x_loc).strip()
    yelem = xml.etree.ElementTree.SubElement(cartesiantriple, "y")
    yelem.text = str(y_loc).strip()
    zelem = xml.etree.ElementTree.SubElement(cartesiantriple, "z")
    zelem.text = str(z_loc).strip()
    return cartesiantriple


def odb_parseinfo(line, build_all_instances=False):
    """ Converts an odb instance info into glist format.

    DESCRIPTION:
        Converts an odb instance info into a glist format.

    KEYWORD ARGUMENTS:
        line (str): the line to convert. "INFO" is expected to be part of the
            line.
        build_all_instances (bool, optional): A flag to tell the converter to
            fully defined static instance. The default is False. If false, the
            minimum static instance will be used. This is only applied to objects
            and not primatives.

    RETURNS:
        xml.etree.ElementTree.Element: the glist version of the instance.

    EXCEPTIONS:
        RuntimeError: if not a valid instance.

    """
    try:
        if "INFO" not in line:
            msg = "There should be an INFO here"
            raise RuntimeError(msg)

        line = get_right_of_equals(line)

        # a dynamic instance controlled by a mov file
        if ".mov" in line:
            # we are a dynamic instance
            # Do I need to worry about ppd files? or is that a glist feature?

            info = xml.etree.ElementTree.Element("dynamicinstance")
            kfm = xml.etree.ElementTree.SubElement(info, "keyframemovement")
            filename = xml.etree.ElementTree.SubElement(kfm, "filename")
            filename.text = line

        # we are either a 9-ple or 16-ple that is comma separated
        elif "," in line:
            # separate by comma
            line = line.split(",")

            # remove whitespace
            line = [tmp.strip() for tmp in line]

            # check that we are valid (that we have 9 or 16 elements)
            if len(line) == 9:
                # we are a 9-ple

                # make a static instance
                info = xml.etree.ElementTree.Element("staticinstance")

                if (float(line[0]) != 0.0) or (float(line[1]) != 0.0) or \
                    (float(line[2]) != 0.0) or build_all_instances:

                    # make a translation
                    translation = xml.etree.ElementTree.SubElement(info, \
                        "translation")
                    translation.append(xyz2point(line[0], line[1], line[2]))

                if (float(line[3]) == 0.0) or (float(line[4]) == 0.0) or \
                    (float(line[5]) == 0.0):
                    msg = "Glist files only support non-zero scales."
                    raise RuntimeError(msg)

                elif (float(line[3]) != 1.0) or (float(line[4]) != 1.0) or \
                    (float(line[5]) != 1.0) or build_all_instances:

                    # make a scale
                    scale = xml.etree.ElementTree.SubElement(info, "scale")
                    scale.append(xyz2cartesiantriple(line[3], line[4], line[5]))

                if (float(line[6]) != 0.0) or (float(line[7]) != 0.0) or \
                    (float(line[8]) != 0.0) or build_all_instances:

                    # make a rotation
                    rotation = xml.etree.ElementTree.SubElement(info, "rotation")
                    rotation.append(xyz2cartesiantriple(line[6], line[7], line[8]))

            elif len(line) == 16:
                # we are a 16-ple

                # make a static instance
                info = xml.etree.ElementTree.Element("staticinstance")

                # make a matrix
                matrix = xml.etree.ElementTree.SubElement(info, "matrix")
                matrix.text = ", ".join(line)
            else:
                msg = "I am not sure how to parse the line.\n" + \
                    "I was expecting either 9 or 16 comma separated values"
                raise RuntimeError(msg)

        else:
            # assume 4x4 affine matrix, split by white space
            # can I have a space separated 9-ple here?
            regex = re.compile(r"\s+")
            tmp = regex.split(line)
            if len(tmp) != 16:
                # we expect 16 elements in this line
                msg = "I am not sure how to parse the line.\n" + \
                    "I was expecting either 16 space separated values"
                raise RuntimeError(msg)

            # convert to xml (requires values be comma separated)
            # make a static instance
            info = xml.etree.ElementTree.Element("staticinstance")
            matrix = xml.etree.ElementTree.SubElement(info, "matrix")
            matrix.text = ", ".join(tmp)
        return info
    except Exception:
        raise


def odb_object2glist(odb, lineno, build_all_instances=False):
    """ Converts an odb object to glist format

    DESCRIPTION:
        Converts an odb file into the equivalent glist file. This is to facilitate
        make use of the additional features that are available from glist files.

    KEYWORD ARGUMENTS:
        odb (list of str): the file from which a object is read.
        lineno (int): the line of odb to start from.
        build_all_instances (bool, optional): A flag to tell the converter to
            fully defined static instance. The default is False. If false, the
            minimum static instance will be used. This is only applied to objects
            and not primatives.

    RETURNS:
        xml.etree.ElementTree.Element: the glist version of the object.

    EXCEPTIONS:
        RuntimeError: if not a valid object.

    """
    try:
        if "OBJECT" not in odb[lineno]:
            msg = "At line " + str(lineno) + ",\n" + \
                "Not a OBJECT.\n" + \
                odb[lineno]
            raise RuntimeError(msg)

        # set up the xml to handle an object
        obj = xml.etree.ElementTree.Element("object")
        basegeo = xml.etree.ElementTree.SubElement(obj, "basegeometry")
        units = None

        run = True
        while run:
            lineno += 1

            # Should not need this case, probably should remove
            if lineno >= len(odb):
                run = False

            # Skip any empty lines
            elif len(odb[lineno].strip()) == 0:
                pass

            # stop running if the closing bracket is found
            elif "}" in odb[lineno]:
                run = False

            # we have a comment
            elif "#" in odb[lineno]:
                # assume we are a comment
                tmp = odb[lineno]
                comment = xml.etree.ElementTree.Comment(text=(tmp[1:]).strip())
                basegeo.append(comment)

            # We are including some type of file.
            elif "_FILENAME" in odb[lineno]:
                # We want either a gdb, obj, or odb file
                if "GDB_FILENAME" in odb[lineno]:
                    geotype = xml.etree.ElementTree.SubElement(basegeo, "gdb")
                elif "OBJ_FILENAME" in odb[lineno]:
                    geotype = xml.etree.ElementTree.SubElement(basegeo, "obj")
                elif "ODB_FILENAME" in odb[lineno]:
                    geotype = xml.etree.ElementTree.SubElement(basegeo, "odb")
                else:
                    msg = "At line " + str(lineno) + "\nUnsupported geometry type."
                    raise RuntimeError(msg)

                # add the filename
                filename = xml.etree.ElementTree.SubElement(geotype, "filename")
                filename.text = get_right_of_equals(odb[lineno])

            # Add units
            elif "UNITS" in odb[lineno]:
                if "CENTIMETERS" in odb[lineno]:
                    # this needs to come before meters since meters is in
                    # centimeters
                    units = "centimeters"
                elif "METERS" in odb[lineno]:
                    units = "meters"
                    # consider using pass here since the default is meters
                elif "FEET" in odb[lineno]:
                    units = "feet"
                elif "INCHES" in odb[lineno]:
                    units = "inches"
                else:
                    msg = "At line " + str(lineno) + "\nUnsupported units."
                    raise RuntimeError(msg)

            # we have found a set of instances
            elif "INSTANCES" in odb[lineno]:
                # get the instance(s)
                run2 = True
                while run2:
                    lineno += 1

                    # ignore empty lines
                    if len(odb[lineno].strip()) == 0:
                        pass

                    # stop running
                    elif "}" in odb[lineno]:
                        run2 = False

                    # we found a comment
                    elif "#" in odb[lineno]:
                        tmp = odb[lineno]
                        comment = xml.etree.ElementTree.Comment(\
                            text=(tmp[1:]).strip())
                        obj.append(comment)

                    # We have found an info
                    elif "INFO" in odb[lineno]:
                        # used a separate try to add file line info
                        try:
                            obj.append(odb_parseinfo(odb[lineno], \
                                build_all_instances=build_all_instances))
                        except Exception, exception:
                            raise RuntimeError('At line ' + str(lineno) + \
                                ':\n' + exception.message)
                    else:
                        msg = "At line " + str(lineno) + "\n" + \
                            "There should be an INFO here."
                        raise RuntimeError(msg)

            # Add the units to the geotype.
            # This was moved to allow for units to appear before the filename.
            if units:
                geotype.set("units", units)

        return obj, lineno

    except Exception:
        raise


def odb_sphere2glist(odb, lineno):
    """ Converts an odb sphere to a glist sphere.

    DESCRIPTION:
        Converts an odb sphere to a glist sphere. The first line of the odb file
        that is read is expected to contain "SPHERE".

    KEYWORD ARGUMENTS:
        odb (list of str): the file from which a sphere object is read.
        lineno (int): the line of odb to start from.

    RETURNS:
        xml.etree.ElementTree.Element: the glist version of the sphere.

    EXCEPTIONS:
        RuntimeError: if not a valid sphere object.

    """

    try:
        # verify that we are a sphere
        if "SPHERE" not in odb[lineno]:
            msg = "At line " + str(lineno) + ",\n" + \
                "Not a SPHERE primitive." + \
                odb[lineno]
            raise RuntimeError(msg)
        run = True
        primitive = xml.etree.ElementTree.Element("object")
        basegeo = xml.etree.ElementTree.SubElement(primitive, "basegeometry")
        sphere = xml.etree.ElementTree.SubElement(basegeo, "sphere")
        while run:
            lineno += 1

            if lineno >= len(odb):
                run = False
            elif len(odb[lineno].strip()) == 0:
                pass
            elif "}" in odb[lineno]:
                run = False
            elif "RADIUS" in odb[lineno]:
                radius = xml.etree.ElementTree.SubElement(sphere, "radius")
                radius.text = get_right_of_equals(odb[lineno])
            elif "CENTER" in odb[lineno]:
                center = xml.etree.ElementTree.SubElement(sphere, "center")
                tmp = get_right_of_equals(odb[lineno])
                tmp = tmp.split(",")
                center.append(xyz2point(tmp[0], tmp[1], tmp[2]))
            elif "MATERIAL_IDS" in odb[lineno]:
                matid = xml.etree.ElementTree.SubElement(sphere, "matid")
                matid.text = get_right_of_equals(odb[lineno])
            else:
                msg = "At line " + str(lineno) + ",\n" + \
                    "Unexpected line in SPHERE primitive." + \
                    odb[lineno]
                raise RuntimeError(msg)

        # add a static instance with no parameters!
        staticinstance = xml.etree.ElementTree.SubElement(primitive, "staticinstance")

        return primitive, lineno

    except Exception:
        raise


def odb_groundplane2glist(odb, lineno):
    """ Converts an odb ground plane to a glist ground plane.

    DESCRIPTION:
        Converts an odb ground plane to a glist sphere. The first line of the odb
        file that is read is expected to contain "GROUND_PLANE".

    KEYWORD ARGUMENTS:
        odb (list of str): the file from which a groundplane object is read.
        lineno (int): the line of odb to start from.

    RETURNS:
        xml.etree.ElementTree.Element: the glist version of the groundplane.

    EXCEPTIONS:
        RuntimeError: if not a valid groundplane object.

    """

    try:
        if "GROUND_PLANE" not in odb[lineno]:
            msg = "At line " + str(lineno) + ",\n" + \
                "Not a GROUND_PLANE primitive." + \
                odb[lineno]
            raise RuntimeError(msg)

        run = True
        primitive = xml.etree.ElementTree.Element("object")
        basegeo = xml.etree.ElementTree.SubElement(primitive, "basegeometry")
        groundplane = xml.etree.ElementTree.SubElement(basegeo, "groundplane")
        while run:
            lineno += 1
            if lineno >= len(odb):
                run = False
            elif len(odb[lineno].strip()) == 0:
                pass
            elif "}" in odb[lineno]:
                run = False
            elif "ANCHOR" in odb[lineno]:
                anchor = xml.etree.ElementTree.SubElement(groundplane, "anchor")
                tmp = get_right_of_equals(odb[lineno])
                tmp = tmp.split(",")
                anchor.append(xyz2point(tmp[0], tmp[1], tmp[2]))
            elif "MATERIAL_ID" in odb[lineno]:
                matid = xml.etree.ElementTree.SubElement(groundplane, "matid")
                matid.text = get_right_of_equals(odb[lineno])
            elif "ADD_CHECKS" in odb[lineno]:
                run2 = True
                while run2:
                    lineno += 1
                    checkers = xml.etree.ElementTree.SubElement(groundplane, "checkers")
                    if lineno >= len(odb):
                        run2 = False
                    elif len(odb[lineno].strip()) == 0:
                        pass
                    elif "}" in odb[lineno]:
                        run2 = False
                    elif "MATERIAL_ID" in odb[lineno]:
                        checkers.set("matid", get_right_of_equals(odb[lineno]))
                    elif "WIDTH" in odb[lineno]:
                        checkers.set("width", get_right_of_equals(odb[lineno]))
                    else:
                        msg = "At line " + str(lineno) + ":\n" + \
                            "I do not know what to do with this line in " + \
                            "GROUND_PLANE:ADD_CHECKS\n" + \
                            odb[lineno]
                        raise RuntimeError(msg)

            else:
                msg = "At line " + str(lineno) + ":\n" + \
                    "Unexpected line in GROUND_PLANE primitive" + \
                    odb[lineno]
                raise RuntimeError(msg)

        # add a static instance with no parameters!
        staticinstance = xml.etree.ElementTree.SubElement(primitive, \
            "staticinstance")

        return primitive, lineno

    except Exception:
        raise


def odb_secchidisk2glist(odb, lineno):
    """ Converts an odb secchi disk to a glist secchi disk.

    DESCRIPTION:
        Converts an odb secchi disk to a glist secchi disk. The first line of the
        odb file that is read is expected to contain "SECCHI_DISK".

    KEYWORD ARGUMENTS:
        odb (list of str): the file from which a secchi disk object is read.
        lineno (int): the line of odb to start from.

    RETURNS:
        xml.etree.ElementTree.Element: the glist version of the secchi disk.

    EXCEPTIONS:
        RuntimeError: if not a valid secchi disk object.

    """
    try:
        if "SECCHI_DISK" not in odb[lineno]:
            msg = "At line " + str(lineno) + ",\n" + \
                "Not a SECCHI_DISK primitive.\n" + \
                odb[lineno]
            raise RuntimeError(msg)

        run = True
        primitive = xml.etree.ElementTree.Element("object")
        basegeo = xml.etree.ElementTree.SubElement(primitive, "basegeometry")
        secchidisk = xml.etree.ElementTree.SubElement(basegeo, "secchidisk")

        # secchidisk locations are in the static instance part of the glist!
        staticinstance = xml.etree.ElementTree.SubElement(primitive, \
            "staticinstance")

        while run:
            lineno += 1

            if lineno >= len(odb):
                run = False
            elif len(odb[lineno].strip()) == 0:
                pass
            elif "}" in odb[lineno]:
                run = False
            elif "RADIUS" in odb[lineno]:
                radius = xml.etree.ElementTree.SubElement(secchidisk, "radius")
                radius.text = get_right_of_equals(odb[lineno])
            elif "CENTER" in odb[lineno]:
                translation = xml.etree.ElementTree.SubElement(staticinstance, \
                    "translation")
                tmp = get_right_of_equals(odb[lineno])
                tmp = tmp.split(",")
                translation.append(xyz2point(tmp[0], tmp[1], tmp[2]))
            elif "MATERIAL_IDS" in odb[lineno]:
                matid_a = xml.etree.ElementTree.SubElement(secchidisk, "matid_a")
                matid_b = xml.etree.ElementTree.SubElement(secchidisk, "matid_b")
                tmp = (get_right_of_equals(odb[lineno])).split(",")
                matid_a.text = (tmp[0]).strip()
                matid_b.text = (tmp[1]).strip()
            else:
                msg = "At line " + str(lineno) + ":\n" + \
                    "Unexpected line in SECCHI_DISK primitive" + \
                    odb[lineno]
                raise RuntimeError(msg)

        return primitive, lineno
    except Exception:
        raise


def odb_disk2glist(odb, lineno):
    """ Converts an odb disk to a glist disk.

    DESCRIPTION:
        Converts an odb disk to a glist disk. The first line of the odb file
        that is read is expected to contain "DISK", but not "SECCHI".

    KEYWORD ARGUMENTS:
        odb (list of str): the file from which a disk object is read.
        lineno (int): the line of odb to start from.

    RETURNS:
        xml.etree.ElementTree.Element: the glist version of the disk.

    EXCEPTIONS:
        RuntimeError: if not a valid disk object.

    """
    try:
        if "DISK" not in odb[lineno] or "SECCHI" in odb[lineno]:
            msg = "At line " + str(lineno) + ",\n" + \
                "Not a DISK primitive.\n" + \
                odb[lineno]
            raise RuntimeError(msg)
        run = True
        primitive = xml.etree.ElementTree.Element("object")
        basegeo = xml.etree.ElementTree.SubElement(primitive, "basegeometry")
        disk = xml.etree.ElementTree.SubElement(basegeo, "disk")

        # disk locations are in the static instance part of the glist!
        staticinstance = xml.etree.ElementTree.SubElement(primitive, \
            "staticinstance")

        while run:
            lineno += 1

            if lineno >= len(odb):
                run = False
            elif len(odb[lineno].strip()) == 0:
                pass
            elif "}" in odb[lineno]:
                run = False
            elif "RADIUS" in odb[lineno]:
                radius = xml.etree.ElementTree.SubElement(disk, "radius")
                radius.text = get_right_of_equals(odb[lineno])
            elif "CENTER" in odb[lineno]:
                translation = xml.etree.ElementTree.SubElement(staticinstance, \
                    "translation")
                tmp = get_right_of_equals(odb[lineno])
                tmp = tmp.split(",")
                translation.append(xyz2point(tmp[0], tmp[1], tmp[2]))
            elif "MATERIAL_ID" in odb[lineno]:
                matid = xml.etree.ElementTree.SubElement(disk, "matid")
                matid.text = get_right_of_equals(odb[lineno])
            else:
                msg = "At line " + str(lineno) + ":\n" + \
                    "Unexpected line in DISK primitive\n" + \
                    odb[lineno]
                raise RuntimeError(msg)

        return primitive, lineno

    except Exception:
        raise


def odb_box2glist(odb, lineno):
    """ Converts an odb box to a glist box.

    DESCRIPTION:
        Converts an odb box to a glist box. The first line of the odb file that
        is read is expected to contain "BOX".

    KEYWORD ARGUMENTS:
        odb (list of str): the file from which a box object is read.
        lineno (int): the line of odb to start from.

    RETURNS:
        xml.etree.ElementTree.Element: the glist version of the box.

    EXCEPTIONS:
        RuntimeError: if not a valid box object.

    """
    try:
        if "BOX" not in odb[lineno]:
            msg = "At line " + str(lineno) + ",\n" + \
                "Not a BOX primitive.\n" + \
                odb[lineno]
            raise RuntimeError(msg)

        run = True
        primitive = xml.etree.ElementTree.Element("object")
        basegeo = xml.etree.ElementTree.SubElement(primitive, "basegeometry")
        box = xml.etree.ElementTree.SubElement(basegeo, "box")
        while run:
            lineno += 1

            if lineno >= len(odb):
                run = False
            elif len(odb[lineno].strip()) == 0:
                pass
            elif "}" in odb[lineno]:
                run = False
            elif "LOWER_EXTENT" in odb[lineno]:
                lowerextent = xml.etree.ElementTree.SubElement(box, "lowerextent")
                tmp = get_right_of_equals(odb[lineno])
                tmp = tmp.split(",")
                lowerextent.append(xyz2point(tmp[0], tmp[1], tmp[2]))
            elif "UPPER_EXTENT" in odb[lineno]:
                upperextent = xml.etree.ElementTree.SubElement(box, "upperextent")
                tmp = get_right_of_equals(odb[lineno])
                tmp = tmp.split(",")
                upperextent.append(xyz2point(tmp[0], tmp[1], tmp[2]))
            elif "MATERIAL_IDS" in odb[lineno]:
                matid = xml.etree.ElementTree.SubElement(box, "matid")
                matid.text = get_right_of_equals(odb[lineno])
            else:
                msg = "At line " + str(lineno) + ":\n" + \
                    "Unexpected line in BOX primitive\n" + \
                    odb[lineno]
                raise RuntimeError(msg)

        # add a static instance with no parameters!
        staticinstance = xml.etree.ElementTree.SubElement(primitive, \
            "staticinstance")

        return primitive, lineno
    except Exception:
        raise


def odb_cylinder2glist(odb, lineno):
    """ Converts an odb cylinder to a cylinder disk.

    DESCRIPTION:
        Converts an odb cylinder to a glist cylinder. The first line of the odb
        file that is read is expected to contain "CYLINDER".

    KEYWORD ARGUMENTS:
        odb (list of str): the file from which a cylinder object is read.
        lineno (int): the line of odb to start from.

    RETURNS:
        xml.etree.ElementTree.Element: the glist version of the cylinder.

    EXCEPTIONS:
        RuntimeError: if not a valid cylinder object.

    """
    try:
        if "CYLINDER" not in odb[lineno]:
            msg = "At line " + str(lineno) + ",\n" + \
                "Not a CYLINDER primitive.\n" + \
                odb[lineno]
            raise RuntimeError(msg)

        run = True
        primitive = xml.etree.ElementTree.Element("object")
        basegeo = xml.etree.ElementTree.SubElement(primitive, "basegeometry")
        cylinder = xml.etree.ElementTree.SubElement(basegeo, "cylinder")
        while run:
            lineno += 1

            if lineno >= len(odb):
                run = False
            elif len(odb[lineno].strip()) == 0:
                pass
            elif "}" in odb[lineno]:
                run = False
            elif "POINT_A" in odb[lineno]:
                point_a = xml.etree.ElementTree.SubElement(cylinder, "point_a")
                tmp = get_right_of_equals(odb[lineno])
                tmp = tmp.split(",")
                point_a.append(xyz2point(tmp[0], tmp[1], tmp[2]))
            elif "POINT_B" in odb[lineno]:
                point_b = xml.etree.ElementTree.SubElement(cylinder, "point_b")
                tmp = get_right_of_equals(odb[lineno])
                tmp = tmp.split(",")
                point_b.append(xyz2point(tmp[0], tmp[1], tmp[2]))
            elif "MATERIAL_ID" in odb[lineno]:
                matid = xml.etree.ElementTree.SubElement(cylinder, "matid")
                matid.text = get_right_of_equals(odb[lineno])
            elif "RADIUS" in odb[lineno]:
                radius = xml.etree.ElementTree.SubElement(cylinder, "radius")
                radius.text = get_right_of_equals(odb[lineno])
            elif "CAP_A" in odb[lineno]:
                tmp = get_right_of_equals(odb[lineno])
                if tmp.lower() == "true":
                    cylinder.set("cap_a", "true")
                elif tmp.lower() == "false":
                    cylinder.set("cap_a", "false")
                else:
                    msg = "At line " + str(lineno) + ",\n" + \
                        "Unexpect CAP_A option: " + tmp
                    raise RuntimeError(msg)
            elif "CAP_B" in odb[lineno]:
                tmp = get_right_of_equals(odb[lineno])
                if tmp.lower() == "true":
                    cylinder.set("cap_b", "true")
                elif tmp.lower() == "false":
                    cylinder.set("cap_b", "false")
                else:
                    msg = "At line " + str(lineno) + ",\n" + \
                        "Unexpect CAP_B option: " + tmp
                    raise RuntimeError(msg)

            else:
                msg = "At line " + str(lineno) + ",\n" + \
                    "Unexpected line in CYLINDER primitive.\n" + \
                    odb[lineno]
                raise RuntimeError(msg)

        # add a static instance with no parameters!
        staticinstance = xml.etree.ElementTree.SubElement(primitive, "staticinstance")

        return primitive, lineno
    except Exception:
        raise


def odb_curvedfrustum2glist(odb, lineno):
    """ Converts an odb curved frustum to a glist secchi disk.

    DESCRIPTION:
        Converts an odb curved frustum to a glist curved frustum. The first line
        of the odb file that is read is expected to contain "CURVED_FRUSTUM".

    KEYWORD ARGUMENTS:
        odb (list of str): the file from which a curved frustum object is read.
        lineno (int): the line of odb to start from.

    RETURNS:
        xml.etree.ElementTree.Element: the glist version of the curved frustum.

    EXCEPTIONS:
        RuntimeError: if not a valid curved frustum object.

    NOTES:
        Although defined in the odb version of the curved frustum, the ROTATE and
        RAMP parameters are not mentioned in the glist documentation, and not
        implimented. An exception will be thrown if they are included in the odb
        file.

    """
    try:
        if "CURVED_FRUSTUM" not in odb[lineno]:
            msg = "At line " + str(lineno) + ",\n" + \
                "Not a CYLINDER primitive.\n" + \
                odb[lineno]
            raise RuntimeError(msg)


        run = True
        primitive = xml.etree.ElementTree.Element("object")
        basegeo = xml.etree.ElementTree.SubElement(primitive, "basegeometry")
        curvedfrustum = xml.etree.ElementTree.SubElement(basegeo, "curvedfrustum")

        # add bottom and top
        bottom = xml.etree.ElementTree.SubElement(curvedfrustum, "bottom")
        top = xml.etree.ElementTree.SubElement(curvedfrustum, "top")

        # add a static instance

        staticinstance = xml.etree.ElementTree.SubElement(primitive, \
            "staticinstance")

        while run:
            lineno += 1

            if lineno >= len(odb):
                run = False
            elif len(odb[lineno].strip()) == 0:
                pass
            elif "}" in odb[lineno]:
                run = False
            elif "HEIGHT" in odb[lineno]:
                height = xml.etree.ElementTree.SubElement(curvedfrustum, "height")
                height.text = get_right_of_equals(odb[lineno])
            elif "CENTER" in odb[lineno]:
                translation = xml.etree.ElementTree.SubElement(staticinstance, \
                    "translation")
                tmp = get_right_of_equals(odb[lineno])
                tmp = tmp.split(",")
                translation.append(xyz2point(tmp[0], tmp[1], tmp[2]))
            elif "BOTTOM_WIDTH_X" in odb[lineno]:
                xwidth = xml.etree.ElementTree.SubElement(bottom, "xwidth")
                xwidth.text = get_right_of_equals(odb[lineno])
            elif "BOTTOM_WIDTH_Y" in odb[lineno]:
                ywidth = xml.etree.ElementTree.SubElement(bottom, "ywidth")
                ywidth.text = get_right_of_equals(odb[lineno])
            elif "MATERIAL_ID" in odb[lineno]:
                matid = xml.etree.ElementTree.SubElement(curvedfrustum, "matid")
                matid.text = get_right_of_equals(odb[lineno])
            elif "TOP_RADIUS" in odb[lineno]:
                radius = xml.etree.ElementTree.SubElement(top, "radius")
                radius.text = get_right_of_equals(odb[lineno])
            elif "BOTTOM_RADIUS" in odb[lineno]:
                radius = xml.etree.ElementTree.SubElement(bottom, "radius")
                radius.text = get_right_of_equals(odb[lineno])
            elif "ROTATE" in odb[lineno]:
                msg = "At line " + str(lineno) + ",\n" + \
                    "I have no idea how to handle a rotate in a glist file.\n" + \
                    odb[lineno]
                raise RuntimeError(msg)
            elif "RAMP" in odb[lineno]:
                msg = "At line " + str(lineno) + ",\n" + \
                    "I have no idea how to handle a ramp in a glist file.\n" + \
                    odb[lineno]
                raise RuntimeError(msg)
            else:
                msg = "At line " + str(lineno) + ",\n" + \
                    "Unexpected line in CURVED_FRUSTUM primitive.\n" + \
                    odb[lineno]
                raise RuntimeError(msg)
        return primitive, lineno

    except Exception:
        raise


def odb2glist(inputfile, outputfile=None, build_all_instances=False, \
    add_metadata=True):
    """ Converts an odb file to a glist file.

    DESCRIPTION:
        Converts an odb file into the equivalent glist file. This is to facilitate
        make use of the additional features that are available from glist files.

    KEYWORD ARGUMENTS:
        inputfile (str): The filename of the file to read. Include any path
            information as needed.
        outputfile (str, optional), The filename of the file to write. Include any
            path information as needed. If outputfile is None, than the output
            file will be the same as the input odb file, but with a .glist
            extension.
        build_all_instances (bool, optional): A flag to tell the converter to
            fully defined static instance. The default is False. If false, the
            minimum static instance will be used. This is only applied to objects
            and not primatives.
        add_metadata (bool, optional): A flag to tell the converter to add a
            comment to the output glist file. The comment contains the filename
            (with absolute path) of the input file, a time stamp for when the
            conversion took place, and that odb2glist.py was used. This is to help
            track down any discrepancy in the two files.

    RETURNS:
        bool: True if the file was successfully converted.

    OUTPUTS:
        A glist file (name dependent on the value of outputfile) will be written.

    """

    try:
        # set the output filename if it is not set
        if not outputfile:
            tmp = os.path.splitext(inputfile)
            outputfile = tmp[0] + ".glist"

        # read the odb
        fid = open(inputfile, "r")
        odb = [tmp for tmp in fid.readlines()]
        fid.close()

        # remove newlines and spaces
        odb = [tmp.strip() for tmp in odb]

        # Make sure that "DIRSIG_ODB" is in the first line of the file
        if "DIRSIG_ODB" not in odb[0]:
            # todo: use exceptions
            msg = "At line 1 in %s: The file is not a valid odb file" % \
                inputfile
            raise RuntimeError(msg)

        geomtetrylist = xml.etree.ElementTree.Element("geometrylist")
        geomtetrylist.set("enabled", "true")

        if add_metadata:
            # Add a comment to the glist about where and when the file was
            # converted. This is to help track down original files incase bugs
            # come up. We are using abspath to help disambiguate files.
            cmt = "Converted from: " + os.path.abspath(inputfile) + " at " + \
                datetime.datetime.now().isoformat() + " by odb2glist.py"
            comment = xml.etree.ElementTree.Comment(cmt)
            geomtetrylist.append(comment)

        i = 1
        # loop through each line of the file
        while i < len(odb):
            if len(odb[i].strip()) == 0:
                # ignore empty lines!
                pass

            elif "#" in odb[i]:
                # we are a comment.
                tmp = odb[i]
                comment = xml.etree.ElementTree.Comment(text=(tmp[1:]).strip())
                geomtetrylist.append(comment)

            elif "OBJECT" in odb[i]:
                obj, i = odb_object2glist(odb, i, \
                    build_all_instances=build_all_instances)
                geomtetrylist.append(obj)

            # we are a sphere primitive
            elif "SPHERE" in odb[i]:
                obj, i = odb_sphere2glist(odb, i)
                geomtetrylist.append(obj)

            # we are a ground plane primitive
            elif "GROUND_PLANE" in odb[i]:
                obj, i = odb_groundplane2glist(odb, i)
                geomtetrylist.append(obj)

            # we are a Secchi disk primitive
            elif "SECCHI_DISK" in odb[i]:
                obj, i = odb_secchidisk2glist(odb, i)
                geomtetrylist.append(obj)

            # we are a disk primitive
            elif "DISK" in odb[i]:
                obj, i = odb_disk2glist(odb, i)
                geomtetrylist.append(obj)

            # we are a box primitive
            elif "BOX" in odb[i]:
                obj, i = odb_box2glist(odb, i)
                geomtetrylist.append(obj)

            # we are a cylinder primitive
            elif "CYLINDER" in odb[i]:
                obj, i = odb_cylinder2glist(odb, i)
                geomtetrylist.append(obj)

            # we are a curved frustum primitive
            elif "CURVED_FRUSTUM" in odb[i]:
                obj, i = odb_curvedfrustum2glist(odb, i)
                geomtetrylist.append(obj)

            else:
                msg = "At line " + str(i) + ",\n" + \
                    "'" + (odb[i]).strip() + "' is an unsupported odb option.\n"
                raise RuntimeError(msg)

            # read the next line
            i += 1

        # write the glist file
        fid = open(outputfile, "w")
        # use prettify to make more human-readable xml
        fid.write(prettify(geomtetrylist))
        fid.close()

        return True
    except Exception, exception:
        raise RuntimeError('In ' + inputfile + \
            ':\n' + exception.message)



if __name__ == "__main__":
    # set defaults
    INPUTFILE = ''
    OUTPUTFILE = ''
    BUILD_ALL_INSTANCES = False

    # get the command line input
    ARGS = sys.argv

    if "odb2glist.py" in ARGS[0]:
        ARGS.pop(0)

    # todo: use exceptions
    if not ARGS:
        MSG = "No inputs from odb2glist.\n" + \
            "Usage: odb2glist.py [options] filename.odb\n"
        sys.exit(MSG)

    # get the inputfile name (always last argument)
    # TODO: make this work if the user has spaces in the filename.
    INPUTFILE = ARGS[-1]

    # make sure the file exists
    if not os.path.isfile(INPUTFILE):
        sys.exit("'" + INPUTFILE + "' is not a file.")

    I = 0
    while I <= (len(ARGS) - 2):
        # future options here
        if ARGS[I] == '-o':
            OUTPUTFILE = ARGS[I+1]
            I += 2
        elif ARGS[I] == '-f':
            BUILD_ALL_INSTANCES = True
            I += 1
        else:
            sys.exit("'" + str(ARGS[I]) + "' is not a valid option.")

    # set the output filename if it is not set
    if not OUTPUTFILE:
        TMP = os.path.splitext(INPUTFILE)
        OUTPUTFILE = TMP[0] + ".glist"

    STATUS = odb2glist(INPUTFILE, outputfile=OUTPUTFILE, \
        build_all_instances=BUILD_ALL_INSTANCES)
