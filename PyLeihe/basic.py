"""
"""
import json
import urllib.parse as up
import requests
from bs4 import BeautifulSoup


class PyLeiheWeb:
    DOMAIN = "onleihe.net"
    SCHEME = "HTTPS"

    Session = None

    def __init__(self, sess=None):
        if sess is not None:
            self.Session = sess
        if self.Session is None or sess == True:
            self.Session = requests.Session()

    @classmethod
    def reprJSON(cls):
        return {
            "cls": cls.__name__
        }

    def toJSON(self):
        return json.dumps(self.reprJSON())

    @classmethod
    def toJSONFile(cls, filename=""):
        if filename == "":
            filename = cls.__name__
        with open('{}.json'.format(filename), 'w') as f:
            json.dump(cls.reprJSON(), f, sort_keys=False, indent=4)

    @classmethod
    def _loadJSONFile(cls, filename=""):
        if filename == "":
            filename = cls.__name__
        with open('{}.json'.format(filename), 'r') as f:
            data = json.load(f)
        return data

    @classmethod
    def searchNodeMultipleContain(cls, content, Node, NodeAttr, ContNode=None, ContNodeData=None):
        ContNodeData = ContNodeData or {}
        soup = BeautifulSoup(content, features="html.parser")
        forms = soup.find_all(Node, attrs=NodeAttr)
        found_forms = len(forms)
        if found_forms == 0:
            return None
        elif found_forms == 1 or ContNode == "" or ContNode is None:
            return forms[0]
        else:
            for f in forms:
                if f.find(ContNode, ContNodeData):
                    return f

    @classmethod
    def getPostFormURL(cls, content, ContNode="", curr_url=None, ContNodeData=None):
        form = cls.searchNodeMultipleContain(content, "form", {"method": "post"}, ContNode, ContNodeData)
        if form is None:
            return None
        form_action = form.get('action')
        if curr_url is None:
            return form_action
        return up.urljoin(curr_url, form_action)

    @classmethod
    def getURL(cls, to):
        if not isinstance(to, str):
            to = "/".join(to)
        return cls.SCHEME + "://" + cls.DOMAIN + "/" + to
