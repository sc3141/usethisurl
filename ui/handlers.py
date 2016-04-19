import httplib
import json
import logging
import urllib

import webapp2

from google.appengine.api import urlfetch

import app
from gapplib import handler

class MainPage(webapp2.RequestHandler):
    def get(self, **kwargs):
        url = ''
        short_url = ''
        message = ''

        short_id = kwargs.get('sid', None)
        if short_id:
            service_url = handler.module_path('default', [ 'shorturl', short_id ])

            result = urlfetch.fetch(service_url, follow_redirects=False)
            if result.status_code == httplib.OK:
                payload = json.loads(result.content)
                url = payload.get('url').encode('utf-8')
                short_url = payload.get('short_url').encode('utf-8')
            elif result.status_code >= httplib.BAD_REQUEST:
                logging.error("status %d: %s" % (result.status_code, result.content))
                message = result.content
        else:
            message = self.request.get('message', '')
            url = self.request.get('url', '')

        template_values = {
            'submit_path': app.SUBMIT_URL_PATH,
            'url': url,
            'short_url': short_url,
            'message': message,
        }

        template = app.JINJA_ENVIRONMENT.get_template('content/index.html')
        self.response.write(template.render(template_values))

class SubmitUrl(webapp2.RequestHandler):

    def post(self):
        short_id = ''
        message = ''

        dest_url = self.request.get('url')
        if dest_url:
            logging.info('UI request to shorten (%s)' % dest_url)

            # shortening service currently runs as part of same app
            service_url = handler.module_path('default', 'shorturl')
            result = urlfetch.fetch(service_url,
                        payload=json.dumps({ 'url': dest_url}),
                        method=urlfetch.POST,
                        headers = {'Content-Type': 'application/json'},
                        follow_redirects=False)

            if result.status_code == httplib.CREATED or \
                result.status_code == httplib.OK:
                payload = json.loads(result.content)
                short_id = payload.get('short_id').encode('utf-8')
                logging.info("status %d: %s" % (result.status_code, result.content))
            elif result.status_code >= httplib.BAD_REQUEST:
                logging.error("status %d: %s" % (result.status_code, result.content))
                message = result.content

        if short_id:
            self.redirect('/' + short_id)
        else:
            parms = {
                'message': message,
                'url': dest_url
            }
            self.redirect('/?' + urllib.urlencode(parms))

