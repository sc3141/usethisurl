import httplib
import json
import logging
import os
import urllib

import webapp2

from google.appengine.api import urlfetch

from app import JINJA_ENVIRONMENT, HOSTURL, SUBMIT_URL_PATH

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

