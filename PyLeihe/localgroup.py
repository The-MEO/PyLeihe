# -*- coding: utf-8 -*-
"""
ContaiDefines object representation of local libraries and bibliographies groups.
"""
import logging
from collections import defaultdict
import re
from bs4 import BeautifulSoup
from .basic import PyLeiheWeb
from .bibliography import Bibliography


class LocalGroup(PyLeiheWeb):
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
        uebersicht = self.getURL(self.BASIC_URL.format(self.lid))
        r = self.simpleGET(uebersicht)
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

        For additional information see: `Bibliography.grepSearchURL()`

        Arguments:
            newtitle (bool): _optional_ whether new title names are to be
                generated on the basis of the new available data
        """
        for bib in self.Bibliotheken:
            if force or bib.search_url is None:
                bib.grepSearchURL()
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
            return LocalGroup(m.group(1), m.group(2))
        logging.error("Can't create LocalGroup from url: '%s'", url)
        raise ValueError(url)

    def __repr__(self):
        return "{}({:>2d}, {})".format(self.__class__.__name__, self.lid, self.name)

    def groupbytitle(self):
        """
        Merges multiple list objects (`PyLeihe.bibliography.Bibliography`) by the same title name.

        This method is case insensitive.
        """
        dict_title = defaultdict(list)
        for bib in self.Bibliotheken:
            dict_title[bib.title.lower()].append(bib)
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
    def loadFromJSON(cls, data=None, filename=None):
        if data is None:
            data = cls._loadJSONFile(filename)
        bl = LocalGroup(data["id"], data["name"])
        bl.Bibliotheken = [Bibliography.loadFromJSON(
            b) for b in data["bibliotheken"].values()]
        return bl
