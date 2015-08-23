#!/usr/bin/env python
"""panfilter.py: filter out parts of a pandoc document
"""

from __future__ import absolute_import, division, print_function
from future_builtins import ascii, filter, hex, map, oct, zip

__version__ = "0.1"

## Copyright 2015 Michael M. Hoffman <michael.hoffman@utoronto.ca>

import json
import sys

def panfilter(infile, include_file):
    pandoc_in = json.load(infile)
    metadata, tree = pandoc_in

    assert isinstance(metadata, dict)
    assert isinstance(tree, list)

    include_ids = frozenset(line.strip() for line in include_file)

    accept = True
    res = []

    for node in tree:
        if node["t"] == "Header":
            accept = node["c"][1][0] in include_ids

        if accept:
            res.append(node)

    pandoc_out = metadata, res
    json.dump(pandoc_out, sys.stdout)

    # XXX: print heading options
    # print(*(node["c"][1][0] for node in tree
    #         if node["t"] == "Header"), sep="\n")

def parse_args(args):
    from argparse import (ArgumentDefaultsHelpFormatter, ArgumentParser,
                          FileType)

    description = __doc__.splitlines()[0].partition(": ")[2]
    parser = ArgumentParser(description=description,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("infile", nargs="?", type=FileType("r"),
                        default=sys.stdin, metavar="FILE",
                        help="input file in Pandoc JSON format")
    parser.add_argument("--include-from", type=FileType("r"),
                        dest="include_file", metavar="FILE",
                        help="file of list of heading IDs to include, "
                        "newline-delimited")

    version = "%(prog)s {}".format(__version__)
    parser.add_argument("--version", action="version", version=version)

    return parser.parse_args(args)

def main(argv=sys.argv[1:]):
    args = parse_args(argv)

    return panfilter(args.infile, args.include_file)

if __name__ == "__main__":
    sys.exit(main())
