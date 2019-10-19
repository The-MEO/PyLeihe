"""
Testfunctions for `Pyleihe.simple_functions`
"""
# pylint: disable=wrong-import-position,wildcard-import
from unittest import mock
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
