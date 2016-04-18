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

        logging.info('HOSTURL %s' % handler.host_url())

        short_id = kwargs.get('sid', None)
        if short_id:
            logging.info('got short id: (%s)' % short_id)
            logging.info('short id class: (%s)' % short_id.__class__)

            service_url = handler.module_path('default', [ 'shorturl', short_id ])
            logging.info("## default service url ### %s #####" % service_url)

            result = urlfetch.fetch(service_url, follow_redirects=False)
            if result.status_code == httplib.OK:
                payload = json.loads(result.content)
                url = payload.get('url').encode('utf-8')
                short_url = payload.get('short_url').encode('utf-8')
            elif result.status_code >= httplib.BAD_REQUEST:
                logging.error("response content: (%s)" % result.content)
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

        logging.info('template: %s' % template_values)

        template = app.JINJA_ENVIRONMENT.get_template('content/index.html')
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

            # shortening service currently runs as part of same app
            service_url = handler.module_path('default', 'shorturl')
            logging.info("## default service url ### %s #####" % service_url)

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
            self.redirect('/' + short_id)
        else:
            parms = {
                'message': message,
                'url': longurl
            }
            self.redirect('/?' + urllib.urlencode(parms))

