import urlparse
import webapp2

from google.appengine.api.app_identity import app_identity

from handlers import ShortenUrl

HOSTNAME = app_identity.get_default_version_hostname()
HOSTURL = urlparse.urlunsplit(('http', HOSTNAME, '', '', ''))

SERVICE_ID = 'shorturl'
SERVICE_PATH = '/' + SERVICE_ID

instance = webapp2.WSGIApplication([
    (SERVICE_PATH, ShortenUrl),
], debug=True)
