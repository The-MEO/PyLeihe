"""
Testfunctins for `PyLeiheWeb` from `basic.py`
"""
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
