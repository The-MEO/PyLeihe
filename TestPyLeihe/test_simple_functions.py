"""
Testfunctions for `Pyleihe.simple_functions`
"""
# pylint: disable=wrong-import-position,wildcard-import,unused-argument,no-self-use
import logging
from unittest import mock
import pytest
import _paths  # pylint: disable=unused-import
from PyLeihe.simple_functions import *


@mock.patch('PyLeihe.simple_functions.correct_searchurls_land')
def test_correct_search_urls(mock_correct_searchurls_land):
    """
    Checks if `correct_searchurls_land` is applied to every `PyLeiheNet.Laender`
    inside of `correct_search_urls`
    """
    PyLN = mock.Mock()
    PyLN.Laender = ["A", "B"]
    correct_search_urls(PyLN)
    assert mock_correct_searchurls_land.mock_calls == [mock.call(x) for x in PyLN.Laender]


class Test_correct_searchurls_land:
    """
    Checks if `correct_searchurls_land` sets some search-urls and is case insensitive.
    """

    def test_bw1(self):
        """
        Checks the first branch for 'bw'
        """
        # setup
        land = mock.MagicMock()
        d = {"libell-e": mock.MagicMock(search_url=None), "baden": mock.MagicMock()}
        land.__getitem__.side_effect = d.__getitem__
        land.name = "badenWuerttemberg"
        # test
        correct_searchurls_land(land)
        # checks
        land.Bibliotheken.remove.assert_called_once_with(d["baden"])
        assert isinstance(d["libell-e"].search_url, str)

    def test_bw2(self):
        """
        Checks the second branch for 'bw'
        """
        # setup
        land = mock.MagicMock()
        land.name = "badenWuerttemberg"
        d = {"libell-e": None, "baden": None}
        land.__getitem__.side_effect = d.__getitem__
        # run
        correct_searchurls_land(land)
        # evaluate
        land.Bibliotheken.remove.assert_not_called()

    @pytest.mark.parametrize(
        "country", [
            "sachsen", "Schleswigholstein", "Nordrheinwestfalen", "Sachsenanhalt"])
    def test_call_fix_searchurl(self, country):
        """
        Checks if fix_searchurl get called
        """
        land = mock.MagicMock()
        land.name = country
        correct_searchurls_land(land)
        land.fix_searchurl.assert_called()

    def test_different_libelle(self):
        """
        Checks if the libell-e search urls are different and if the state name is respected
        """
        # setup
        land = mock.MagicMock()
        d = {"libell-e": mock.MagicMock(search_url=None)}
        land.__getitem__.side_effect = d.__getitem__
        land.name = "noname"
        # test
        correct_searchurls_land(land)
        # checks
        assert isinstance(d["libell-e"].search_url, str)
        url1 = d["libell-e"].search_url
        # state name unknow -> no fix should be called
        land.fix_searchurl.assert_not_called()
        # get second url
        land.name = "Rheinlandpfalz"
        correct_searchurls_land(land)
        assert isinstance(d["libell-e"].search_url, str)
        url2 = d["libell-e"].search_url
        assert url1 != url2


@mock.patch('PyLeihe.simple_functions.correct_search_urls')
@mock.patch('PyLeihe.simple_functions.PyLeiheNet')
class TestMakejson:
    """
    Contains tests for `makejson`
    """

    def test_reload_true(self, mock_PyLeiheNet, mock_correct_search_urls, capsys):
        """
        Checks the call behaviour of `makejson(reload_data=True)`
        """
        # setup
        pln = mock_PyLeiheNet.return_value
        pln.Laender = [mock.MagicMock(name="Land1"), mock.MagicMock(name="Land2")]
        manager = mock.Mock()
        manager.attach_mock(pln.getBundesLaender, 'the_getBundesLaender')
        manager.attach_mock(pln.loadallBundesLaender, 'the_loadallBundesLaender')
        # run unit under test
        assert pln == makejson(reload_data=True,
                               filename="filename.text",
                               to_filename="to_filename.test")
        # check results
        pln.getBundesLaender.assert_called_once()
        pln.loadallBundesLaender.assert_called_once()
        expected_calls = [
            mock.call.the_getBundesLaender(),
            mock.call.the_loadallBundesLaender(groupbytitle=True, loadsearchURLs=False),
        ]
        assert manager.mock_calls == expected_calls
        pln.toJSONFile.assert_called_once_with("to_filename.test")
        for l in pln.Laender:
            l.loadsearchURLs.assert_called_once()
            l.groupbytitle.assert_called_once()
        # ignore prints
        capsys.readouterr()

    def test_reload_false(self, mock_PyLeiheNet, mock_correct_search_urls, capsys):
        """
        Checks the call behaviour of `makejson(reload_data=False)`
        """
        # setup
        mock_loadFromJSON = mock_PyLeiheNet.return_value.loadFromJSON
        pln = mock_loadFromJSON.return_value
        pln.Laender = [mock.MagicMock(name="Land1"), mock.MagicMock(name="Land2")]
        # run unit under test
        assert pln == makejson(reload_data=False,
                               filename="filename.text",
                               to_filename="to_filename.test")
        # check results
        mock_loadFromJSON.assert_called_once_with(filename="filename.text")
        pln.toJSONFile.assert_called_once_with("to_filename.test")
        for l in pln.Laender:
            l.loadsearchURLs.assert_called_once()
            l.groupbytitle.assert_called_once()
        # ignore prints
        capsys.readouterr()

    def test_exception(self, mock_PyLeiheNet, mock_correct_search_urls, capsys, caplog):
        """
        Checks the call behaviour of `makejson(reload_data=False)` when file not exists.
        """
        # setup
        mock_loadFromJSON = mock_PyLeiheNet.return_value.loadFromJSON
        pln = mock_loadFromJSON.return_value
        mock_loadFromJSON.side_effect = FileNotFoundError
        # run unit under test
        assert makejson(reload_data=False,
                        filename="filename.text",
                        to_filename="to_filename.test") is None
        # check results
        mock_loadFromJSON.assert_called_once_with(filename="filename.text")
        pln.toJSONFile.assert_not_called()
        # ignore prints
        capsys.readouterr()
        caplog.clear()


