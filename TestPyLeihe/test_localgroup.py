"""
Testfunctins for `LocalGroup` from `bibindex.py`
"""
from collections import namedtuple
import logging
import json
from unittest import mock
import pytest
import _paths  # pylint: disable=unused-import
from PyLeihe.localgroup import LocalGroup


def test_getitem():
    """
    Test acces operation of LocalGroup
    """
    B1 = mock.Mock(title="B1")
    B2 = mock.Mock(title="B2")
    B3 = mock.Mock(title="B3")
    B4 = mock.Mock(title="B4")
    bibs = [B1, B2, B3, B4]
    land = LocalGroup(0, "", bibs=bibs)
    # check number and slice index
    assert land[0] == B1
    assert land[2] == B3
    assert land[-1] == B4
    assert land[1:-1] == [B2, B3]
    # check string key
    assert land["B1"] == B1
    assert land["B3"] == B3
    assert land["B5"] is None


@mock.patch("PyLeihe.localgroup.Bibliography")
@mock.patch("PyLeihe.localgroup.BeautifulSoup")
@mock.patch("PyLeihe.basic.PyLeiheWeb.simpleGET")
def test_loadBibURLs(mock_simpleGET, mock_BeautifulSoup, mock_Bibliography):
    """
    UnitTest for `LocalGroup.loadBibURLs`
    """
    # setup
    land = LocalGroup(73, "TestLand")
    links = [mock.MagicMock(href="m1.test", text="m1.city1"),
             mock.MagicMock(href="m1.test", text="m1.city2"),
             mock.MagicMock(href="m2.test", text="m2.city1")]
    for m in links:
        d = {'href': m.href}
        m.__getitem__.side_effect = d.__getitem__
        m.get_text.return_value = m.text
    # setup additional mocks
    soup = mock_BeautifulSoup.return_value
    soup.find.return_value.find_all.return_value = links
    mock_Bibliography.return_value = 1
    # run method under test
    land.loadBibURLs()
    # evaluate calls
    mock_simpleGET.assert_called_once()
    mock_BeautifulSoup.assert_called_once_with(mock_simpleGET.return_value.content,
                                               features="html.parser")
    assert mock_Bibliography.call_count == 2
    assert mock_Bibliography.call_args_list[0] == mock.call("m1.test", ["m1.city1", "m1.city2"])
    assert mock_Bibliography.call_args_list[1] == mock.call("m2.test", ["m2.city1"])
    assert len(land.Bibliotheken) == 2


@mock.patch("PyLeihe.localgroup.BeautifulSoup")
@mock.patch("PyLeihe.basic.PyLeiheWeb.simpleGET")
def test_loadBibURLs_exception(mock_simpleGET, mock_BeautifulSoup):
    """
    Checks if Exception during loadBibURLs is reraised
    """
    # setup
    land = LocalGroup(73, "TestLand")
    # setup additional mocks
    soup = mock_BeautifulSoup.return_value
    soup.find.return_value.find_all.return_value = ["abc"]
    # test
    with pytest.raises(Exception) as excinfo:
        assert land.loadBibURLs()
    assert "happens at" in str(excinfo.value)


def test_loadsearchURLs():
    """
    Test for `LocalGroup.loadsearchURLs`
    """
    B1 = mock.Mock(title="B1", search_url=None)
    B2 = mock.Mock(title="B2", search_url="url")
    land = LocalGroup(0, "", bibs=[B1, B2])
    land.loadsearchURLs(newtitle=False, force=False)
    assert B1.grepSearchURL.call_count == 1
    assert B1.generateTitle.call_count == 0
    assert B2.grepSearchURL.call_count == 0
    assert B2.generateTitle.call_count == 0

    B1 = mock.Mock(title="B1", search_url=None)
    B2 = mock.Mock(title="B2", search_url="url")
    land = LocalGroup(0, "", bibs=[B1, B2])
    land.loadsearchURLs(newtitle=True, force=True)
    assert B1.grepSearchURL.call_count == 1
    assert B1.generateTitle.call_count == 1
    assert B2.grepSearchURL.call_count == 1
    assert B2.generateTitle.call_count == 1


def test_fix_searchurl():
    """
    Test for `LocalGroup.fix_searchurl`
    """
    B1 = mock.Mock(title="B1", search_url=None)
    B2 = mock.Mock(title="B2", search_url=None)
    bibs = [B1, B2]
    land = LocalGroup(0, "", bibs=bibs)
    land.fix_searchurl("B3", "abc")
    assert B1.search_url is None
    land.fix_searchurl("B1", "url")
    assert B1.search_url == "url"
    assert B2.search_url is None


def test_from_url(caplog):
    """
    Test for `LocalGroup.from_url`
    """
    BLU = namedtuple('BL_Url', ['url', 'id', 'name'])
    to_test = [BLU("/index.php?id=43#badenwuerttemberg", 43, "badenwuerttemberg"),
               BLU("https://www.onleihe.net/index.php?id=35#mecklenburgvorpommern",
                   35, "mecklenburgvorpommern")]
    for x in to_test:
        BL = LocalGroup.from_url(x.url)
        assert BL.lid == x.id
        assert BL.name.lower() == x.name

    raised_value = 0
    for url in ["no_correct_url", "id=wrong#11", "3#badenwuerttemberg"]:
        try:
            LocalGroup.from_url(url)
        except ValueError:
            raised_value += 1
    assert raised_value == 3
    assert len([x for x in caplog.record_tuples if x[1] == logging.ERROR]) == 3
    if len(caplog.record_tuples) == 3:
        caplog.clear()


def test_from_groupbytitle():
    """
    Test for `LocalGroup.groupbytitle`
    """
    pass


def test_repr():
    """
    Test for `LocalGroup.__repr__`
    """
    land = LocalGroup(73, "TestLand")
    repr(land)


def test_groupbytitle():
    """
    Test behaviour of groupbytitle()

    grouping and key acces case insensitive.
    """
    land = LocalGroup(73, "TestLand")
    groups = ["A", "B", "C"]
    land.Bibliotheken = [
        mock.MagicMock(title="A", cities=["A1", "A2"]),
        mock.MagicMock(title="A", cities=["A3", "A4"]),
        mock.MagicMock(title="a", cities=["a1", "a2"]),
        mock.MagicMock(title="B", cities=["B1", "B2"]),
        mock.MagicMock(title="B", cities=["B3"]),
        mock.MagicMock(title="C", cities=["C3", "C4"]),
    ]
    land.groupbytitle()
    assert len(land.Bibliotheken) == len(groups)
    assert len(land["A"].cities) == 6
    assert len(land["b"].cities) == 3
    for g in groups:
        for c in land[g].cities:
            assert c[0].upper() == g.upper()


def test_reprJSON():
    """
    Checks if reprJSON returns a json serializable object.
    """
    land = LocalGroup(73, "TestLand")
    json.dumps(land.reprJSON())
