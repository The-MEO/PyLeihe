"""
Testfunctins for `Bibliography` from `bibliography.py`
"""
from collections import namedtuple
from unittest import mock
import _paths  # pylint: disable=unused-import
from PyLeihe.bibliography import Bibliography


@mock.patch('PyLeihe.bibliography.Bibliography.generateTitle')
def test_init(mock_generateTitle):
    """
    Test initialization
    """
    bib = Bibliography("https://http//www.test.land")
    mock_generateTitle.assert_called_once()
    assert bib.url_up == "https://www.test.land"
    assert bib.url.netloc == "www.test.land"


@mock.patch('PyLeihe.bibliography.Bibliography._generateTitleByUrl')
def test_generateTitle(mock_generate):
    """
    Test title generation basic
    """
    bib = Bibliography("")
    mock_generate.reset_mock()
    url = "www.test.land"
    su = "www.search.test.land"
    bib.url = url
    bib.generateTitle()
    mock_generate.assert_called_once_with(url)
    mock_generate.reset_mock()
    bib.search_url = su
    bib.generateTitle()
    mock_generate.assert_called_once_with(su)


def test_repr():
    """
    Test for `Bibliography.__repr__`
    """
    bib = Bibliography("")
    repr(bib)


def test_parse_results():
    """
    Test for `Bibliography.parse_results`
    """
    cases = [("42-Treffer!", 42), ("5 \ttreffer", 5),
             ("keine Treffer", 0), ("keine  treffer", 0),
             ("0", -1)]
    for c in cases:
        SearchRequest = mock.Mock(text="Suchergebnis : " + c[0])
        assert Bibliography.parse_results(SearchRequest=SearchRequest) == c[1]


def test_generateTitleByUrl():
    """
    Test for `Bibliography._generateTitleByUrl`
    """
    cases = [("https://www4.onleihe.de/thuebibnet/frontend", "thuebibnet"),
             ("https://leo-sued.onleihe.de/leo-sued/frontend", "leo-sued"),
             ("https://franken.onleihe.de/verbund_franken/frontend", "verbund_franken"),
             ("http://www.nbib24.de/", "nbib24"),
             ("", ""),
             ("http://onleihe.de/", "onleihe.de"),
             ("http://onleihe.de/", "Berlin", ["Berlin"]),
             ("http://onleihe.de/", "Berlin...", ["Berlin", "Brandenburg"])]
    bib = Bibliography("")
    assert bib.title == ""
    for c in cases:
        if len(c) > 2:
            bib.cities = c[2]
        bib._generateTitleByUrl(c[0])
        assert bib.title == c[1]
