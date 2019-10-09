# -*- coding: utf-8 -*-
from enum import Enum
import re
import urllib.parse as up
import requests

from .basic import PyLeiheWeb


class MediaType(Enum):
    alleMedien = -1
    eAudio = 400002
    eBook = 400001
    eLearning = 400013
    eMagazine = 400005
    eMusic = 400003
    ePaper = 400006
    ePub = 400008
    eVideo = 400004

    def __str__(self):
        return self.name


class Bibliography(PyLeiheWeb):
    def __init__(self, url, cities=None, session=None):
        super().__init__(session)
        if "http//" in url:
            url = url.replace("http//", "")
        self.url_up = url
        self.url = up.urlparse(url)
        self.cities = cities or ['']

        self.search_url = None
        self.LastSearch = -255
        self.SuchVersion = None

        self.title = ""
        self.generateTitle()

    def _generateTitleByUrl(self, url):
        if isinstance(url, str):
            url = up.urlparse(url)
        spath = url.path.split('/')
        self.title = url.netloc
        server = url.netloc.split('.')[-2]
        if server != 'onleihe':
            self.title = server
        elif len(url.path) >= 3 and len(spath) > 1:
            self.title = spath[1]
        elif self.cities[0] != '':
            self.title = self.cities[0]
            if len(self.cities) > 1:
                self.title += "..."

    def generateTitle(self):
        if self.search_url is None:
            self._generateTitleByUrl(self.url)
        else:
            self._generateTitleByUrl(self.search_url)

    def __repr__(self):
        return "{}({!r}, {})".format(self.__class__.__name__, self.title, up.urlunparse(self.url))

    def reprJSON(self):
        jdict = {
            "name": self.title,
            "url": up.urlunparse(self.url),
            "search_url": self.search_url,
            "cities": self.cities
        }
        return jdict

    @classmethod
    def loadFromJSON(cls, data=None):
        if data is None:
            data = cls._loadJSONFile()
        bib = Bibliography(data["url"], cities=data["cities"])
        bib.search_url = data["search_url"]
        return bib

    def grapSearchURL(self):
        try:
            mp = self.Session.get(up.urlunparse(self.url))
            mp.raise_for_status()
        except requests.ConnectionError as exc:
            message = str(exc)
            if "[Errno 11004] getaddrinfo failed" in message or "[Errno -2] Name or service not known" in message or "[Errno 8] nodename nor servname " in message:
                return
            else:
                raise
        self.search_url = self.getPostFormURL(
            mp.content, curr_url=mp.url, ContNode="input", ContNodeData={"id": "searchtext"})
        if self.search_url is None:
            a_search = self.searchNodeMultipleContain(
                mp.content, "a", {'title': 'Erweiterte Suche'})
            if a_search is not None:
                self.search_url = a_search.get('href')
        if self.search_url is None:
            a_search = self.searchNodeMultipleContain(mp.content, "a", mp.url)
            if a_search is not None:
                try_second_search = a_search.get('href')
                mp = self.Session.get(try_second_search)
                mp.raise_for_status()
                self.search_url = self.getPostFormURL(
                    mp.content,
                    curr_url=mp.url,
                    ContNode="input", ContNodeData={"id": "searchtext"})
        if self.search_url is None:
            print("No search-URL could be found for "
                  + self.title + " on: " + mp.url)

    def SetSearchResultsPerPage(self, amount: int = 100, search_result_page=None):
        if search_result_page is not None:
            set_results_url = self.getPostFormURL(
                search_result_page.content,
                curr_url=search_result_page.url,
                ContNode="select", ContNodeData={"id": "elementsPerPage"})
        set_page = self.Session.post(set_results_url, data={
            'elementsPerPage': amount})
        set_page.raise_for_status()
        return set_page

    def parse_results(self, SearchRequest):
        m = re.search(
            r"Suchergebnis .* ([\d.]+|keine)[^0-9.]*[Tt]reffer.*", SearchRequest.text)
        Treffer = -1
        if m is not None:
            if m.group(1) == "keine":
                Treffer = 0
            else:
                Treffer = int(m.group(1).replace(".", ""))
        return Treffer

    def search(self, text: str, kategorie: MediaType = None, savefile=False):
        if kategorie is None:
            kategorie = MediaType.alleMedien
        # get MainPage
        if self.search_url is None:
            self.grapSearchURL()
        if self.search_url is None:
            return -3
        try:
            SearchRequest = self.Session.post(self.search_url,
                                              data={'pMediaType': kategorie.value,
                                                    'pText': text,
                                                    "Suchen": "Suche",
                                                    "cmdId": 703,
                                                    'sk': 1000,
                                                    'pPageLimit': 100})
            SearchRequest.raise_for_status()
            Treffer = self.parse_results(SearchRequest)
        except requests.exceptions.ConnectionError:
            return -4

        if Treffer == -1:
            SearchRequest = self.Session.post(self.search_url,
                                              data={'pMediaType': kategorie.value,
                                                    'pText': text,
                                                    "Suchen": "Suchen",
                                                    "cmdId": 701,
                                                    'sk': 1000,
                                                    'pPageLimit': 100})
            Treffer = self.parse_results(SearchRequest)
            # print(self.title + ": Suchen")

        self.LastSearch = Treffer
        if savefile:
            f = open(self.title + ".html", 'wb')
            f.write(SearchRequest.content)
            f.close()
        #print("[{0}] Treffer: {1}".format(self.title, Treffer))
        return Treffer
