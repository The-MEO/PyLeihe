"""
Testfunctins for `PyLeiheWeb` from `basic.py`
"""
# pylint: disable=protected-access
import json
import urllib.parse as up
from unittest import mock
import pytest
import requests
import _paths  # pylint: disable=unused-import
from PyLeihe.basic import PyLeiheWeb


def test_session():
    """
    Checks if the Session is correct created.
    """
    plw1 = PyLeiheWeb()
    assert isinstance(plw1.Session, requests.Session), "Session was not created automatically"
    s = requests.Session()
    plw2 = PyLeiheWeb(sess=s)
    assert plw2.Session == s, "Session was not transferred"
    plw3 = PyLeiheWeb(sess=True)
    assert isinstance(plw3.Session, requests.Session), "Session was not recreated"
    assert plw1.Session != plw3.Session
    assert plw2.Session != plw3.Session


def test_getURL():
    """
    Test for `PyLeiheWeb.getURL()`
    """
    plw = PyLeiheWeb()
    assert plw.getURL("TEST") == "HTTPS://onleihe.net/TEST"
    assert plw.getURL(["Test", "index.html"]) == "HTTPS://onleihe.net/Test/index.html"
    PyLeiheWeb.DOMAIN = "domain"
    PyLeiheWeb.SCHEME = "scheme"
    assert plw.getURL("") == "scheme://domain/"
    plw = PyLeiheWeb()
    assert plw.DOMAIN == PyLeiheWeb.DOMAIN


@pytest.mark.parametrize("toformat,searchparams,expected",
                         [
                             (("post", "post"), {}, "toTest1.html"),
                             (("get", "post"), {}, "toTest2.html"),
                             (("post", "post"),
                              {"curr_url": "test.com/start.html"},
                              "test.com/toTest1.html"
                              ),
                             (("post", "post"),
                              {"ContNodeData": {"name": "test_input_2"}},
                              "toTest2.html"
                              ),
                             (("post", "post"),
                              {"ContNode": None, "ContNodeData": None},
                              "toTest1.html"
                              ),
                             (("post", "post"), {"ContNode": "h3"}, "toTest2.html"),
                             (("post", "post"), {"ContNode": "p"}, "toTest1.html"),
                             (("get", "post"), {"ContNode": "p"}, None),
                         ])
def test_getPostFormURL_searchNodeMultipleContain(toformat, searchparams, expected):
    """
    Test for `PyLeiheWeb.getPostFormURL()`

    Arguments:
        toformat: list with arguments to format the local `content`
        searchparams: dict with additional informationsto pass to `getPostFormURL`
        expected: expected result url
    """
    content = """
    <div>
        <h1>Test</h1>
        <form action='toTest1.html' method={0}>
        <p>
        Description
        </p>
        <input name='test_input_1'>
        </form>
        <h2>blabla</h2>
        <form action='toTest2.html' method={1}>
        <div>
        <h3>Description</h3>
        </div>
        <input name='test_input_2'>
        </form>
    </div>
    """
    url = PyLeiheWeb.getPostFormURL(
        content.format(*toformat),
        **searchparams
    )
    assert url == expected


def test_searchNodeMultipleContain():
    """
    already tested in `test_getPostFormURL_searchNodeMultipleContain`
    """
    pass


def test_get_title():
    """
    Checks the behaviour of `_get_title`
    """
    plw = PyLeiheWeb()
    assert plw._get_title() == ""
    plw.title = "title of uut"
    assert plw._get_title() == "title of uut"

@mock.patch("builtins.open", new_callable=mock.mock_open,
            read_data=json.dumps({'a': 'data', 'b': 2}))
@pytest.mark.parametrize("name_in,name_called,",
                         [("", "PyLeiheWeb.json"),
                          ("file.name", "file.name.json")
                          ])
def test_loadJSONFile(mock_file, name_in, name_called):
    """
    Tests `_loadJSONFile()`
    """
    assert PyLeiheWeb._loadJSONFile(name_in) == {'a': 'data', 'b': 2}
    mock_file.assert_called_once_with(name_called, "r")


@mock.patch("PyLeihe.basic.PyLeiheWeb.reprJSON")
@mock.patch("builtins.open", new_callable=mock.mock_open)
@pytest.mark.parametrize("name_in", ["", "write_to_file"])
def test_toJSONFile(mock_file, mock_reprJSON, name_in):
    """
    Tests toJSONFile
    """
    mock_reprJSON.return_value = {'d': "data", "j": "json"}
    plw = PyLeiheWeb()
    plw.toJSONFile(name_in)
    mock_file.return_value.write.assert_called()
    args, _kwargs = mock_file.call_args
    args_write_mode = args[1]
    args_filename = args[0]
    assert "w" in args_write_mode, "write mode required"
    assert len(args_filename) > 5, "meaningful file name required"
    assert args_filename.endswith(".json"), "json file format expected"
    if name_in:
        assert args_filename[:-5] == name_in


