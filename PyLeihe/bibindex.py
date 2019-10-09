# -*- coding: utf-8 -*-
from collections import defaultdict
import re
import requests
from bs4 import BeautifulSoup

from .basic import PyLeiheWeb
from .bibliography import Bibliography


class BundesLand(PyLeiheWeb):
    BASIC_URL = "index.php?id={}"

    Bibliotheken = []

    def __init__(self, lid, name):
        super().__init__()
        self.lid = int(lid)
        self.name = name.capitalize()

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.Bibliotheken[key]
        for x in self.Bibliotheken:
            if x.title.lower() == key.lower():
                return x
        return None

    def loadBibURLs(self):
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
        for bib in self.Bibliotheken:
            if force or bib.search_url is None:
                bib.grapSearchURL()
            if newtitle:
                bib.generateTitle()

    def fix_searchurl(self, bib, url):
        bib = self[bib]
        if bib is not None:
            bib.search_url = url

    @classmethod
    def from_url(cls, url):
        m = re.search(r"id=(\d+)#([a-zA-Z]+)", url)
        if m is not None:
            return BundesLand(m.group(1), m.group(2))
        raise ValueError(url)

    def __repr__(self):
        return "{}({:>2d}, {})".format(self.__class__.__name__, self.lid, self.name)

    def groupbytitle(self):
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
    URL_Deutschland = "fuer-leser-hoerer-zuschauer/ihre-onleihe-finden/onleihen-in-deutschland.html"

    Laender = []

    def __init__(self):
        super().__init__()

    def __getitem__(self, key):
        for x in self.Laender:
            if x.lid == key or (isinstance(key, str) and x.name.lower() == key.lower()):
                return x

    @classmethod
    def reprJSON(cls):
        return {l.name: l.reprJSON() for l in cls.Laender}

    @classmethod
    def loadFromJSON(cls, filename=""):
        data = cls._loadJSONFile(filename)
        cls.Laender = [BundesLand.loadFromJSON(
            ldata) for ldata in data.values()]

    @classmethod
    def loadallBundesLaender(cls, groupbytitle=True, loadsearchURLs=False):
        if not cls.Laender:
            cls.getBundesLaender()

        for land in cls.Laender:
            land.loadBibURLs()
            if loadsearchURLs:
                land.loadsearchURLs()
            if groupbytitle:
                land.groupbytitle()

    @classmethod
    def getBundesLaender(cls):
        # load data from internet
        germany = PyLeiheNet.getURL(PyLeiheNet.URL_Deutschland)
        r = requests.get(germany)
        r.raise_for_status()
        # analyze html
        soup = BeautifulSoup(r.content, features="html.parser")
        areas = soup.find_all('area', attrs={'alt': 'Zum Wunschformular'})
        cls.Laender = [BundesLand.from_url(a['href']) for a in areas]
