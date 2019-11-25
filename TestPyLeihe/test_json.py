"""
Unit and function tests to check all json related function and methods.
"""
# pylint: disable=wrong-import-position,wildcard-import
from unittest import mock
import _paths  # pylint: disable=unused-import
from PyLeihe import PyLeiheNet, LocalGroup, Bibliography
from PyLeihe.basic import PyLeiheWeb


def add_jsonMockList():
    """
    returns a list with simple mocks for json repr testing
    """
    ml = [mock.Mock(), mock.Mock(), mock.Mock()]
    ml[0].name = "Alf"
    ml[0].reprJSON.return_value = "Melmac"
    ml[1].name = "Kangaroo"
    ml[1].reprJSON.return_value = "liquor praline"
    ml[2].name = "StarTrek"
    ml[2].reprJSON.return_value = ['UFP', 'KlingonEmpire']
    for m in ml:
        m.title = m.name
    return ml


def check_jsonMockList(j):
    """
    checks the json mocks from `add_jsonMockList`
    """
    assert j["Alf"] == "Melmac"
    assert j["Kangaroo"] == "liquor praline"
    assert isinstance(j["StarTrek"], list)
    assert j["StarTrek"][0] == "UFP"
    assert j["StarTrek"][1] == "KlingonEmpire"


# PyLeiheWeb
@mock.patch('PyLeihe.basic.json.dumps')
@mock.patch('PyLeihe.basic.PyLeiheWeb.reprJSON')
def test_PyLeiheWeb_to_json(mock_repr, mock_jsondumps):
    """
    Checks if the right functions are called for json convertion.
    """
    ret_mock_repr = mock_repr.return_value
    plw = PyLeiheWeb()
    plw.toJSON()
    mock_jsondumps.assert_called_once_with(ret_mock_repr)
    mock_repr.assert_called_once_with()


def test_PyLeiheWeb_reprJSON():
    """
    Default JSON representation should return class name as dict
    """
    plw = PyLeiheWeb()
    j = plw.reprJSON()
    assert j == {"cls": "PyLeiheWeb"}, \
        "default JSON representation should return class name as dict"


# PyLeiheNet
def test_PyLeiheNet_to_json():
    """
    Checks the conversion of an `PyLeiheNet` instance to json
    """
    pln = PyLeiheNet()
    assert pln.reprJSON() == {}
    pln.Laender.extend(add_jsonMockList())
    r = pln.reprJSON()
    check_jsonMockList(r)


@mock.patch('PyLeihe.LocalGroup.loadFromJSON')
@mock.patch('PyLeihe.PyLeiheNet._loadJSONFile')
def test_PyLeiheNet_from_json(mock_loadJSONFile, mock_LocalGrouploadFromJSON):
    """
    Checks the conversion of an `PyLeiheNet` instance from json
    """
    j = {"T1": "Test1", "T2": "Test2"}
    filepath = "path/to/file"
    pln = None
    # check both paths: with direct data or import from file
    for branch in range(0, 2):
        mock_loadJSONFile.reset_mock()
        mock_LocalGrouploadFromJSON.reset_mock()
        mock_loadJSONFile.return_value = j
        if branch == 0:
            pln = PyLeiheNet.loadFromJSON(data=j)
        else:
            pln = PyLeiheNet.loadFromJSON(filename=filepath)
            # check the work inside the function
            assert mock_loadJSONFile.call_args == mock.call(filepath),\
                "only one parameter (filename)"
        assert mock_LocalGrouploadFromJSON.call_count == len(j)
        assert len(mock_LocalGrouploadFromJSON.call_args_list) == len(j)
        for call_data in j.values():
            count = len([x for x in mock_LocalGrouploadFromJSON.call_args_list
                         if x == mock.call(call_data)])
            assert count == 1, "every dict value should be exactly one time the call parameter"
        # check the end result
        assert len(pln.Laender) == len(j)


# LocalGroup
def test_LocalGroup_to_json():
    """
    Checks the conversion of an `LocalGroup` instance to json
    """
    bl = LocalGroup("42", "the land of red towels")
    j = bl.reprJSON()
    assert j["id"] == 42, "check ID convertion from string to int"
    assert j["name"][0] == "T", "check name capitalize"
    assert j["name"] == "The_land_of_red_towels", "check whitespace replacement"
    assert j["bibliotheken"] == {}
    # add bibliotheken mocks and check if they are correctly added
    bl.Bibliotheken.extend(add_jsonMockList())
    r = bl.reprJSON()
    check_jsonMockList(r['bibliotheken'])


# Bibliography
def test_Bibliography_to_json():
    """
    Checks the conversion of an `Bibliography` instance to json
    """
    url = "http://test.url/"
    cities = ["Vulcan", "Romulus", "Ferenginar", "Risa"]
    bib = Bibliography(url)
    j = bib.reprJSON()
    assert j["name"] == "test"
    assert j["url"] == url
    assert j["search_url"] is None
    assert isinstance(j["cities"], list)
    assert not j["cities"]
    bib = Bibliography(url, cities=cities)
    j = bib.reprJSON()
    assert j["cities"] == cities