@mock.patch("PyLeihe.basic.PyLeiheWeb.simpleSession")
def test_simpleGET(mock_simpleSession):
    """
    Tests simpleGET
    """
    plw = PyLeiheWeb()
    assert mock_simpleSession.return_value == plw.simpleGET("url.test",
                                                            data="additional_data")
    mock_simpleSession.assert_called_once_with(url="url.test",
                                               method="get",
                                               data="additional_data")


def test_reprJSON():
    """
    Checks if reprJSON returns a json serializable object.
    """
    json.dumps(PyLeiheWeb.reprJSON())


@mock.patch("PyLeihe.basic.json.dumps")
@mock.patch("PyLeihe.basic.PyLeiheWeb.reprJSON")
def test_toJSON(mock_reprJSON, mock_json_dumps):
    """
    Checks if `toJSON` calls reprJSON as argument of json_dumps
    """
    plw = PyLeiheWeb()
    assert plw.toJSON() == mock_json_dumps.return_value
    mock_reprJSON.assert_called_once_with()
    mock_json_dumps.assert_called_once_with(mock_reprJSON.return_value)


@pytest.mark.parametrize("method_in", ["get", "post"])
def test_simpleSession(method_in):
    """
    Checks the normal case for `simpleSession`
    """
    # setup
    plw = PyLeiheWeb()
    plw.Session = mock.MagicMock(name="requests.Session")
    # test
    called_func = plw.Session.request
    assert called_func.return_value == plw.simpleSession(url="test.url",
                                                         method=method_in,
                                                         data="data_arg")
    called_func.assert_called_once_with(method_in.upper(), "test.url",
                                        data="data_arg")


@mock.patch("PyLeihe.basic.up.urlunparse")
def test_simpleSession_urlunparse(mock_urlunparse):
    """
    Checks the parsing of the url in `simpleSession`
    """
    # setup
    plw = PyLeiheWeb()
    plw.Session = mock.MagicMock(name="requests.Session")
    # test: url is already string
    plw.simpleSession(url="test.url")
    mock_urlunparse.assert_not_called()
    plw.Session.request.assert_called_with("POST", "test.url")
    # test: url is no string
    plw.simpleSession(url=up.urlparse("test.url"))
    mock_urlunparse.assert_called_once()
    plw.Session.request.assert_called_with("POST", mock_urlunparse.return_value)


def test_simpleSession_exception_ClosedConnection(caplog):
    """
    Checks `simpleSession` with `ClosedConnection` exception
    """
    # setup
    plw = PyLeiheWeb()
    plw.title = "UnitUnderTest"
    plw.Session = mock.Mock(name="requests.Session")
    mock_rfs = mock.Mock()
    mock_rfs.side_effect = requests.ConnectionError(
        "Remote end closed connection without response")
    plw.Session.request.return_value.raise_for_status = mock_rfs
    # test
    retrys = 3
    calls = retrys + 1
    assert plw.simpleSession(url="test.url", retry=retrys) is None
    assert plw.Session.request.call_count == calls
    assert mock_rfs.call_count == calls
    assert len([x for x in caplog.record_tuples
                if "Remote end closed connection" in x[2]]) == calls, \
        "A warning should be logged for each call with an error."
    if len(caplog.record_tuples) == calls:
        caplog.clear()


@pytest.mark.parametrize("effect", ["[Errno 11004] getaddrinfo failed",
                                    "[Errno -2] Name or service not known",
                                    "[Errno 8] nodename nor servname "])
def test_simpleSession_exception_getaddrinfo_failed(caplog, effect):
    """
    Checks `simpleSession` with `getaddrinfo failed` exception for different OS
    """
    # setup
    plw = PyLeiheWeb()
    plw.title = "UnitUnderTest"
    plw.Session = mock.Mock(name="requests.Session")
    mock_rfs = mock.Mock()
    mock_rfs.side_effect = requests.ConnectionError(effect)
    plw.Session.request.return_value.raise_for_status = mock_rfs
    # test
    assert plw.simpleSession(url="test.url") is None
    assert len([x for x in caplog.record_tuples
                if "Hostname can't be resolved" in x[2]]) == 1
    if len(caplog.record_tuples) == 1:
        caplog.clear()


def test_simpleSession_exception_unknown():
    """
    Checks the behaviour of `simpleSession` if an exception occurs.
    """  # setup
    plw = PyLeiheWeb()
    plw.title = "UnitUnderTest"
    plw.Session = mock.Mock(name="requests.Session")
    mock_rfs = mock.Mock()
    mock_rfs.side_effect = requests.ConnectionError("UnKnownException")
    plw.Session.request.return_value.raise_for_status = mock_rfs
    # test
    with pytest.raises(requests.ConnectionError):
        assert plw.simpleSession(url="test.url")


def test_simpleSession_recursion():
    """
    Checks the recursion crash prevention of `simpleSession`
    """
    # setup
    plw = PyLeiheWeb()
    plw.Session = mock.Mock(name="requests.Session")
    # test
    assert plw.simpleSession(url="test.url", retry=-1) is None
    assert plw.Session.request.call_count == 0
