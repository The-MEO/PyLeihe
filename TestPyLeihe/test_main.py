"""
Tests to check the command line interface from the module
"""
from unittest import mock
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


@mock.patch('PyLeihe.__main__.dev_make')
@mock.patch('PyLeihe.__main__.search_print')
@mock.patch('PyLeihe.__main__.makejson')
def test_main_nothing(mock_makejson, mock_search_print, mock_dev_make):
    """
    Test checks that no actions are performed without parameter call.
    Ideally, the help should be displayed, but this is not yet checked.
    """
    pylmain.main([])
    mock_makejson.assert_not_called()
    mock_search_print.assert_not_called()
    mock_dev_make.assert_not_called()


@mock.patch('PyLeihe.__main__.dev_make')
@mock.patch('PyLeihe.__main__.search_print')
@mock.patch('PyLeihe.__main__.makejson')
def test_main_makejson(mock_makejson, mock_search_print, mock_dev_make):
    """
    test checks whether the makejson parameter calls the corresponding function only.
    In addition to a simple call, it also controls specifying a json file
    and the command to load the data.
    """
    pylmain.main(["--makejson"])
    mock_makejson.assert_called_once_with(False, "")
    mock_search_print.assert_not_called()
    mock_dev_make.assert_not_called()

    mock_makejson.reset_mock()
    pylmain.main(["--makejson", '--loadonline', "-j", "./path/to/file"])
    mock_makejson.assert_called_once_with(True, "./path/to/file")


@mock.patch('PyLeihe.__main__.dev_make')
@mock.patch('PyLeihe.__main__.search_print')
@mock.patch('PyLeihe.__main__.makejson')
def test_main_search(mock_makejson, mock_search_print, mock_dev_make):
    """
    Checks parsing with some search parameters.
    """
    pylmain.main(["-s", "TestSuche42"])
    _a, k = mock_search_print.call_args
    assert k['search'] == "TestSuche42", "argument search word is at the right function parameter"
    assert k['jsonfile'] != "TestSuche42", "argument search word is at the right function param" \
                            "(not json file path)"
    assert k['use_json'] is True, "default use local json file"

    pylmain.main(["-s", "StarTrek", "--threads", "42", "-c", "eBook"])
    _a, k = mock_search_print.call_args
    assert k['search'] == "StarTrek", "check search word"
    assert k['threads'] == 42, "check thread parameter"
    assert k['category'] == pylmain.MediaType.eBook, "check category parameter"

    mock_makejson.assert_not_called()
    mock_dev_make.assert_not_called()
    assert mock_search_print.call_count == 2


@mock.patch('PyLeihe.__main__.dev_make')
@mock.patch('PyLeihe.__main__.search_print')
@mock.patch('PyLeihe.__main__.makejson')
def test_main_make(mock_makejson, mock_search_print, mock_dev_make):
    """
    Function tests whether the make function was called with the corresponding
    command line parameter.
    """
    ret_main = pylmain.main(["--make"])
    assert ret_main == 0, "main should return no error exit code"
    mock_search_print.assert_not_called()
    mock_makejson.assert_not_called()
    assert mock_dev_make.call_count == 1


def test_parseargs():
    """
    Checks if the parsing from the parameters are working
    """
    parsed = pylmain.parseargs(["--makejson", "--loadonline"])
    assert (parsed.makejson
            and parsed.loadonline is True
            and parsed.make is False
            and parsed.test is False)


@mock.patch('PyLeihe.__main__.subprocess.Popen')
def test_run_console(mock_popen):
    """
    Üper checks the functionality of the `run_console` function
    """
    instance = mock_popen.return_value
    instance.returncode = 0

    cmd = ["command", "param1", "value"]
    c = pylmain.run_console(cmd)
    a, _k = mock_popen.call_args
    assert a[0] == cmd, "command should be looped through"
    assert c == 0, "should return the exit code"
    instance.returncode = 1
    c = pylmain.run_console(["command_2", "param2", "value2"])
    assert c == 1, "should return the exit code"


@mock.patch('PyLeihe.__main__.run_console')
def test_dev_make(mock_run_console):
    """
    checks if the make jobs are called
    """
    pylmain.dev_make()
    a, _k = mock_run_console.call_args
    assert a[0][:3] == ["python3", "-m", "pdoc"], "check pdoc command"
    assert mock_run_console.call_count == 1
