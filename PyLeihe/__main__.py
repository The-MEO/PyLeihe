"""
Command line interface for the execution of the module in the terminal.

Help is displayed with the `-h` parameter:
    ```
    python3 -m PyLeihe -h
    ```
"""
import sys
import subprocess
import argparse
from . import PyLeiheNet, MediaType
from .simple_functions import *


def run_console(cmd):
    print('[  ] ', end='')
    print(' '.join(cmd), end='', flush=True)
    pdoc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    pdoc_pipe = pdoc.communicate(timeout=15)
    if pdoc.returncode == 1:
        print("\r[!!]")
        print()
        print(pdoc_pipe[0])
        print(pdoc_pipe[1])
    else:
        print("\r[OK]")
    return pdoc.returncode

def parseargs(args):
    """
    Defines and parses the arguments.
    """
    parser = argparse.ArgumentParser(description='Python search for the german online libraries - created by MEO')
    parser.add_argument('--loadonline', help='loads all neccessary data from the web', action='store_true')
    parser.add_argument('--makejson', help='group and correct and finally saves the data to a json file', action='store_true')
    parser.add_argument('-j', '--jsonfile', help="Path to the jsonfile", default="")
    parser.add_argument('-s', '--search', help="Search for keywords in all bibs")
    parser.add_argument('-c', '--category', help="Media category", type=lambda t: MediaType[t], choices=list(MediaType), default=MediaType.alleMedien)
    parser.add_argument('-t', '--top', help="Number of print results", type=int, default=-1)
    parser.add_argument('--threads', help="Number of used parallel threads", type=int, default=4)
    parser.add_argument('--csv', help="stores result in csv", action='store_true')
    parser.add_argument('--make', help="[only for Developer] do some build tasks", action='store_true')
    parser.add_argument('--test', help="[only for Developer] do some test tasks", action='store_true')
    parser.add_argument('--version', action='version', version='%(prog)s 0.1')
    parsed_args = parser.parse_args(args)
    # print(parsed_args)
    return parsed_args


def main(args):
    """
    Entry point function for command line interface from the module.

    Used the parsed arguments to call the other functions with their parameters.
    """
    parsed_args = parseargs(args)
    if parsed_args.makejson:
        makejson(parsed_args.loadonline, parsed_args.jsonfile)
    if parsed_args.search is not None:
        search_print(top=parsed_args.top, search=parsed_args.search, category=parsed_args.category, use_json=not parsed_args.loadonline, jsonfile=parsed_args.jsonfile, threads=parsed_args.threads)
    if parsed_args.make:
        run_console(["python3", "-m", "pdoc", "--html", "-o", "./doc", "-f", "PyLeihe"])
    if parsed_args.test:
        pass
    return 0

def init():
    """
    Check if the package is run as console programm and start `main()` function.
    """
    if __name__ == "__main__":
        # execute only if run as a script
        sys.exit(main(sys.argv[1:]))

init()
