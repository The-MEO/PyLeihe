"""
Unit and function tests to check all json related function and methods.
"""
from unittest import mock
from PyLeihe import PyLeiheNet, BundesLand, Bibliography


# PyLeiheNet
def test_PyLeiheNet_to_json():
    """
    Checks the conversion of an `PyLeiheNet` instance to json
    """
    pln = PyLeiheNet()
    assert pln.reprJSON() == {}
    pln.Laender.extend([mock.Mock(), mock.Mock(), mock.Mock()])
    pln.Laender[0].name = "Alf"
    pln.Laender[0].reprJSON.return_value = "Melmac"
    pln.Laender[1].name = "Kangaroo"
    pln.Laender[1].reprJSON.return_value = "liquor praline"
    pln.Laender[2].name = "StarTrek"
    pln.Laender[2].reprJSON.return_value = ['UFP', 'KlingonEmpire']
    r = pln.reprJSON()
    assert r["Alf"] == "Melmac"
    assert r["Kangaroo"] == "liquor praline"
    assert isinstance(r["StarTrek"], list)
    assert r["StarTrek"][0] == "UFP"
    assert r["StarTrek"][1] == "KlingonEmpire"


# BundesLand
def test_BundesLand_to_json():
    """
    Checks the conversion of an `BundesLand` instance to json
    """
    bl = BundesLand("42", "the land of red towels")
    j = bl.reprJSON()
    assert j["id"] == 42, "check ID convertion from string to int"
    assert j["name"][0] == "T", "check name capitalize"
    assert j["name"] == "The_land_of_red_towels", "check whitespace replacement"
    assert j["bibliotheken"] == {}
    # TODO add bibliotheken mocks and check if they are correctly added


# Bibliography
def test_Bibliography_to_json():
    """
    Checks the conversion of an `Bibliography` instance to json
    """
    pass
