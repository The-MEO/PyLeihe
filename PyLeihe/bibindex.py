# -*- coding: utf-8 -*-
"""
Contains container objects to group the libraries and bibliographies logically
"""
from bs4 import BeautifulSoup


from .basic import PyLeiheWeb
from .localgroup import LocalGroup


class PyLeiheNet(PyLeiheWeb):
    """
    Group Object for multiple `LocalGroup` instances.
    """
    URL_Deutschland = "fuer-leser-hoerer-zuschauer/ihre-onleihe-finden/onleihen-in-deutschland.html"

    def __init__(self):
        super().__init__()
        self.Laender = []

    def __getitem__(self, key):
        """
        Returns the `LocalGroup` belonging to the `key` or `None`.

        Arguments:
            key:
                * `int` the id of the requested `LocalGroup`
                * `str` the name of the requested `LocalGroup`
                    _case insensitive_
        """
        for x in self.Laender:
            if x.lid == key or (isinstance(key, str) and x.name.lower() == key.lower()):
                return x
        return None

    def getBib(self, name):
        """
        Searches in all `LocalGroup` instances for the `PyLeihe.bibliography.Bibliography`
        with the name and returns the first one.

        Arguments:
            name (str): name of the bib to search for

        Returns:
            * `PyLeihe.bibliography.Bibliography` first search result
            * `None` if no one was found
        """
        for l in self.Laender:
            b = l[name]
            if b is not None:
                return b
        return None

    def reprJSON(self):
        """
        function returns a representation of the instance from JSON compliant data types
        (lists and dictionaries).

        For contained instances of other classes,
        their respective conversion functions are called.
        """
        return {l.name: l.reprJSON() for l in self.Laender}

    @classmethod
    def loadFromJSON(cls, data=None, filename=""):
        """
        Converts a typical json representation consisting of lists and dicts into an instance.

        For contained instances of other classes,
        their respective conversion functions are called.

        If no data is passed, the `_loadJSONFile` with the filename parameter will be used.

        Arguments:
            data (dict): _optional_ the representation as dict and lists
            filename (str): _optional_ the path to the json file containing the data
        """
        pln = PyLeiheNet()
        if data is None:
            data = cls._loadJSONFile(filename)
        pln.Laender = [LocalGroup.loadFromJSON(
            ldata) for ldata in data.values()]
        return pln

    def loadallBundesLaender(self, groupbytitle=True, loadsearchURLs=False):
        """
        Loads the federal states and the addresses of the corresponding libraries from the Internet.

        Arguments:
            groupbytitle (bool): if true calls `LocalGroup.groupbytitle()`
            loadsearchURLs (bool): if true calls `LocalGroup.loadsearchURLs()`
        """
        if not self.Laender:
            self.getBundesLaender()

        for land in self.Laender:
            land.loadBibURLs()
            if loadsearchURLs:
                land.loadsearchURLs()
            if groupbytitle:
                land.groupbytitle()

    def getBundesLaender(self):
        """
        Loads the federal states and their urls from the Internet.
        """
        # load data from internet
        germany = self.getURL(self.URL_Deutschland)
        r = self.simpleGET(germany)
        # analyze html
        soup = BeautifulSoup(r.content, features="html.parser")
        areas = soup.find_all('area', attrs={'alt': 'Zum Wunschformular'})
        unique_urls = {a['href'] for a in areas}
        self.Laender = [LocalGroup.from_url(a) for a in unique_urls]
