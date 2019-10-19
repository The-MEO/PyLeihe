# PyLeihe

Python module to search in all German online libraries that work with the software `Onleihe`.

## Installation

1.  To use the module including command line interface you need [python3](https://www.python.org/downloads/).  
    _For the later call it is easiest if python is included in the path variable._
2.  clone or download this repository
3.  open your preferred console program in the downloaded project folder
4.  Install the required dependencies
        python -m pip install -r requirements.txt
    If you want to develop the source code further, there are some interesting tools (like `pytest`) in requirements_tools.txt
5.  Start the command line program and display the corresponding help text:
        ```shell
        python -m PyLeihe -h
        ``` 

## Tools

## Documentation

### Command-Line usage

It is assumed that the terminal is open in the project folder.
The module can then be executed with the following command:

```shell
python3 -m PyLeihe
```

1.  An overview of all possible options can be displayed with the following parameter: 
    ```shell
    python3 -m PyLeihe --help
    ```
2.  To avoid having to retrieve relatively static data every time you search,
    it is recommended that you save it locally. 
    For this purpose the module provides the possibility to load it and save it as a JSON file.
    ```shell
    python3 -m PyLeihe --loadonline --makejson 
    ```
3.  The actual search can then be performed with the following call:

    ```shell
    python3 -m PyLeihe -s "SEARCH TERM"
    ```

    For more specific searches, additional options can be used. For example:

    -   books only: `-category eBook`
    -   displays only the first 10 libraries, descending Sorted by number of hits: `-t 10`
    -   eight threads are used in parallel for the search (default is 4): `--threads 8`

    Results in th following call:

    ```shell
    python3 -m PyLeihe -s "SEARCH TERM" -c eBook -t 10 --threads 8
    ```

### Code Example

How the individual classes can be used together can be found in the functions from `simple_functions.py`.

### Code Documentation

The source code documentation was created automatically with [pdoc3](https://pdoc3.github.io/pdoc/).
To rebuild the documentation you can either run `pdoc` manually or start the package with the option `python3 -m PyLeihe --make`. 
