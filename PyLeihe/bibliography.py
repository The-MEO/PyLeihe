# -*- coding: utf-8 -*-
"""
Contains the `Bibliography` class definition to abstract one library.
Also contains the enumeration for the diferent mediatypes.
"""
from enum import Enum
import re
import logging
import urllib.parse as up

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
            url (str): URL to the website of the library with search field
            cities (list[str]): list of city names that are included in the
                library association
            session (requests.session): set some session settings for
                customized search
        """
        super().__init__(session)
        if not url:
            url = "NoURL"
        if "http//" in url:
            logging.info("removed wrong 'http//' from '%s'", url)
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
    def loadFromJSON(cls, data=None, filename=None):
        """
        Generates a new instance based on JSON data.

        Arguments:
            data: _optional_ parsed json as dict with json comaptible
                python objects
                *if None* `_loadJSONFile` is called and data is loaded from disk
            filename (str): _optional_ the path to the json file containing the data

        Returns:
            new instance
        """
        if data is None:
            data = cls._loadJSONFile(filename)
        bib = Bibliography(data["url"], cities=data["cities"])
        bib.search_url = data["search_url"]
        return bib

    @classmethod
    def _grepSearchURL_PostFormURL(cls, mp):
        """
        Searches a html page for the link-url to an search.

        Arguments:
            mp (requests.Response): to search in

        Returns:
            str: with the destination url of the form
        """
        return cls.getPostFormURL(
            mp.content,
            curr_url=mp.url,
            ContNode="input", ContNodeData={"id": "searchtext"})

    def _grepSearchURL_extendedSearch(self, mp):
        """
        Searches a html page for the link-url to an advanced search.

        Arguments:
            mp (requests.Response): to search in

        Returns:
            `None` if no url was found
            else `str` with the result url
        """
        a_search = self.searchNodeMultipleContain(
            mp.content, "a", {'title': 'Erweiterte Suche'})
        if a_search is not None:
            logging.debug("extendedSearch hit")
            return a_search.get('href')
        logging.debug("extendedSearch no match")
        return None

    def _grepSearchURL_href_secondSearch(self, mp):
        """
        Searches for the address of the search form by following the link.

        First the link to the search page is searched.
        This url is opened with the session and the address of the
        search endpoint (post target) is extracted from the page there.

        Arguments:
            mp (requets.Respons): opened website to search

        Returns:
            * `None` if no url was found
            * else `str` with the result url
        """
        url = None
        a_search = self.searchNodeMultipleContain(mp.content, "a", mp.url)
        if a_search is not None:
            logging.debug("secondSearch hit")
            try_second_search = a_search.get('href')
            mp = self.simpleGET(try_second_search)
            url = self._grepSearchURL_PostFormURL(mp)
        else:
            logging.debug("secondSearch no match")
        return url

    def _grepSearchURL_simplelink(self, mp):
        """
        Searches for a adress to the domain `onleihe.de`.

        Arguments:
            mp (requets.Respons): opened website to search

        Returns:
            * `None` if no url was found
            * else `str` with the result url
        """
        url = None
        a_search = self.searchNodeMultipleContain(
            mp.content, "a", {"href": re.compile(r'.*onleihe[^\/]*\.de.*')})
        if a_search is not None:
            try_second_search = a_search.get('href')
            mp = self.simpleGET(try_second_search)
            url = self._grepSearchURL_PostFormURL(mp)
        return url

    def _grepSearchURL_loadData(self):
        """
        Loads the website from the library and returns the Response.

        For further informations see: `PyLeiheWeb.simpleGET`

        Returns:
            * `None` if the data could not be loaded
            * else `requets.Response` with the page content in
                `requets.Response.content`
        """
        return self.simpleGET(self.url)

    def grepSearchURL(self, lvl=1):
        """
        Searches the library website for the endpoint (post target) of the
        search form.

        1. Loads the content of the website
        2. trys different methods to extract the post target
            1. [LVL0] searches input field with id for simple search
            2. [LVL1] searches for a link to `onleihe.de`
            3. [LVL2] searches for advanced search
            4. [LVL2] searches link to different search page
        3. *stores the result in* `search_url`

        Arguments:
            lvl (int): specifies the number of additional search methods.

        Returns:
            bool: status whether a post target url was found.

        """
        mp = self._grepSearchURL_loadData()
        if mp is None:
            return False
        self.search_url = self._grepSearchURL_PostFormURL(mp)
        if self.search_url is None and lvl >= 1:
            logging.info("[%s] No search form found on the start page", str(self))
            self.search_url = self._grepSearchURL_simplelink(mp)
        if self.search_url is None and lvl >= 2:
            self.search_url = self._grepSearchURL_extendedSearch(mp)
        if self.search_url is None and lvl >= 2:
            self.search_url = self._grepSearchURL_href_secondSearch(mp)
        if self.search_url is None:
            logging.warning("[%s] No search-URL could be found on '%s' ",
                            str(self), mp.url)
            return False
        return True

    def SetSearchResultsPerPage(self, amount: int = 100, search_result_page=None):
        """
        Changes the amount of results per page on the server side.

        Arguments:
            amount (int): _optional_  maximum Amount of results on one page
            search_result_page (requests.Response): _optional_  result page from
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
                * -1 if regex failed
                * int: number of results
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

    def _postSearchParse(self, cmd_id, text: str, kategorie: MediaType, savefile=False):
        """
        Executes a http request to the web search to the library.

        Arguments:
            cmd_id (int): Parameter for the search method: `703` for simple and
                `701`for extended search
            text (str): keyword to search for
            kategorie (MediaType, optional):  the media category to be searched
            savefile (bool, optional): if the result page of the search should
                be stored on the local disc. The file name is taken from the
                title of the library.
        Returns:
            None: if ConnectionError occurs, see `PyLeiheWeb.simpleSession`
            int: number of results, see `Bibliography.parse_results`
            -1: result could not be parsed
        """
        SearchRequest = self.simpleSession(self.search_url,
                                           data={'pMediaType': kategorie.value,
                                                 'pText': text,
                                                 "Suchen": "Suche",
                                                 "cmdId": cmd_id,
                                                 'sk': 1000,
                                                 'pPageLimit': 100})
        if SearchRequest is None:
            return None
        Treffer = self.parse_results(SearchRequest)
        if savefile or (Treffer == -1 and logging.getLogger().isEnabledFor(logging.DEBUG)):
            f = open("{0}_{1}.html".format(self.title, cmd_id), 'wb')
            f.write(SearchRequest.content)
            f.close()
        return Treffer

    def search(self, text: str, kategorie: MediaType = None, savefile=False):
        """
        Performs a search query to a library.

        Arguments:
            text (str): keyword to search for
            kategorie (MediaType, optional):  the media category to be searched
            savefile (bool, optional): if the result page of the search should
                be stored on the local disc. The file name is taken from the
                title of the library.

        Returns:
            int: number of results or negative for error codes:
            - `-1` regex failed
            - `-2`
            - `-3` no search url available
            - `-4` ConnectionError
        """
        if kategorie is None:
            kategorie = MediaType.alleMedien
        # get MainPage
        if self.search_url is None:
            self.grepSearchURL()
        if self.search_url is None:
            logging.info("[%s][search: %s] No search_url available", self, text)
            return -3

        Treffer = self._postSearchParse(703, text, kategorie, savefile)
        if Treffer is None:
            return -4
        if Treffer == -1:
            logging.info("[%s][search: %s] regex for result counting failed."
                         "Try second methode with cmdId for extended search",
                         self, text)

            Treffer = self._postSearchParse(701, text, kategorie, savefile)

        self.LastSearch = Treffer
        return Treffer
