"""
Testfunctins for `BundesLand` from `bibindex.py`
"""
from collections import namedtuple
from unittest import mock
import logging
import _paths  # pylint: disable=unused-import
from PyLeihe.bibindex import BundesLand


def test_getitem():
    """
    Test acces operation of BundesLand
    """
    B1 = mock.Mock(title="B1")
    B2 = mock.Mock(title="B2")
    B3 = mock.Mock(title="B3")
    B4 = mock.Mock(title="B4")
    bibs = [B1, B2, B3, B4]
    land = BundesLand(0, "", bibs=bibs)
    # check number and slice index
    assert land[0] == B1
    assert land[2] == B3
    assert land[-1] == B4
    assert land[1:-1] == [B2, B3]
    # check string key
    assert land["B1"] == B1
    assert land["B3"] == B3
    assert land["B5"] is None


def test_loadBibURLs():
    """
    Test for `BundesLand.loadBibURLs`
    """
    pass


def test_loadsearchURLs():
    """
    Test for `BundesLand.loadsearchURLs`
    """
    B1 = mock.Mock(title="B1", search_url=None)
    B2 = mock.Mock(title="B2", search_url="url")
    land = BundesLand(0, "", bibs=[B1, B2])
    land.loadsearchURLs(newtitle=False, force=False)
    assert B1.grepSearchURL.call_count == 1
    assert B1.generateTitle.call_count == 0
    assert B2.grepSearchURL.call_count == 0
    assert B2.generateTitle.call_count == 0

    B1 = mock.Mock(title="B1", search_url=None)
    B2 = mock.Mock(title="B2", search_url="url")
    land = BundesLand(0, "", bibs=[B1, B2])
    land.loadsearchURLs(newtitle=True, force=True)
    assert B1.grepSearchURL.call_count == 1
    assert B1.generateTitle.call_count == 1
    assert B2.grepSearchURL.call_count == 1
    assert B2.generateTitle.call_count == 1


def test_fix_searchurl():
    """
    Test for `BundesLand.fix_searchurl`
    """
    B1 = mock.Mock(title="B1", search_url=None)
    B2 = mock.Mock(title="B2", search_url=None)
    bibs = [B1, B2]
    land = BundesLand(0, "", bibs=bibs)
    land.fix_searchurl("B3", "abc")
    assert B1.search_url is None
    land.fix_searchurl("B1", "url")
    assert B1.search_url == "url"
    assert B2.search_url is None


def test_from_url(caplog):
    """
    Test for `BundesLand.from_url`
    """
    BLU = namedtuple('BL_Url', ['url', 'id', 'name'])
    to_test = [BLU("/index.php?id=43#badenwuerttemberg", 43, "badenwuerttemberg"),
               BLU("https://www.onleihe.net/index.php?id=35#mecklenburgvorpommern",
                   35, "mecklenburgvorpommern")]
    for x in to_test:
        BL = BundesLand.from_url(x.url)
        assert BL.lid == x.id
        assert BL.name.lower() == x.name

    raised_value = 0
    for url in ["no_correct_url", "id=wrong#11", "3#badenwuerttemberg"]:
        try:
            BundesLand.from_url(url)
        except ValueError:
            raised_value += 1
    assert raised_value == 3
    assert len([x for x in caplog.record_tuples if x[1] == logging.ERROR]) == 3


def test_from_groupbytitle():
    """
    Test for `BundesLand.groupbytitle`
    """
    pass


def test_repr():
    """
    Test for `BundesLand.__repr__`
    """
    land = BundesLand(73, "TestLand")
    repr(land)
