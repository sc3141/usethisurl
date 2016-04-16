import logging
import httplib
import json
import webapp2

import model
from model import short_id

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
            elif len(url) > model.MAX_URL_LENGTH:
                message='url exceeds maximum allowed length (%d)' % model.MAX_URL_LENGTH
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
            short_url = model.ShortUrl()
            short_url.url = url
            key = short_url.put()

            if key:
                raise ValueError('key.id type: %s' % key.id().__class__)
                sid = short_id.encode(key.id())
                logging.info('created short id (%s) for url (%s)' % (sid, string_util.truncate(url, 128)))

                self.response.set_status(httplib.CREATED)
                self.response.write(json.dumps( {'short_id': sid }))
                self.response.headers.add_header('Content-Type', 'application/json')
                self.response.headers.add_header('Location', os.path.join(HOSTURL, sid))
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


