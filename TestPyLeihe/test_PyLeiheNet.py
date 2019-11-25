"""
Testfunctins for  `PyLeiheNet` from `bibindex.py`
"""
# pylint: disable=unused-import
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


def test_getBib():
    """
    Test the bib search.
    """
    pln = PyLeiheNet()
    pln.Laender = [{'a': None, 'b': 'b1', 'c': None},
                   {'a': 'a2', 'b': 'b2', 'c': None}]
    assert pln.getBib('a') == 'a2'
    assert pln.getBib('b') == 'b1'
    assert pln.getBib('c') is None


@mock.patch('PyLeihe.bibindex.PyLeiheNet.simpleGET')
@mock.patch('PyLeihe.bibindex.PyLeiheNet.getURL')
def test_getBundesLaender(mock_getURL, mock_simpleGET):
    """
    Test for getBundesLaender
    """
    mock_simpleGET.return_value = mock.Mock()
    mock_simpleGET.return_value.content = """
    <div>
    <map name="mapName" id="mapName">
		<!-- Thueringen -->
		<area shape="poly" alt="Zum Wunschformular" href="/index.php?id=39#thueringen" >
		<!-- Bayern -->
		<area shape="poly" alt="Zum Wunschformular" href="/index.php?id=44#bayern" >
		<!-- Baden-WÃ¼rttemberg -->
		<area shape="poly" alt="Zum Wunschformular" href="/index.php?id=43#badenwuerttemberg" >
		<!-- Saarland -->
		<area shape="poly" alt="Zum Wunschformular" href="/index.php?id=42#saarland" >
		<!-- Rheinland-Pfalz -->
		<area shape="poly" alt="Zum Wunschformular" href="/index.php?id=41#rheinlandpfalz" >
		<!-- Hessen -->
		<area shape="poly" alt="Zum Wunschformular" href="/index.php?id=40#hessen" >
		<!-- Nordrhein-Westfalen -->
		<area shape="poly" alt="Zum Wunschformular" href="/index.php?id=45#nordrheinwestfalen" >
		<!-- Bremen -->
		<area shape="poly" alt="Zum Wunschformular" href="/index.php?id=31#bremen" >
		<area shape="poly" alt="Zum Wunschformular" href="/index.php?id=31#bremen" >
	</map>
    </div>
    """
    pln = PyLeiheNet()
    pln.getBundesLaender()
    mock_getURL.assert_called_once_with(pln.URL_Deutschland)
    mock_simpleGET.assert_called_once_with(mock_getURL.return_value)
    ids = [l.lid for l in pln.Laender]  # pylint: disable=no-member
    ids_ref = [39, 44, 43, 42, 41, 40, 45, 31]
    assert len(ids) == len(ids_ref)
    assert any([True for e in ids_ref if e in ids])
