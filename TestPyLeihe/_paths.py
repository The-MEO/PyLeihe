"""
Adds path to the source code to the PATH-Variable,
otherwise the tests cannot import the functions to be tested.
"""
import sys
import os
DIR = os.path.dirname(__file__)
sys.path.append(os.path.join(DIR, ".."))
