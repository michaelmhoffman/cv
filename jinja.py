#!/usr/bin/env python
"""jinja: basic jinja templating
"""

from __future__ import absolute_import, division, print_function
from future_builtins import ascii, filter, hex, map, oct, zip

__version__ = "$Revision: 871 $"

## Copyright 2011, 2015 Michael M. Hoffman <mmh1@uw.edu>

import codecs
import sys

from jinja2 import Environment, FileSystemLoader

def jinja(infile, outfilename):
    env = Environment(loader=FileSystemLoader([".", "../cv-private"]))
    template = env.get_template(infile)

    with codecs.open(outfilename, "w", "utf-8") as outfile:
        print(template.render(), file=outfile)

def parse_args(args):
    from argparse import (ArgumentDefaultsHelpFormatter, ArgumentParser,
                          FileType)

    description = __doc__.splitlines()[0].partition(": ")[2]
    parser = ArgumentParser(description=description,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("infile", metavar="INFILE",
                        help="input Jinja template")
    parser.add_argument("outfile", nargs="?", metavar="OUTFILE",
                        help="output file")

    version = "%(prog)s {}".format(__version__)
    parser.add_argument("--version", action="version", version=version)

    return parser.parse_args(args)

def main(argv=sys.argv[1:]):
    args = parse_args(argv)

    return jinja(args.infile, args.outfile)

if __name__ == "__main__":
    sys.exit(main())
