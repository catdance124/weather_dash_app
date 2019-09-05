#!/virtual/catdance124/.pyenv/shims/python
# coding: utf-8

from flask import Flask
import sys
sys.path.append('../')
from get_weather_data import load_new_data
import os
os.chdir('../')

app = Flask(__name__)

@app.route('/')
def index():
    load_new_data()
    return 'LOAD DATA'

if __name__ == '__main__':
    app.run()