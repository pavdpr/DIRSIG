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

    TODO:
    - Use exceptions for error handling.
    - Allow for the user to choose the output filename.
    - Add the ability to fully define an instance.
        + default is to only populate the non-standard items.
    - Add recursive functionality to convert any sub-odb files to glists.
    - Split components off into separate functions.

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
import os                          # for interacting with files and directories
import re                          # for parsing strings
import sys                         # for getting command-line input
import xml.etree.ElementTree as ET # for xml parsing
import xml.dom.minidom             # for pretty print xml


def prettify(elem, indent="  "):
    """ Returns a pretty-printed XML string.

    DESCRIPTION:
        Returns a pretty-printed (human-readable) string of the element.

    KEYWORD ARGUMENTS:
        elem (xml.etree.Element): the element (and any children of it) to
            convert.
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

    rough_string = ET.tostring(elem, "utf-8")
    reparsed = xml.dom.minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent=indent)



def get_right_of_equals(line):
    """ Returns the text to the right of an equals.

    DESCRIPTION:

    KEYWORD ARGUMENTS:

    RETURNS:

    NOTES:

    TODO:

    REFERENCES:

    """
    tmpline = line.split("=")
    tmpline = tmpline[-1]
    tmpline = tmpline.strip()
    return tmpline


def odb2glist(inputfile, outputfile=None, build_all_instances=False):
    """ Converts an odb file to a glist file.

    DESCRIPTION:

    KEYWORD ARGUMENTS:

    RETURNS:

    NOTES:

    TODO:

    REFERENCES:

    """
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
        print "At line", 1, " in ", inputfile, ":"
        print "The file is not a valid odb file"
        return False

    geomtetrylist = ET.Element("geometrylist")
    geomtetrylist.set("enabled", "true")

    i = 1
    # loop through each line of the file
    while i < len(odb):
        if len(odb[i]) == 0:
            # ignore empty lines!
            pass

        elif "#" in odb[i]:
            # we are a comment.
            tmp = odb[i]
            comment = ET.Comment(text=(tmp[1:]).strip())
            geomtetrylist.append(comment)

        elif "OBJECT" in odb[i]:
            # we are an object

            # set up the xml to handle an object
            obj = ET.SubElement(geomtetrylist, "object")
            basegeo = ET.SubElement(obj, "basegeometry")
            units = None

            run1 = True
            while run1:

                i += 1

                # Should not need this case, probably should remove
                if i >= len(odb):
                    run1 = False

                # Skip any empty lines
                elif len(odb[i]) == 0:
                    pass

                # stop running if the closing bracket is found
                elif "}" in odb[i]:
                    run1 = False

                # we have a comment
                elif "#" in odb[i]:
                    # assume we are a comment
                    tmp = odb[i]
                    comment = ET.Comment(text=(tmp[1:]).strip())
                    basegeo.append(comment)

                # We are including some type of file.
                elif "_FILENAME" in odb[i]:
                    # We want either a gdb, obj, or odb file
                    if "GDB_FILENAME" in odb[i]:
                        geotype = ET.SubElement(basegeo, "gdb")
                    elif "OBJ_FILENAME" in odb[i]:
                        geotype = ET.SubElement(basegeo, "obj")
                    elif "ODB_FILENAME" in odb[i]:
                        geotype = ET.SubElement(basegeo, "odb")
                    else:
                        # some other type of file.
                        print "at line", i + 1, " in ", inputfile, ":"
                        print "unsupported geometry type"
                        return False

                    # add the filename
                    filename = ET.SubElement(geotype, "filename")
                    filename.text = get_right_of_equals(odb[i])

                # Add units
                elif "UNITS" in odb[i]:
                    if "CENTIMETERS" in odb[i]:
                        # this needs to come before meters since meters is in
                        # centimeters
                        units = "centimeters"
                    elif "METERS" in odb[i]:
                        units = "meters"
                        # consider using pass here since the default is meters
                    elif "FEET" in odb[i]:
                        units = "feet"
                    elif "INCHES" in odb[i]:
                        units = "inches"
                    else:
                        print "at line", i + 1, " in ", inputfile, ":"
                        print "unsupported units"
                        return False

                # we have found a set of instances
                elif "INSTANCES" in odb[i]:
                    # Make sure that the filename has been set.
                    if not isValidObject:
                        print "at line", i + 1, " in ", inputfile, ":"
                        print "We have not defined a file yet, how can we have instances?"
                        return False

                    # get the instance(s)
                    run2 = True
                    while run2:
                        i += 1

                        # ignore empty lines
                        if len(odb[i]) == 0:
                            pass

                        # stop running
                        elif "}" in odb[i]:
                            run2 = False

                        # we found a comment
                        elif "#" in odb[i]:
                            tmp = odb[i]
                            comment = ET.Comment(text=(tmp[1:]).strip())
                            obj.append(comment)

                        # Some line I don't know how to handle
                        elif "INFO" not in odb[i]:
                            print "at line", i + 1, " in ", inputfile, ":"
                            print "there should be an INFO here"
                            print odb[i]
                            return False

                        # We have found an info
                        else:
                            line = get_right_of_equals(odb[i])

                            # a dynamic instance controlled by a mov file
                            if ".mov" in line:
                                # we are a dynamic instance
                                # Do I need to worry about ppd files? or is that a glist feature?

                                di = ET.SubElement(obj, "dynamicinstance")
                                kfm = ET.SubElement(di, "keyframemovement")
                                filename = ET.SubElement(kfm, "filename")
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
                                    si = ET.SubElement(obj, "staticinstance")

                                    if (float(line[0]) != 0.0) or \
                                    (float(line[1]) != 0.0) or \
                                    (float(line[2]) != 0.0) or \
                                    build_all_instances:

                                        # make a translation
                                        translation = ET.SubElement(si, "translation")
                                        point = ET.SubElement(translation, "point")
                                        x = ET.SubElement(point, "x")
                                        x.text = (line[0]).strip()
                                        y = ET.SubElement(point, "y")
                                        y.text = (line[1]).strip()
                                        z = ET.SubElement(point, "z")
                                        z.text = (line[2]).strip()

                                    if (float(line[3]) == 0.0) or \
                                        (float(line[4]) == 0.0) or \
                                        (float(line[5]) == 0.0):
                                        print "at line", i + 1, " in ", inputfile, ":"
                                        print "glist files only support non-zero scales"
                                        return False

                                    elif (float(line[3]) != 1.0) or \
                                        (float(line[4]) != 1.0) or \
                                        (float(line[5]) != 1.0) or \
                                        build_all_instances:

                                        # make a scale
                                        scale = ET.SubElement(si, "scale")
                                        ct = ET.SubElement(scale, "cartesiantriple")
                                        x = ET.SubElement(ct, "x")
                                        x.text = (line[3]).strip()
                                        y = ET.SubElement(ct, "y")
                                        y.text = (line[4]).strip()
                                        z = ET.SubElement(ct, "z")
                                        z.text = (line[5]).strip()

                                    if (float(line[6]) != 0.0) or \
                                    (float(line[7]) != 0.0) or \
                                    (float(line[8]) != 0.0) or \
                                    build_all_instances:

                                        # make a rotation
                                        rotation = ET.SubElement(si, "rotation")
                                        ct = ET.SubElement(rotation, "cartesiantriple")
                                        x = ET.SubElement(ct, "x")
                                        x.text = (line[6]).strip()
                                        y = ET.SubElement(ct, "y")
                                        y.text = (line[7]).strip()
                                        z = ET.SubElement(ct, "z")
                                        z.text = (line[8]).strip()
                                elif len(line) == 16:
                                    # we are a 16-ple

                                    # make a static instance
                                    si = ET.SubElement(obj, "staticinstance")

                                    # make a matrix
                                    matrix = ET.SubElement(si, "matrix")
                                    matrix.text = ", ".join(line)
                                else:
                                    print "at line", i + 1, " in ", inputfile, ":"
                                    print "I am not sure how to parse the line:"
                                    print ",".join(line)
                                    print "I was expecting either 9 or 16 comma separated values"
                                    return False

                            else:
                                # assume 4x4 affine matrix, split by white space
                                # can I have a space separated 9-ple here?
                                l = re.compile(r"\s+")
                                tmp = l.split(line)
                                if len(tmp) != 16:
                                    # we expect 16 elements in this line
                                    print "at line", i + 1, " in ", inputfile, ":"
                                    print "I do not understand the instance info:"
                                    print " ".join(tmp)
                                    print "I was expecting 16 numbers separated by spaces"
                                    return False

                                # convert to xml (requires values be comma separated)
                                # make a static instance
                                si = ET.SubElement(obj, "staticinstance")
                                matrix = ET.SubElement(si, "matrix")
                                matrix.text = ", ".join(tmp)

                # Add the units to the geotype.
                # This was moved to allow for units to appear before the filename.
                if units:
                    geotype.set("units", units)

        # we are a sphere primitive
        elif "SPHERE" in odb[i]:
            run2 = True
            obj = ET.SubElement(geomtetrylist, "object")
            basegeo = ET.SubElement(obj, "basegeometry")
            sphere = ET.SubElement(basegeo, "sphere")
            while run2:
                i += 1

                if i >= len(odb):
                    run2 = False
                elif len(odb[i]) == 0:
                    pass
                elif "}" in odb[i]:
                    run2 = False
                elif "RADIUS" in odb[i]:
                    radius = ET.SubElement(sphere, "radius")
                    radius.text = get_right_of_equals(odb[i])
                elif "CENTER" in odb[i]:
                    center = ET.SubElement(sphere, "center")
                    point = ET.SubElement(center, "point")
                    tmp = get_right_of_equals(odb[i])
                    tmp = tmp.split(",")
                    x = ET.SubElement(point, "x")
                    x.text = (tmp[0]).strip()
                    y = ET.SubElement(point, "y")
                    y.text = (tmp[1]).strip()
                    z = ET.SubElement(point, "z")
                    z.text = (tmp[2]).strip()
                elif "MATERIAL_IDS" in odb[i]:
                    matid = ET.SubElement(sphere, "matid")
                    matid.text = get_right_of_equals(odb[i])
                else:
                    print "at line", i + 1, " in ", inputfile, ":"
                    print "Unexpected line in SPHERE primitive"
                    print odb[i]
                    return False

            # add a static instance with no parameters!

            si = ET.SubElement(obj, "staticinstance")

        # we are a ground plane primitive
        elif "GROUND_PLANE" in odb[i]:
            run2 = True
            obj = ET.SubElement(geomtetrylist, "object")
            basegeo = ET.SubElement(obj, "basegeometry")
            groundplane = ET.SubElement(basegeo, "groundplane")
            while run2:
                i += 1

                if i >= len(odb):
                    run2 = False
                elif len(odb[i]) == 0:
                    pass
                elif "}" in odb[i]:
                    run2 = False
                elif "ANCHOR" in odb[i]:
                    anchor = ET.SubElement(groundplane, "anchor")
                    point = ET.SubElement(anchor, "point")
                    tmp = get_right_of_equals(odb[i])
                    tmp = tmp.split(",")
                    x = ET.SubElement(point, "x")
                    x.text = (tmp[0]).strip()
                    y = ET.SubElement(point, "y")
                    y.text = (tmp[1]).strip()
                    z = ET.SubElement(point, "z")
                    z.text = (tmp[2]).strip()
                elif "MATERIAL_ID" in odb[i]:
                    matid = ET.SubElement(groundplane, "matid")
                    matid.text = get_right_of_equals(odb[i])
                elif "ADD_CHECKS" in odb[i]:
                    run3 = True
                    while run3:
                        i += 1
                        checkers = ET.SubElement(groundplane, "checkers")
                        if i >= len(odb):
                            run3 = False
                        elif len(odb[i]) == 0:
                            pass
                        elif "}" in odb[i]:
                            run3 = False
                        elif "MATERIAL_ID" in odb[i]:
                            checkers.set("matid", get_right_of_equals(odb[i]))
                        elif "WIDTH" in odb[i]:
                            checkers.set("width", get_right_of_equals(odb[i]))
                        else:
                            print "at line", i + 1, " in ", \
                                inputfile, ":"
                            print "I do not know what to do with this line in " + \
                                "GROUND_PLANE:ADD_CHECKS"
                            print odb[i]

                else:
                    print "Unexpected line in GROUND_PLANE primitive"
                    print odb[i]
                    return False

            # add a static instance with no parameters!

            si = ET.SubElement(obj, "staticinstance")

        # we are a Secchi disk primitive
        elif "SECCHI_DISK" in odb[i]:
            # SECCHI_DISK mush appear before DISK to make this work!
            run2 = True
            obj = ET.SubElement(geomtetrylist, "object")
            basegeo = ET.SubElement(obj, "basegeometry")
            secchidisk = ET.SubElement(basegeo, "secchidisk")

            # secchidisk locations are in the static instance part of the glist!
            si = ET.SubElement(obj, "staticinstance")

            while run2:
                i += 1

                if i >= len(odb):
                    run2 = False
                elif len(odb[i]) == 0:
                    pass
                elif "}" in odb[i]:
                    run2 = False
                elif "RADIUS" in odb[i]:
                    radius = ET.SubElement(secchidisk, "radius")
                    radius.text = get_right_of_equals(odb[i])
                elif "CENTER" in odb[i]:
                    translation = ET.SubElement(si, "translation")
                    point = ET.SubElement(translation, "point")
                    tmp = get_right_of_equals(odb[i])
                    tmp = tmp.split(",")
                    x = ET.SubElement(point, "x")
                    x.text = (tmp[0]).strip()
                    y = ET.SubElement(point, "y")
                    y.text = (tmp[1]).strip()
                    z = ET.SubElement(point, "z")
                    z.text = (tmp[2]).strip()
                elif "MATERIAL_IDS" in odb[i]:
                    matid_a = ET.SubElement(secchidisk, "matid_a")
                    matid_b = ET.SubElement(secchidisk, "matid_b")
                    tmp = (get_right_of_equals(odb[i])).split(",")
                    matid_a.text = (tmp[0]).strip()
                    matid_b.text = (tmp[1]).strip()
                else:
                    print "at line", i + 1, " in ", \
                        inputfile, ":"
                    print "Unexpected line in DISK primitive"
                    print odb[i]
                    return False

        # we are a disk primitive
        elif "DISK" in odb[i]:
            run2 = True
            obj = ET.SubElement(geomtetrylist, "object")
            basegeo = ET.SubElement(obj, "basegeometry")
            disk = ET.SubElement(basegeo, "disk")

            # disk locations are in the static instance part of the glist!
            si = ET.SubElement(obj, "staticinstance")

            while run2:
                i += 1

                if i >= len(odb):
                    run2 = False
                elif len(odb[i]) == 0:
                    pass
                elif "}" in odb[i]:
                    run2 = False
                elif "RADIUS" in odb[i]:
                    radius = ET.SubElement(disk, "radius")
                    radius.text = get_right_of_equals(odb[i])
                elif "CENTER" in odb[i]:
                    translation = ET.SubElement(si, "translation")
                    point = ET.SubElement(translation, "point")
                    tmp = get_right_of_equals(odb[i])
                    tmp = tmp.split(",")
                    x = ET.SubElement(point, "x")
                    x.text = (tmp[0]).strip()
                    y = ET.SubElement(point, "y")
                    y.text = (tmp[1]).strip()
                    z = ET.SubElement(point, "z")
                    z.text = (tmp[2]).strip()
                elif "MATERIAL_ID" in odb[i]:
                    matid = ET.SubElement(disk, "matid")
                    matid.text = get_right_of_equals(odb[i])
                else:
                    print "at line", i + 1, " in ", \
                        inputfile, ":"
                    print "Unexpected line in DISK primitive"
                    print odb[i]
                    return False

        # we are a box primitive
        elif "BOX" in odb[i]:
            run2 = True
            obj = ET.SubElement(geomtetrylist, "object")
            basegeo = ET.SubElement(obj, "basegeometry")
            box = ET.SubElement(basegeo, "box")
            while run2:
                i += 1

                if i >= len(odb):
                    run2 = False
                elif len(odb[i]) == 0:
                    pass
                elif "}" in odb[i]:
                    run2 = False
                elif "LOWER_EXTENT" in odb[i]:
                    lowerextent = ET.SubElement(box, "lowerextent")
                    point = ET.SubElement(lowerextent, "point")
                    tmp = (get_right_of_equals(odb[i])).split(",")
                    x = ET.SubElement(point, "x")
                    x.text = (tmp[0]).strip()
                    y = ET.SubElement(point, "y")
                    y.text = (tmp[1]).strip()
                    z = ET.SubElement(point, "z")
                    z.text = (tmp[2]).strip()
                elif "UPPER_EXTENT" in odb[i]:
                    upperextent = ET.SubElement(box, "upperextent")
                    point = ET.SubElement(upperextent, "point")
                    tmp = (get_right_of_equals(odb[i])).split(",")
                    x = ET.SubElement(point, "x")
                    x.text = (tmp[0]).strip()
                    y = ET.SubElement(point, "y")
                    y.text = (tmp[1]).strip()
                    z = ET.SubElement(point, "z")
                    z.text = (tmp[2]).strip()
                elif "MATERIAL_IDS" in odb[i]:
                    matid = ET.SubElement(box, "matid")
                    matid.text = get_right_of_equals(odb[i])
                else:
                    print "at line", i + 1, " in ", \
                        inputfile, ":"
                    print "Unexpected line in BOX primitive"
                    print odb[i]
                    return False

            # add a static instance with no parameters!

            si = ET.SubElement(obj, "staticinstance")

        # we are a cylinder primitive
        elif "CYLINDER" in odb[i]:
            run2 = True
            obj = ET.SubElement(geomtetrylist, "object")
            basegeo = ET.SubElement(obj, "basegeometry")
            cylinder = ET.SubElement(basegeo, "cylinder")
            while run2:
                i += 1

                if i >= len(odb):
                    run2 = False
                elif len(odb[i]) == 0:
                    pass
                elif "}" in odb[i]:
                    run2 = False
                elif "POINT_A" in odb[i]:
                    point_a = ET.SubElement(cylinder, "point_a")
                    point = ET.SubElement(point_a, "point")
                    tmp = (get_right_of_equals(odb[i])).split(",")
                    x = ET.SubElement(point, "x")
                    x.text = (tmp[0]).strip()
                    y = ET.SubElement(point, "y")
                    y.text = (tmp[1]).strip()
                    z = ET.SubElement(point, "z")
                    z.text = (tmp[2]).strip()
                elif "POINT_B" in odb[i]:
                    point_b = ET.SubElement(cylinder, "point_b")
                    point = ET.SubElement(point_b, "point")
                    tmp = (get_right_of_equals(odb[i])).split(",")
                    x = ET.SubElement(point, "x")
                    x.text = (tmp[0]).strip()
                    y = ET.SubElement(point, "y")
                    y.text = (tmp[1]).strip()
                    z = ET.SubElement(point, "z")
                    z.text = (tmp[2]).strip()
                elif "MATERIAL_ID" in odb[i]:
                    matid = ET.SubElement(cylinder, "matid")
                    matid.text = get_right_of_equals(odb[i])
                elif "RADIUS" in odb[i]:
                    radius = ET.SubElement(cylinder, "radius")
                    radius.text = get_right_of_equals(odb[i])
                elif "CAP_A" in odb[i]:
                    tmp = get_right_of_equals(odb[i])
                    if tmp.lower() == "true":
                        cylinder.set("cap_a", "true")
                    elif tmp.lower() == "false":

                        cylinder.set("cap_a", "false")
                    else:
                        print "Unexpect CAP_A option: " + tmp
                elif "CAP_B" in odb[i]:
                    tmp = get_right_of_equals(odb[i])
                    if tmp.lower() == "true":
                        cylinder.set("cap_b", "true")
                    elif tmp.lower() == "false":

                        cylinder.set("cap_b", "false")
                    else:
                        print "Unexpect CAP_A option: " + tmp

                else:
                    print "at line", i + 1, " in ", \
                        inputfile, ":"
                    print "Unexpected line in CYLINDER primitive"
                    print odb[i]
                    return False

            # add a static instance with no parameters!

            si = ET.SubElement(obj, "staticinstance")

        # we are a curved frustum primitive
        elif "CURVED_FRUSTUM" in odb[i]:
            run2 = True
            obj = ET.SubElement(geomtetrylist, "object")
            basegeo = ET.SubElement(obj, "basegeometry")
            curvedfrustum = ET.SubElement(basegeo, "curvedfrustum")

            # add bottom and top
            bottom = ET.SubElement(curvedfrustum, "bottom")
            top = ET.SubElement(curvedfrustum, "top")

            # add a static instance

            si = ET.SubElement(obj, "staticinstance")

            while run2:
                i += 1

                if i >= len(odb):
                    run2 = False
                elif len(odb[i]) == 0:
                    pass
                elif "}" in odb[i]:
                    run2 = False
                elif "HEIGHT" in odb[i]:
                    height = ET.SubElement(curvedfrustum, "height")
                    height.text = get_right_of_equals(odb[i])
                elif "CENTER" in odb[i]:
                    translation = ET.SubElement(si, "translation")
                    point = ET.SubElement(translation, "point")
                    tmp = get_right_of_equals(odb[i])
                    tmp = tmp.split(",")
                    x = ET.SubElement(point, "x")
                    x.text = (tmp[0]).strip()
                    y = ET.SubElement(point, "y")
                    y.text = (tmp[1]).strip()
                    z = ET.SubElement(point, "z")
                    z.text = (tmp[2]).strip()
                elif "BOTTOM_WIDTH_X" in odb[i]:
                    xwidth = ET.SubElement(bottom, "xwidth")
                    xwidth.text = get_right_of_equals(odb[i])
                elif "BOTTOM_WIDTH_Y" in odb[i]:
                    ywidth = ET.SubElement(bottom, "ywidth")
                    ywidth.text = get_right_of_equals(odb[i])
                elif "MATERIAL_ID" in odb[i]:
                    matid = ET.SubElement(curvedfrustum, "matid")
                    matid.text = get_right_of_equals(odb[i])
                elif "TOP_RADIUS" in odb[i]:
                    radius = ET.SubElement(top, "radius")
                    radius.text = get_right_of_equals(odb[i])
                elif "BOTTOM_RADIUS" in odb[i]:
                    radius = ET.SubElement(bottom, "radius")
                    radius.text = get_right_of_equals(odb[i])
                elif "ROTATE" in odb[i]:
                    print "at line", i + 1, " in ", \
                        inputfile, ":"
                    print "I have no idea how to handle a rotate in a glist file"
                elif "RAMP" in odb[i]:
                    print "at line", i + 1, " in ", \
                        inputfile, ":"
                    print "I have no idea how to handle a ramp in a glist file"

                else:
                    print "at line", i + 1, " in ", \
                        inputfile, ":"
                    print "Unexpected line in CURVED_FRUSTUM primitive"
                    print odb[i]
                    return False

        else:
            print "at line", i + 1, " in ", inputfile, ":"
            print "'" + (odb[i]).strip() + "' is an unsupported odb option"
            return False

        # read the next line
        i += 1

    # write the glist file
    fid = open(outputfile, "w")
    # use prettify to make more human-readable xml
    fid.write(prettify(geomtetrylist))
    fid.close()

    return True



if __name__ == "__main__":
    # set defaults
    inputfile = ''
    outputfile = ''
    build_all_instances = False

    # get the command line input
    args = sys.argv

    if "odb2glist.py" in args[0]:
        args.pop(0)

    # todo: use exceptions
    if not args:
        msg = "No inputs from odb2glist.\n" + \
            "Usage: odb2glist.py [options] filename.odb\n"
        sys.exit(msg)

    # get the inputfile name (always last argument)
    # TODO: make this work if the user has spaces in the filename.
    tmp = args[-1]

    # make sure the file exists
    if not os.path.isfile(tmp):
        sys.exit("'" + tmp + "' is not a file.")
    inputfile = tmp

    # read any optional arguments
    # TODO: Actually do this!
    i = 0
    while i <= (len(args) - 2):
        # future options here
        if args[i] == "":
            pass
        else:
            sys.exit("The option '" + args[i] + "' is not defined")
        i += 1

    # set the output filename if it is not set
    if not outputfile:
        tmp = os.path.splitext(inputfile)
        outputfile = tmp[0] + ".glist"

    status = odb2glist(inputfile, outputfile=outputfile, \
        build_all_instances=build_all_instances)
