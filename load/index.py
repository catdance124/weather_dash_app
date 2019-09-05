#!/virtual/catdance124/.pyenv/shims/python
# coding: utf-8

import cgitb
cgitb.enable()

from wsgiref.handlers import CGIHandler
from server import app
CGIHandler().run(app)