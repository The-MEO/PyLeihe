import sys
import os
DIR = os.path.dirname(__file__)
sys.path.append(os.path.join(DIR, ".."))
import pytest
from PyLeihe.basic import PyLeiheWeb
import requests


def test_session():
    """
    Checks if the Session is correct created.
    """
    plw1 = PyLeiheWeb()
    assert isinstance(plw1.Session, requests.Session), "Session was not created automatically"
    s = requests.Session()
    plw2 = PyLeiheWeb(sess=s)
    assert plw2.Session == s, "Session was not transferred"
    plw3 = PyLeiheWeb(sess=True)
    assert isinstance(plw3.Session, requests.Session), "Session was not recreated"
    assert plw1.Session != plw3.Session
    assert plw2.Session != plw3.Session

def test_getURL():
    plw = PyLeiheWeb()
    assert plw.getURL("TEST") == "HTTPS://onleihe.net/TEST"
    assert plw.getURL(["Test", "index.html"]) == "HTTPS://onleihe.net/Test/index.html"
    PyLeiheWeb.DOMAIN = "domain"
    PyLeiheWeb.SCHEME = "scheme"
    assert plw.getURL("") == "scheme://domain/"
    plw = PyLeiheWeb()
    assert plw.DOMAIN == PyLeiheWeb.DOMAIN

def test_getPostFormURL():
    pass
