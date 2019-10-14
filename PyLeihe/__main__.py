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
from . import PyLeiheNet, MediaType  # pylint: disable=unused-import
from .simple_functions import makejson, search_print


def run_console(cmd):
    """
    Executes commands for development (to test or document) in the console

    Arguments:
        cmd: shell coammand to execute (list with strings)-used for `subprocess.Popen`

    Return:
        Returns the exit code of the called command.
    """
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

    Arguments:
        args: arguments from the program call with the options

    Return: named tuple with the parsed arguments
    """
    # pylint: disable=line-too-long
    parser = argparse.ArgumentParser(description='Python search for the german online libraries - created by MEO')  # noqa: E501
    parser.add_argument('--loadonline', help='loads all neccessary data from the web', action='store_true')  # noqa: E501
    parser.add_argument('--makejson', help='group and correct and finally saves the data to a json file', action='store_true')  # noqa: E501
    parser.add_argument('-j', '--jsonfile', help="Path to the jsonfile", default="")  # noqa: E501
    parser.add_argument('-s', '--search', help="Search for keywords in all bibs")  # noqa: E501
    parser.add_argument('-c', '--category', help="Media category", type=lambda t: MediaType[t], choices=list(MediaType), default=MediaType.alleMedien)  # noqa: E501
    parser.add_argument('-t', '--top', help="Number of print results", type=int, default=-1)  # noqa: E501
    parser.add_argument('--threads', help="Number of used parallel threads", type=int, default=4)  # noqa: E501
    parser.add_argument('--csv', help="stores result in csv", action='store_true')  # noqa: E501
    parser.add_argument('--make', help="[only for Developer] do some build tasks", action='store_true')  # noqa: E501
    parser.add_argument('--test', help="[only for Developer] do some test tasks", action='store_true')  # noqa: E501
    parser.add_argument('--version', action='version', version='%(prog)s 0.1')  # noqa: E501
    parsed_args = parser.parse_args(args)  # noqa: E501
    # pylint: enable=line-too-long
    # print(parsed_args)
    return parsed_args


def main(args):
    """
    Entry point function for command line interface from the module.

    Used the parsed arguments to call the other functions with their parameters.

    Arguments:
        args: arguments from the program call with the options

    Return:
        int if no error has occurred 0

    Raises:
        NotImplementedError: if option test is selected

    """
    parsed_args = parseargs(args)
    if parsed_args.makejson:
        makejson(parsed_args.loadonline, parsed_args.jsonfile)
    if parsed_args.search is not None:
        search_print(top=parsed_args.top,
                     search=parsed_args.search,
                     category=parsed_args.category,
                     use_json=not parsed_args.loadonline,
                     jsonfile=parsed_args.jsonfile,
                     threads=parsed_args.threads)
    if parsed_args.make:
        run_console(["python3", "-m", "pdoc", "--html", "-o", "./doc", "-f", "PyLeihe"])
    if parsed_args.test:
        raise NotImplementedError("run the test in the project directory with `pytest`")
    return 0


def init():
    """
    Check if the package is run as console programm and start `main()` function.

    Code summarized for unit testing.
    """
    if __name__ == "__main__":
        # execute only if run as a script
        sys.exit(main(sys.argv[1:]))


init()
