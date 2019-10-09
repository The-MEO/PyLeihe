"""
Tests to check the command line interface from the module
"""
import sys
import os
from unittest import mock
import pytest
DIR = os.path.dirname(__file__)
sys.path.append(os.path.join(DIR, ".."))
from PyLeihe import __main__ as pylmain


def test_checkmaincall():
    """
    Checks if the main() function is called if the module is called from command line.
    """
    with mock.patch.object(pylmain, "main", return_value=42):
        with mock.patch.object(pylmain, "__name__", "__main__"):
            with mock.patch.object(pylmain.sys, 'exit') as mock_exit:
                pylmain.init()
                assert mock_exit.call_args[0][0] == 42


@mock.patch('PyLeihe.__main__.run_console')
@mock.patch('PyLeihe.__main__.search_print')
@mock.patch('PyLeihe.__main__.makejson')
def test_main_nothing(mock_makejson, mock_search_print, mock_run_console):
    pylmain.main([])
    mock_makejson.assert_not_called()
    mock_search_print.assert_not_called()
    mock_run_console.assert_not_called()


@mock.patch('PyLeihe.__main__.run_console')
@mock.patch('PyLeihe.__main__.search_print')
@mock.patch('PyLeihe.__main__.makejson')
def test_main_makejson(mock_makejson, mock_search_print, mock_run_console):
    pylmain.main(["--makejson"])
    mock_makejson.assert_called_once_with(False, "")
    mock_search_print.assert_not_called()
    mock_run_console.assert_not_called()

    mock_makejson.reset_mock()
    pylmain.main(["--makejson", '--loadonline', "-j", "./path/to/file"])
    mock_makejson.assert_called_once_with(True, "./path/to/file")


@mock.patch('PyLeihe.__main__.run_console')
@mock.patch('PyLeihe.__main__.search_print')
@mock.patch('PyLeihe.__main__.makejson')
def test_main_search(mock_makejson, mock_search_print, mock_run_console):
    pylmain.main(["-s", "TestSuche42"])
    a, k = mock_search_print.call_args
    assert k['search'] == "TestSuche42", "argument search word is at the right function parameter"
    assert k['jsonfile'] != "TestSuche42", "argument search word is at the right function parameter (not json file path)"
    assert k['use_json'] == True, "default use local json file"

    pylmain.main(["-s", "StarTrek", "--threads", "42"])
    a, k = mock_search_print.call_args
    assert k['search'] == "StarTrek", "check search word"
    assert k['threads'] == 42, "check thread parameter"

    mock_makejson.assert_not_called()
    mock_run_console.assert_not_called()
    assert mock_search_print.call_count == 2


def test_parseargs():
    """
    Checks if the parsing from the parameters are working
    """
    parsed = pylmain.parseargs(["--makejson", "--loadonline"])
    assert (parsed.makejson
            and parsed.loadonline == True
            and parsed.make == False
            and parsed.test == False)
