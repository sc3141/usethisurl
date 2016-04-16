import os
import logging
import urllib
import urlparse
import json
import httplib

from google.appengine.ext import ndb
from google.appengine.api import urlfetch
from google.appengine.api.app_identity import app_identity

import jinja2
import webapp2

import id_encoding
import string_util
import handler_util

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
MAX_URL_LENGTH = 4096

def create_short_id_map(*args):
    """
    Produces a dictionary of shortids which are keyed by id

    Args:
        *args: an iterable sequence of valid short ids

    Returns:
        dict: a dictionary of ids each mapped to the corresponding short-id

    """
    m = dict()

    for v in args:
        k = id_encoding.decode(v)
        if (k < 0):
            raise ValueError(id_encoding.decode_error_description(k))
        m[k] = v

    return m

RESERVED_SHORT_ID = id_encoding.create_short_id_map(SERVICE_ID, SUBMIT_URL_ID)

class ShortUrl(ndb.Model):
    """A main model for representing a url entry."""
    short_id= ndb.StringProperty(indexed=True)
    url = ndb.BlobProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)

class MainPage(webapp2.RequestHandler):
    def get(self):
        url = ''
        short_url = ''
        message = ''

        logging.info('HOSTURL %s' % HOSTURL)

        short_id = self.request.get('short_id')
        if short_id:
            logging.info('got short id: (%s)' % short_id)
            logging.info('short id class: (%s)' % short_id.__class__)
            id = id_encoding.decode(short_id)
            if id < 0:
                message = id_encoding.decode_error_description(id)
                logging.error('PROBLEM: %s' % message)
            else:
                short_url = os.path.join(HOSTURL, short_id)
                if id in RESERVED_SHORT_ID:
                    logging.info('id reserved')
                    url = short_url
                else:
                    logging.info('id not reserved')
                    result = ShortUrl.get_by_id(id)
                    if result:
                        url = result.url
                    else:
                        message = 'No short url registered to that id'
                        short_url = ''
        else:
            message = self.request.get('message', '')
            url = self.request.get('url', '')

        template_values = {
            'submit_path': SUBMIT_URL_PATH,
            'url': url,
            'short_url': short_url,
            'message': message,
        }

        logging.info('template: %s' % template_values)

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))

class SubmitUrl(webapp2.RequestHandler):

    def post(self):
        logging.info('UI request(%s)' % self.request)
        logging.info('host_url(%s)' % self.request.host_url)
        short_id = ''
        message = ''

        longurl = self.request.get('url')
        if longurl:
            logging.info('UI request to shorten (%s)' % longurl)
            payload = { 'url': longurl }

            # shortening service currently runs as part of same app
            service_url = os.path.join(self.request.host_url, SERVICE_ID)
            logging.info('service path %s' % service_url)

            result = urlfetch.fetch(service_url,
                        payload=json.dumps({ 'url': longurl}),
                        method=urlfetch.POST,
                        headers = {'Content-Type': 'application/json'},
                        follow_redirects=False)

            logging.info('service result %d' % result.status_code)

            if result.status_code == httplib.CREATED or \
                result.status_code == httplib.OK:
                payload = json.loads(result.content)
                short_id = payload.get('short_id').encode('utf-8')
            elif result.status_code >= httplib.BAD_REQUEST:
                logging.error("response content: (%s)" % result.content)
                message = result.content

        if short_id:
            self.redirect('/?' + urllib.urlencode({'short_id': short_id}))
        else:
            parms = {
                'message': message,
                'url': longurl
            }
            self.redirect('/?' + urllib.urlencode(parms))

class ShortenUrl(webapp2.RequestHandler):

    def _extract_post_url(self):
        """
        Extracts/Validates url from json payload
        Returns:

        """

        valid_url = None

        try:
            payload = json.loads(self.request.body)
            url = payload.get('url')
            if not url:
                handler_util.set_status(self.response, httplib.BAD_REQUEST, 'empty url')
            elif len(url) > MAX_URL_LENGTH:
                message='url exceeds maximum allowed length (%d)' % MAX_URL_LENGTH
                handler_util.set_status(self.response, httplib.REQUEST_ENTITY_TOO_LARGE, message)
            else:
                logging.info('url type %s' % url.__class__)
                valid_url = url.encode('utf-8')
        except ValueError as e:
            handler_util.set_status(self.response, httplib.BAD_REQUEST, e.message)
        except TypeError as e:
            handler_util.set_status(self.response, httplib.BAD_REQUEST, e.message)
        except StandardError as e:
            handler_util.set_status(self.response, httplib.INTERNAL_SERVER_ERROR, e.message)

        return valid_url

    def _post_url(self, url):
        try:
            short_url = ShortUrl()
            short_url.url = url
            key = short_url.put()

            if key:
                raise ValueError('key.id type: %s' % key.id().__class__)
                short_id = id_encoding.encode(key.id())
                logging.info('created short id (%s) for url (%s)' % (short_id, string_util.truncate(url, 128)))

                self.response.set_status(httplib.CREATED)
                self.response.write(json.dumps( {'short_id': short_id }))
                self.response.headers.add_header('Content-Type', 'application/json')
                self.response.headers.add_header('Location', os.path.join(HOSTURL, short_id))
            else:
                message = 'Failed to create short url for url (%s)' % string_util.truncate(url, 128)
                self.response.set_status(httplib.INSUFFICIENT_STORAGE, message=message)
                logging.error(message)

        except StandardError as e:
            handler_util.set_status(self.response, httplib.INTERNAL_SERVER_ERROR, e.message)

    def post(self):
        logging.info('SHORTEN: (%s)' % self.request.body)
        logging.info('request  (%s)' % self.request)

        url = self._extract_post_url()
        if url:
            self._post_url(url)


app = webapp2.WSGIApplication([
    ('/', MainPage),
    (SUBMIT_URL_PATH, SubmitUrl),
    (SERVICE_PATH, ShortenUrl),
], debug=True)
