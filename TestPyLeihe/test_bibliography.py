"""
Testfunctins for `Bibliography` from `bibliography.py`
"""
# pylint: disable=protected-access, singleton-comparison
from unittest import mock
import pytest
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


@mock.patch('PyLeihe.bibliography.Bibliography._grepSearchURL_loadData')
@mock.patch('PyLeihe.bibliography.Bibliography._grepSearchURL_PostFormURL')
@mock.patch('PyLeihe.bibliography.Bibliography._grepSearchURL_simplelink')
@mock.patch('PyLeihe.bibliography.Bibliography._grepSearchURL_extendedSearch')
@mock.patch('PyLeihe.bibliography.Bibliography._grepSearchURL_href_secondSearch')
@pytest.mark.parametrize("level,NoneReturn,called,result",
                         [(0, 0, 0b1, True),
                          (0, 1, 0b1, False),
                          (1, 1, 0b11, True),
                          (2, 1, 0b11, True),
                          (2, -1, 0b1111, False),
                          (2, 2, 0b111, True),
                          (2, 3, 0b1111, True),
                          ])
def test_grepSearchURL_searchmethods(mock_secondSearch, mock_extendedSearch,
                                     mock_simplelink, mock_PostFormURL,
                                     mock_loadData,
                                     level, NoneReturn, called, result):
    """
    Test for `Bibliography.grepSearchURL` to validate the behaviour of the used methods

    Arguments:
        level (int)
        NoneReturn (int): mock int which returns `"url"` - all other return `None`
        called (int): the bits and their position (corresponding to the position
            in the mock list) indicates which mocks were executed exactly once
            and the other were not executed.
        result (bool): return value of the function to be tested for assert
    """
    # setup mocks
    mocks = [mock_secondSearch, mock_extendedSearch, mock_simplelink,
             mock_PostFormURL]
    mocks.reverse()
    # setup return values from mocks
    for m in mocks:
        m.return_value = None
    if NoneReturn >= 0:
        mocks[NoneReturn].return_value = "url"
    mock_loadData.return_value = mock.Mock(name="requests.Sessions")

    bib = Bibliography("")
    bib.search_url = None
    assert bib.grepSearchURL(lvl=level) == result
    if result:
        assert bib.search_url == "url", "if the function was executed \
            successfully, the search url was saved"
    else:
        assert bib.search_url is None, "if the function wasn't executed \
            successfully, the search url should be still None"

    # check called counts
    mock_loadData.assert_called_once_with()
    for i, m in enumerate(mocks):
        if (called >> i) & 0b1:
            mocks[i].assert_called_once_with(mock_loadData.return_value)
        else:
            mocks[i].assert_not_called()


@mock.patch('PyLeihe.bibliography.Bibliography._grepSearchURL_loadData')
@mock.patch('PyLeihe.bibliography.Bibliography._grepSearchURL_PostFormURL')
def test_grepSearchURL_basic(mock_PostFormURL, mock_loadData):
    """
    Test for `Bibliography.grepSearchURL` to check the DataLoading behaviour
    """
    bib = Bibliography("")
    # check for Error/None during loading
    mock_loadData.return_value = None
    assert bib.grepSearchURL() == False, "stop if loadData returns None"
    mock_loadData.assert_called_once()
    mock_PostFormURL.assert_not_called()
    # reset mocks
    mock_loadData.reset_mock()
    mock_PostFormURL.reset_mock()
    # check if first grap return None
    # reset mocks
    mock_loadData.reset_mock()
    mock_PostFormURL.reset_mock()
    # check if first grap works
    mock_loadData.return_value = mock.Mock(name="requests.Sessions")
    mock_PostFormURL.return_value = "url"
    assert bib.grepSearchURL() == True, "url should have been set"
    assert bib.search_url == "url"
    mock_loadData.assert_called_once()
    mock_PostFormURL.assert_called_once_with(mock_loadData.return_value)
