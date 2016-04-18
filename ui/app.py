import os

import jinja2
import webapp2

from handlers import MainPage, SubmitUrl

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

SUBMIT_URL_ID = 'submit_url'
SUBMIT_URL_PATH = '/' + SUBMIT_URL_ID

instance = webapp2.WSGIApplication([
    (SUBMIT_URL_PATH, SubmitUrl),
    webapp2.Route('/<sid:.*>', MainPage),
], debug=True)
