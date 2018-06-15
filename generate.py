#
# Gather text files and put them into a python dictionary.
# To keep things simple, we assume the text files do not
# contain python triple quotes.
#
from __future__ import print_function
import sys
import os
import argparse

parser = argparse.ArgumentParser(description='Generate resource file.')
parser.add_argument('-q','--quiet', action='store_true')
parser.add_argument('-o','--output', type=argparse.FileType('w'), default=sys.stdout)
parser.add_argument('input', nargs='*', type=argparse.FileType('r'), default=[sys.stdin])
args = parser.parse_args()

args.output.write('# This is a generated file. Do not edit.\n\n')
args.output.write('resources = {\n')
for resource in args.input:
    if not args.quiet:
        print("Writing '{0}' to '{1}'.".format(resource.name, args.output.name))
    name = os.path.basename(resource.name)
    args.output.write('    "{0}":\\\n"""\\\n{1}""",\n\n\n'.format(name, resource.read()))
args.output.write('}\n')
