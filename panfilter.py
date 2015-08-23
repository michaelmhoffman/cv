#!/usr/bin/env python
"""panfilter.py: filter out parts of a pandoc document
"""

from __future__ import absolute_import, division, print_function
from future_builtins import ascii, filter, hex, map, oct, zip

__version__ = "0.1"

## Copyright 2015 Michael M. Hoffman <michael.hoffman@utoronto.ca>

from datetime import date
import json
import re
import sys

import yaml

YEAR = date.today().year

re_year = re.compile(r"19\d\d|20\d\d|present")

def text_to_year(text):
    if text == "present":
        return YEAR
    else:
        return int(text)

def panfilter(infile, config_file):
    pandoc_in = json.load(infile)
    metadata, tree = pandoc_in

    assert isinstance(metadata, dict)
    assert isinstance(tree, list)

    config_raw = yaml.load(config_file)
    config = dict((item["id"], dict(subitem for subitem in item.items()
                                    if subitem[0] != "id"))
                  for item in config_raw)

    include_ids = frozenset(section["id"] for section in config_raw)

    section_id = None
    section_accept = True
    para_accept = True
    section_year_min = None
    res = []

    for node in tree:
        node_type = node["t"]
        node_content= node["c"]

        if node_type == "Header":
            section_id = node_content[1][0]
            section_accept = section_id in include_ids
            section_config = config.get(section_id)
            para_accept = True
            if section_config is not None:
                section_name = section_config.get("name")
                if section_name:
                    node_content[2] = [{"c": section_name, "t": "Str"}]

                section_exclude = frozenset(section_config.get("exclude", []))

                section_year_min = section_config.get("year-min")
                if section_year_min is not None and section_year_min < 0:
                    section_year_min = YEAR + section_year_min

        if not section_accept:
            continue

        if section_year_min is not None and node_type == "Para":
            if node_content[0]["c"].rstrip(".") in section_exclude:
                para_accept = False
                continue

            for subnode in node_content:
                if subnode["t"] == "Str":
                    node_years = [text_to_year(match.group(0))
                                  for match in re_year.finditer(subnode["c"])]
                    if node_years and max(node_years) < section_year_min:
                        para_accept = False
                        break
            else:
                para_accept = True

        if not para_accept:
            continue

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
    parser.add_argument("--config", type=FileType("r"),
                        metavar="FILE", help="file with YAML configuration")

    version = "%(prog)s {}".format(__version__)
    parser.add_argument("--version", action="version", version=version)

    return parser.parse_args(args)

def main(argv=sys.argv[1:]):
    args = parse_args(argv)

    return panfilter(args.infile, args.config)

if __name__ == "__main__":
    sys.exit(main())
