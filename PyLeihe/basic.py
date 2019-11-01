"""
Basic Class to provide similar interfaces
and basic methods to all child classes
"""
import json
import urllib.parse as up
import requests
from bs4 import BeautifulSoup


class PyLeiheWeb:
    """
    Basic Class to provide similar interfaces
    and basic methods to all child classes
    """
    DOMAIN = "onleihe.net"
    SCHEME = "HTTPS"

    Session = None

    def __init__(self, sess=None):
        if sess is not None:
            self.Session = sess
        if self.Session is None or sess is True:
            self.Session = requests.Session()

    @classmethod
    def reprJSON(cls):
        """
        Creates a JSON combatable representation.

        .. HINT::
            Should be implemented individually for each class.

        Returns:
            json compatible representation (dict or list)
        """
        return {
            "cls": cls.__name__
        }

    def toJSON(self):
        """
        Converts the current object instance to json.

        Calls the `reprJSON` method from the instance
        to get a json compatible representation
        """
        return json.dumps(self.reprJSON())

    @classmethod
    def toJSONFile(cls, filename=""):
        """
        Saves the json representation as a file

        Uses the functions `toJSON()` and
        thus including `reprJSON()`

        Arguments:
            filename: `str`path to the file to write
        """
        if filename == "":
            filename = cls.__name__
        with open('{}.json'.format(filename), 'w') as f:
            json.dump(cls.reprJSON(), f, sort_keys=False, indent=4)

    @classmethod
    def _loadJSONFile(cls, filename=""):
        """
        Private method to load a JSON file and
        automatically convert it to python types.

        Returns:
            the json data as python types (dict or list)
        """
        if filename == "":
            filename = cls.__name__
        with open('{}.json'.format(filename), 'r') as f:
            data = json.load(f)
        return data

    @classmethod
    def searchNodeMultipleContain(cls, content, Node, NodeAttr, ContNode=None, ContNodeData=None):
        """
        Searches an html text `content` for the first occurrence of an `Node`
        with the properties `NodeAttr`.
        As an additional condition it can be required
        that a certain node `ContNode` must be contained in the foudn `Node`
        with certain properties `ContNodeData`.

        Arguments:
            content: `str` html content
            Node: `str`name of the node
            NodeAttr: `dict(str: str)` with the attributes of the nodes
            ContNode: `str` optional addition node wich must be inside of `Node`
            ContNodeData: `dict(str: str)` with the attributes of the `ContNode`

        Returns:
            First node that meets the conditions
        """
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
        """
        Searches an html text `content` for the destination address
        of the first html post form.
        As an additional condition it can be required that the form should contain
        a specific `ContNode`.

        Arguments:
            content: `str` html content
            curr_url: _optional_ address of the form,
                if available this is combined with the target address
            ContNode: `str` optional node wich must be inside of the form
            ContNodeData: `dict(str: str)` with the attributes of the `ContNode`

        Returns:
            `str` with the destination url of the form
        """
        form = cls.searchNodeMultipleContain(content,
                                             Node="form",
                                             NodeAttr={"method": "post"},
                                             ContNode=ContNode,
                                             ContNodeData=ContNodeData)
        if form is None:
            return None
        form_action = form.get('action')
        if curr_url is None:
            return form_action
        return up.urljoin(curr_url, form_action)

    @classmethod
    def getURL(cls, to):
        """
        Build a URL from the given schema, domain and target path on the server and return it.

        Arguments:
            to: `str` or `list(str)` path of a destination address

        Returns:
            `str` with the compound url
        """
        if not isinstance(to, str):
            to = "/".join(to)
        return cls.SCHEME + "://" + cls.DOMAIN + "/" + to
