"""
Testfunctins for  `PyLeiheNet` from `bibindex.py`
"""
from unittest import mock
import pytest
import _paths  # pylint: disable=unused-import
from PyLeihe.bibindex import PyLeiheNet


@mock.patch('PyLeihe.bibindex.PyLeiheNet.getBundesLaender')
def test_loadallBundesLaender(mock_get):
    """
    Test for `PyLeiheNet.loadallBundesLaender`
    """
    pln = PyLeiheNet()
    pln.loadallBundesLaender(groupbytitle=False, loadsearchURLs=True)
    mock_get.assert_called_once()
    mock_get.reset_mock()

    land = mock.Mock()
    pln.Laender = [land]
    pln.loadallBundesLaender(groupbytitle=False, loadsearchURLs=True)
    land.loadBibURLs.assert_called_once()
    land.loadsearchURLs.assert_called_once()
    land.groupbytitle.assert_not_called()

    land.reset_mock()
    pln.loadallBundesLaender(groupbytitle=True, loadsearchURLs=False)
    land.loadBibURLs.assert_called_once()
    land.loadsearchURLs.assert_not_called()
    land.groupbytitle.assert_called_once()

    mock_get.assert_not_called()


def test_get():
    """
    Test for get acces of `PyLeiheNet`
    """
    pln = PyLeiheNet()
    ml1 = mock.Mock(lid=1)
    ml1.name = "L1"
    ml2 = mock.Mock(lid=2)
    ml2.name = "L2"
    assert pln[1] is None
    pln.Laender = [ml1, ml2]
    assert pln[0] is None
    assert pln[1] == ml1
    assert pln["l2"] == ml2
