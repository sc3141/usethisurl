import os
import urlparse

import jinja2
import webapp2

from google.appengine.api.app_identity import app_identity

from handlers import MainPage, SubmitUrl

HOSTNAME = app_identity.get_default_version_hostname()
HOSTURL = urlparse.urlunsplit(('http', HOSTNAME, '', '', ''))

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

SERVICE_ID = 'short'
SERVICE_PATH = '/' + SERVICE_ID
SUBMIT_URL_ID = 'ui'
SUBMIT_URL_PATH = '/' + SUBMIT_URL_ID

instance = webapp2.WSGIApplication([
    ('/', MainPage),
    (SUBMIT_URL_PATH, SubmitUrl),
], debug=True)
