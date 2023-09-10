import os

file_path = os.path.abspath(__file__).split('run.py')[0]

# go to the file path address
os.chdir(file_path)

from src.initialize import *