@mock.patch('PyLeihe.simple_functions.search_list')
def test_search_print(mock_search_list, capsys):
    """
    Checks the call behaviour of `search_print`.
    """
    # setup
    mock_search_list.return_value = [
        (mock.Mock(title="10R", cities=["c1"]), 10),
        (mock.Mock(title="7R", cities=["c8"]), 7),
        (mock.Mock(title="4R", cities=["c2"]), 4),
        (mock.Mock(title="6R", cities=["c3", "c4", "c5", "c6", "c7"]), 6),
        (None),
    ]
    # run unit under test
    # checks if None is removed from result_list
    search_print(15, 5, test=21)
    mock_search_list.reset_mock()
    # ignore prints
    capsys.readouterr()
    # checks top
    max_count = 3
    search_print(max_count, 5, test=21)
    # checks
    mock_search_list.assert_called_once_with(5, test=21)
    # check prints
    printed = capsys.readouterr()
    ascii_table = printed.out.split("\n")
    ascii_table = [r for r in ascii_table if r != '']
    assert len(ascii_table) == max_count
    assert "10R" in ascii_table[0]
    assert "7R" in ascii_table[1]
    assert "6R" in ascii_table[2]


@mock.patch('PyLeihe.simple_functions.Pool')
@mock.patch('PyLeihe.simple_functions.PyLeiheNet')
def test_search_list_single_thread(mock_PyLeiheNet, mock_Pool, caplog):
    """
    Checks the call behaviour of `search_list` with only one thread and
    import from JSON.
    """
    # setup
    caplog.set_level(logging.INFO)
    mock_loadFromJSON = mock_PyLeiheNet.return_value.loadFromJSON
    pln = mock_loadFromJSON.return_value
    mock_Laender = mock.PropertyMock()
    type(pln).Laender = mock_Laender
    # run unit under test
    result = search_list(search="searchword",
                         use_json=True,
                         jsonfile="json.file.test",
                         threads=0)
    # check subcalls
    mock_loadFromJSON.assert_called_once_with(filename="json.file.test")
    mock_Laender.assert_called_once_with()


@mock.patch('PyLeihe.simple_functions.parallel_search_helper')
@mock.patch('PyLeihe.simple_functions.Pool')
@mock.patch('PyLeihe.simple_functions.PyLeiheNet')
def test_search_list_multi_thread(mock_PyLeiheNet, mock_Pool, mock_parallel_search_helper, caplog):
    """
    Checks the call behaviour of `search_list` with only one thread and
    import from JSON.
    """
    # setup
    caplog.set_level(logging.INFO)
    pln = mock_PyLeiheNet.return_value
    mock_Laender = mock.PropertyMock()
    type(pln).Laender = mock_Laender
    threads = 5
    # run unit under test
    result = search_list(search="searchword",
                         use_json=False,
                         jsonfile="json.file.test",
                         threads=threads)
    # check subcalls
    mock_Laender.assert_called_once_with()
    mock_parallel_search_helper.assert_called_once_with("searchword", mock.ANY)
    # assert thread calls
    workpool = mock_Pool.return_value
    mock_Pool.assert_called_once_with(threads)
    workpool.map.assert_called_once_with(mock_parallel_search_helper.return_value, mock.ANY)
    workpool.close.assert_called_once()
    assert result == workpool.map.return_value


def test_parallel_search_helper():
    """
    Test `parallel_search_helper` return function.
    """
    to_run = parallel_search_helper("search word", "search category")
    bib = mock.MagicMock()
    result = to_run(bib)
    # checks
    bib.search.assert_called_once_with("search word", "search category")
    assert len(result) >= 2
    assert result[0] == bib
    assert result[1] == bib.search.return_value
