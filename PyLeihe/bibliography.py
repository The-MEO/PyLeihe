# -*- coding: utf-8 -*-
"""
Contains the `Bibliography` class definition to abstract one library.
Also contains the enumeration for the diferent mediatypes.
"""
from enum import Enum
import re
import urllib.parse as up
import requests

from .basic import PyLeiheWeb


class MediaType(Enum):
    """
    Represents the different media types and
    their corresponding html value.
    """
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
    """
    Abstraction of one or more libraries and their bibliographie
    """

    def __init__(self, url, cities=None, session=None):
        """
        Arguments:
            url: `str` URL to the website of the library with search field
            cities: `list[str]` list of city names that are included in the
                library association
            session: `requests.session` set some session settings for
                customized search
        """
        super().__init__(session)
        if not url:
            url = "NoURL"
        if "http//" in url:
            url = url.replace("http//", "")
        self.url_up = url
        self.url = up.urlparse(url)
        self.cities = cities or []

        self.search_url = None
        self.LastSearch = -255
        self.SuchVersion = None

        self.title = ""
        self.generateTitle()

    def _generateTitleByUrl(self, url):
        """
        Generates a meaningful title `self.title` based on the url.

        The URL usually contains a name of the representative library
        association.
        This can be extracted with simple methods and used for later output

        Arguments:
            url: `str` or `urllib.parse.ParseResult` URL to the website of the
                library.

        """
        if isinstance(url, str):
            url = up.urlparse(url)
        spath = url.path.split('/')
        self.title = url.netloc
        domains = url.netloc.split('.')
        if len(domains) >= 2 and domains[-2] != 'onleihe':
            self.title = domains[-2]
        elif len(url.path) >= 3 and len(spath) > 1:
            self.title = spath[1]
        elif len(self.cities) > 0:
            self.title = self.cities[0]
            if len(self.cities) > 1:
                self.title += "..."

    def generateTitle(self):
        """
        Calls the corresponding subfunction to generate a new title.

        The called function depends on whether a search url has already been
        found or not.
        """
        if self.search_url is None:
            self._generateTitleByUrl(self.url)
        else:
            self._generateTitleByUrl(self.search_url)

    def __repr__(self):
        return "{}({!r}, {})".format(self.__class__.__name__,
                                     self.title,
                                     self.url_up)

    def reprJSON(self):
        """
        Creates a JSON compatible representation of the instance.

        Returns:
            json compatible representation `dict[str->json compatible object]`.
        """
        jdict = {
            "name": self.title,
            "url": self.url_up,
            "search_url": self.search_url,
            "cities": self.cities
        }
        return jdict

    @classmethod
    def loadFromJSON(cls, data=None):
        """
        Generates a new instance based on JSON data.

        Arguments:
            data: _optional_ parsed json as dict with json comaptible
                python objects
                *if None* `_loadJSONFile` is called and data is loaded from disk

        Returns:
            new instance
        """
        if data is None:
            data = cls._loadJSONFile()
        bib = Bibliography(data["url"], cities=data["cities"])
        bib.search_url = data["search_url"]
        return bib

    def _grapSearchURL_extendedSearch(self, mp):
        """
        Searches a html page for the link-url to an advanced search.

        Arguments:
            mp: `requests.Response` to search in

        Returns:
            `None` if no url was found
            else `str` with the result url
        """
        a_search = self.searchNodeMultipleContain(
            mp.content, "a", {'title': 'Erweiterte Suche'})
        if a_search is not None:
            return a_search.get('href')
        return None

    def _grapSearchURL_href_secondSearch(self, mp):
        """
        Searches for the address of the search form by following the link.

        First the link to the search page is searched.
        This url is opened with the session and the address of the
        search endpoint (post target) is extracted from the page there.

        Returns:
            * `None` if no url was found
            * else `str` with the result url
        """
        url = None
        a_search = self.searchNodeMultipleContain(mp.content, "a", mp.url)
        if a_search is not None:
            try_second_search = a_search.get('href')
            mp = self.Session.get(try_second_search)
            mp.raise_for_status()
            url = self.getPostFormURL(
                mp.content,
                curr_url=mp.url,
                ContNode="input", ContNodeData={"id": "searchtext"})
        return url

    def _grapSearchURL_loadData(self):
        """
        Loads the website from the library and returns the Response.

        Returns:
            * `None` if the data could not be loaded
            * else `requets.Respons` with the page content in
                `requets.Respons.content`

        Raises:
            see `requets.Response.raise_for_status` except:
                * [Errno 11004] getaddrinfo failed
                * [Errno -2] Name or service not known
                * [Errno 8] nodename nor servname
        """
        mp = None
        try:
            mp = self.Session.get(up.urlunparse(self.url))
            mp.raise_for_status()
        except requests.ConnectionError as exc:
            message = str(exc)
            if ("[Errno 11004] getaddrinfo failed" in message or
                    "[Errno -2] Name or service not known" in message or
                    "[Errno 8] nodename nor servname " in message):
                return None
            raise
        return mp

    def grapSearchURL(self):
        """
        Searches the library website for the endpoint (post target) of the
        search form.

        1. Loads the content of the website
        2. trys different methods to extract the post target
            1. searches input field with id for simple search
            2. searches for advanced search
            3. searches link to different search page
        3. stores the result in `search_url`
        """
        mp = self._grapSearchURL_loadData()
        if mp is None:
            return
        self.search_url = self.getPostFormURL(
            mp.content, curr_url=mp.url,
            ContNode="input", ContNodeData={"id": "searchtext"})
        if self.search_url is None:
            self.search_url = self._grapSearchURL_extendedSearch(mp)
        if self.search_url is None:
            self.search_url = self._grapSearchURL_href_secondSearch(mp)
        if self.search_url is None:
            print("No search-URL could be found for "
                  + self.title + " on: " + mp.url)

    def SetSearchResultsPerPage(self, amount: int = 100, search_result_page=None):
        """
        Changes the amount of results per page on the server side.

        Arguments:
            amount: _optional_ `int` maximum Amount of results on one page
            search_result_page: _optional_ `requests.Response` result page from
                one page where the amount can be set.
                The changed number is than stored in the session on server side.

        Returns:
            `requests.Response` Response from the post-command.
        """
        if search_result_page is not None:
            set_results_url = self.getPostFormURL(
                search_result_page.content,
                curr_url=search_result_page.url,
                ContNode="select", ContNodeData={"id": "elementsPerPage"})
        set_page = self.Session.post(set_results_url, data={
            'elementsPerPage': amount})
        set_page.raise_for_status()
        return set_page

    @staticmethod
    def parse_results(SearchRequest):
        """
        Extracts the number of search results from the result page

        Arguments:
            SearchRequest: `requests.Response` the result page of a search

        Returns:
            `int` number of results
            -1 if regex failed
        """
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
        """
        Performs a search query to a library.

        Arguments:
            text: `str` keyword to search for
            kategorie: _optional_ `MediaType` the media category to be searched
            savefile: _optional_ `bool` if the result page of the search should
                be stored on the local disc. The file name is taken from the
                title of the library.

        Returns:
            `int` number of results
        """
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
        # print("[{0}] Treffer: {1}".format(self.title, Treffer))
        return Treffer
