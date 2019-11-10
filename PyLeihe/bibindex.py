# -*- coding: utf-8 -*-
"""
Contains container objects to group the libraries and bibliographies logically
"""
from collections import defaultdict
import re
import logging
import requests
from bs4 import BeautifulSoup

from .basic import PyLeiheWeb
from .bibliography import Bibliography


class BundesLand(PyLeiheWeb):
    """
    Object to group bibliographies `PyLeihe.bibliography.Bibliography` (into their federal states).

    In addition to the functions for grouping, the class provides an
    abstraction of the individual federal states.
    So they can be load with their corresponding `PyLeihe.bibliography.Bibliography`.

    """
    BASIC_URL = "index.php?id={}"

    def __init__(self, lid, name, bibs=None):
        """
        Arguments:
            lid: to `int`convertable object, as unique ID
            name (str): name of the group (federal state)
            bibs (list[bibliography]): _optional_ the initial elements of
                the group
        """
        super().__init__()
        self.lid = int(lid)
        self.name = name.capitalize().replace(' ', '_')
        self.Bibliotheken = bibs or []

    def __getitem__(self, key):
        """
        Returns the object corresponding to the `key` or
            `None` if there exists none.

        Arguments:
            key:
                * `int` with element index
                * `str` name of the `PyLeihe.bibliography.Bibliography` _case insensitive_
        """
        if isinstance(key, (int, slice)):
            return self.Bibliotheken[key]
        for x in self.Bibliotheken:
            if x.title.lower() == key.lower():
                return x
        return None

    def loadBibURLs(self):
        """
        Loads all `PyLeihe.bibliography.Bibliography`s from the website of the federal state.

        **Warning**
        Overrides the internal list with objects.
        """
        uebersicht = PyLeiheNet.getURL(self.BASIC_URL.format(self.lid))
        r = requests.get(uebersicht)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, features="html.parser")
        links = soup.find('table', {"class": "contenttable"}).find_all(
            'a', attrs={'target': '_blank'})
        workBibs = {}
        for a in links:
            try:
                key = a['href']
                if key in workBibs:
                    workBibs[key].append(a.get_text())
                else:
                    workBibs[key] = [a.get_text()]
            except Exception as e:
                raise type(e)(
                    str(e) + ' happens at [{}]:{}'.format(self.name, a))

        self.Bibliotheken = [Bibliography(k, v) for k, v in workBibs.items()]

    def loadsearchURLs(self, newtitle=False, force=False):
        """
        Loads all search urls for the containing elements.

        For additional information see: `Bibliography.grapSearchURL()`

        Arguments:
            newtitle (bool): _optional_ whether new title names are to be
                generated on the basis of the new available data
        """
        for bib in self.Bibliotheken:
            if force or bib.search_url is None:
                bib.grapSearchURL()
            if newtitle:
                bib.generateTitle()

    def fix_searchurl(self, key, url):
        """
        Sets a new search url for a library with the `key` if possible.
        """
        bib = self[key]
        if bib is not None:
            bib.search_url = url

    @classmethod
    def from_url(cls, url):
        """
        Creates a new instance from a url.

        Arguments:
            url (str): in the format `...id=ID#Name...`

        Raises:
            ValueError: if the URL did not fulfill the search condition.
        """
        m = re.search(r"id=(\d+)#([a-zA-Z]+)", url)
        if m is not None:
            return BundesLand(m.group(1), m.group(2))
        logging.error("Can't create BundesLand from url: '%s'", url)
        raise ValueError(url)

    def __repr__(self):
        return "{}({:>2d}, {})".format(self.__class__.__name__, self.lid, self.name)

    def groupbytitle(self):
        """
        Merges multiple list objects (`PyLeihe.bibliography.Bibliography`) by the same title name.
        """
        dict_title = defaultdict(list)
        for bib in self.Bibliotheken:
            dict_title[bib.title].append(bib)
        grouped_bibs = []
        for group in dict_title.values():
            grouped_bibs.append(group[0])
            if len(group) > 1:
                remain_bib = group[0]
                for b in group[1:]:
                    remain_bib.cities.extend(b.cities)

        self.Bibliotheken = grouped_bibs

    def reprJSON(self):
        return {"name": self.name,
                "id": self.lid,
                "bibliotheken": {b.title: b.reprJSON() for b in self.Bibliotheken}}

    @classmethod
    def loadFromJSON(cls, data=None):
        if data is None:
            data = cls._loadJSONFile()
        bl = BundesLand(data["id"], data["name"])
        bl.Bibliotheken = [Bibliography.loadFromJSON(
            b) for b in data["bibliotheken"].values()]
        return bl


class PyLeiheNet(PyLeiheWeb):
    """
    Group Object for multiple `BundesLand` instances.
    """
    URL_Deutschland = "fuer-leser-hoerer-zuschauer/ihre-onleihe-finden/onleihen-in-deutschland.html"

    def __init__(self):
        super().__init__()
        self.Laender = []

    def __getitem__(self, key):
        """
        Returns the `BundesLand` belonging to the `key` or `None`.

        Arguments:
            key:
                * `int` the id of the requested `BundesLand`
                * `str` the name of the requested `BundesLand`
                    _case insensitive_
        """
        for x in self.Laender:
            if x.lid == key or (isinstance(key, str) and x.name.lower() == key.lower()):
                return x
        return None

    def getBib(self, name):
        """
        Searches in all `BundesLand` instances for the `PyLeihe.bibliography.Bibliography`
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
        pln.Laender = [BundesLand.loadFromJSON(
            ldata) for ldata in data.values()]
        return pln

    def loadallBundesLaender(self, groupbytitle=True, loadsearchURLs=False):
        """
        Loads the federal states and the addresses of the corresponding libraries from the Internet.

        Arguments:
            groupbytitle (bool): if true calls `BundesLand.groupbytitle()`
            loadsearchURLs (bool): if true calls `BundesLand.loadsearchURLs()`
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
        germany = PyLeiheNet.getURL(PyLeiheNet.URL_Deutschland)
        r = requests.get(germany)
        r.raise_for_status()
        # analyze html
        soup = BeautifulSoup(r.content, features="html.parser")
        areas = soup.find_all('area', attrs={'alt': 'Zum Wunschformular'})
        self.Laender = [BundesLand.from_url(a['href']) for a in areas]
