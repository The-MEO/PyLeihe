"""
"""
from multiprocessing.dummy import Pool
from . import PyLeiheNet


def correct_search_urls(PyLN):
    for land in PyLN.Laender:
        correct_searchurls_land(land)


def correct_searchurls_land(land):
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
    def run(bib):
        return (bib, bib.search(search, category))
    return run


def search_list(search="", category=None, use_json=True, jsonfile='', threads=4):
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
