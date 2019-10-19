"""
This module provides basic functions for the use of the package.
Most of the functions are used for the command line interface in `__main__.py`
"""
from multiprocessing.dummy import Pool
from . import PyLeiheNet


def correct_search_urls(PyLN):
    """
    Performs the searchurl correction (see `correct_searchurls_land`)
    for all libraries of the contained (federal) states

    Arguments:
        PyLN: `PyLeiheNet` containing the countries to be corrected
    """
    for land in PyLN.Laender:
        correct_searchurls_land(land)


def correct_searchurls_land(land):
    """
    Correct some special searchurls for all Bibs in one `BundesLand`

    Some libraries of alliances use different URLs.
    This function is intended to merge outliers that are not automatically detected.
    The list of corrections was created manually and
    will need maintenance in the future if the URLs change.

    Argument:
        land: `BundesLand` with libraries with search_urls to be corrected
    """
    # pylint: disable=line-too-long
    if land["libell-e"] is not None:
        if land.name in ("Badenwuerttemberg", "Rheinlandpfalz"):
            land["libell-e"].search_url = "https://www2.onleihe.de/libell-e-sued/frontend/search,0-0-0-0-0-0-0-0-0-0-0.html"  # noqa: E501
        else:
            land["libell-e"].search_url = "https://www2.onleihe.de/libell-e-nord/frontend/search,0-0-0-0-0-0-0-0-0-0-0.html"  # noqa: E501
    if land.name == "Badenwuerttemberg":
        land.fix_searchurl("meine-medienwelt", "https://www1.onleihe.de/heilbronn/frontend/search,0-0-0-0-0-0-0-0-0-0-0.html")  # noqa: E501
        remove_baden = land["baden"]
        if remove_baden is not None:
            land.Bibliotheken.remove(remove_baden)
    elif land.name == "Sachsen":
        land.fix_searchurl("grossenhain", "https://www2.onleihe.de/bibo-on/frontend/search,0-0-0-0-0-0-0-0-0-0-0.html")  # noqa: E501
    elif land.name == "Schleswigholstein":
        land.fix_searchurl("amt-buechen", "https://www2.onleihe.de/bibo-on/frontend/search,0-0-0-0-0-0-0-0-0-0-0.html")  # noqa: E501
    elif land.name == "Nordrheinwestfalen":
        land.fix_searchurl("stadtdo", "https://www2.onleihe.de/dortmund/frontend/search,0-0-0-0-0-0-0-0-0-0-0.html")  # noqa: E501
    elif land.name == "Sachsenanhalt":
        land.fix_searchurl("Sangerhausen", "https://biblio24.onleihe.de/verbund_sachsen_anhalt/frontend/welcome,51-0-0-100-0-0-1-0-0-0-0.html")  # noqa: E501
    elif land.name == "Berlin":
        land.fix_searchurl("voebb24", "https://voebb.onleihe.de/berlin/frontend/search,0-0-0-0-0-0-0-0-0-0-0.html")  # noqa: E501
    # pylint: enable=line-too-long


def makejson(reload_data=False, filename=""):
    """
    The aim of the function is to create a json file with all preprocessed data.

    Arguments:
        reload_data: `bool` specifies whether the data should be loaded
                    fresh from the website or from a local file.
        filename: `str` path to the json file
            from which the json data is imported if `reload_data` is `False`
    Returns:
        the saved `PyLeiheNet` instance
    """
    if reload_data:
        print("Lade Bundeslaender")
        PyLeiheNet.getBundesLaender()
        print("Lade Bibliotheken der Bundeslaender")
        PyLeiheNet.loadallBundesLaender(groupbytitle=True, loadsearchURLs=False)
    else:
        PyLeiheNet.loadFromJSON(filename)
    print("SearchURLs manuell ergänzen")
    correct_search_urls(PyLeiheNet)
    print("SearchURLslLaden")
    for land in PyLeiheNet.Laender:
        land.loadsearchURLs(newtitle=True)
    print("Neues Gruppieren mit SearchURL")
    for land in PyLeiheNet.Laender:
        land.groupbytitle()
    print("Speichere JSON")
    PyLeiheNet.toJSONFile()


def parallel_search_helper(search="", category=None):
    """
    Help function that creates the search function when using multiple threads.

    Arguments:
        search: `str` optional keyword to search for
                which is passed to `Bibliography.search()`
        search: `MediaType` optional media categorie to search for
                which is passed to `Bibliography.search()`

    Return:
        Function `run` which can be called
    """
    def run(bib):
        """
        Performs the search in the specified library.

        Arguments:
            bib: the library to be searched

        Return:
            Tuple with the library and the return value from the search.
            see `Bibliography.search()`
        """
        return (bib, bib.search(search, category))
    return run


def search_list(search="", category=None, use_json=True, jsonfile='', threads=4):
    """

    Arguments:
        search: `str` keyword to search for in all PyLeiheNet
        category: `MediaType`
        use_json: `bool` whether pre-processed local data from a json file
                  of countries and libraries should be used
                  or everything should be downloaded on-the-fly from the Internet
        jsonfile: `str` path to json file (used for `use_json = True`)
        threads: `int` number of concurrent threads to be used for searching
    """
    if use_json:
        PyLeiheNet.loadFromJSON(jsonfile)
    else:
        PyLeiheNet.getBundesLaender()
        PyLeiheNet.loadallBundesLaender(groupbytitle=True, loadsearchURLs=False)
    bibs = [b for l in PyLeiheNet.Laender for b in l.Bibliotheken]
    results = []
    if threads > 0:
        workpool = Pool(threads)
        search_run = parallel_search_helper(search, category)
        results = workpool.map(search_run, bibs)
        # close the pool and wait for the work to finish
        workpool.close()
        workpool.join()
    else:
        results = [(bib, bib.search(search, category)) for bib in bibs]
    return results


def search_print(top=10, *args, **kwargs):  # pylint: disable=keyword-arg-before-vararg
    """
    Simple function to search and output the results in the console.

    Tasks:
        1. start `search_list`
        2. sort results
        3. print the first `top` results to the console

    Arguments:
        top: `int` optional limitation of the number of results (<1 for unlimited)
        args: passed to `search_list`
        kwargs: passed to `search_list`
    """
    results = search_list(*args, **kwargs)
    results.sort(key=lambda x: x[1] if x is not None else -5, reverse=True)
    for i, r in enumerate(results):
        if i > top and top > 0:
            break
        b = r[0]
        title = b.title or "NA"
        ls = b.LastSearch or -128
        print("{1:2d} {0:25}\t".format(title, r[1]), end='')
        if len(b.cities) < 5:
            print(','.join(b.cities))
        else:
            print(','.join(b.cities[:5]))
