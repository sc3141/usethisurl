import httplib
import json
import logging
import os
import webapp2

import model
from model.model_error import DecodeError, ModelError

from gapplib import handler, strutil


class RedirectUrl(webapp2.RequestHandler):

    def get(self, **kwargs):
        logging.info('############################################')
        sid = kwargs.get('sid', None)
        if not sid:
            ui_url = handler.module_url('ui')
            logging.info("## ui ### %s #####" % ui_url)
            self.redirect(ui_url)
        else:
            try:
                kid = model.short_id.decode(sid)
                short_url = model.ShortUrl().get_by_id(kid)
                if short_url:
                    logging.info('sid: redirecting')
                    self.redirect(short_url.url)
                else:
                    logging.error("sid %s: kid %d: not found" % (sid, kid))
                    handler.render_error(self.response, httplib.NOT_FOUND, handler.host_path(sid))
            except DecodeError as e:
                handler.render_and_log_error(self.response, httplib.BAD_REQUEST, e.message)
            except StandardError as e:
                handler.render_and_log_error(self.response, httplib.INTERNAL_SERVER_ERROR, e.message)


class QueryUrl(webapp2.RequestHandler):

    def get(self, **kwargs):
        sid = kwargs.get('sid', None)
        if not sid:
            handler.render_error(self.response, httplib.BAD_REQUEST, 'empty or missing reference to short url')
        else:
            logging.info("GET on QueryUrl (%s)" % sid)
            self._get_url(sid)

    def _get_url(self, sid):
        try:
            kid = model.short_id.decode(sid)
            short_url = model.ShortUrl().get_by_id(kid)
            if short_url:
                self.response.set_status(httplib.OK)
                self.response.write(json.dumps( {'url': short_url.url, 'short_url': handler.host_path(sid) }))
                self.response.headers.add_header('Content-Type', 'application/json')
                logging.info("query succeeded: sid==%s" % sid)
            else:
                message="no corresponding short url: short id '%s'" % sid
                handler.write_and_log_error(self.response, httplib.NOT_FOUND, message=message)

        except DecodeError as e:
            handler.write_and_log_error(self.response, httplib.BAD_REQUEST, message=e.message)
        except StandardError as e:
            handler.write_and_log_error(self.response, httplib.INTERNAL_SERVER_ERROR, e.message)


class ShortenUrl(webapp2.RequestHandler):

    def post(self):
        logging.info('SHORTEN: (%s)' % self.request.body)
        logging.info('request  (%s)' % self.request)

        url = self._extract_post_url()
        if url:
            self._post_url(url)

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
                handler.write_and_log_error(self.response, httplib.BAD_REQUEST, 'empty url')
            elif len(url) > model.MAX_URL_LENGTH:
                message='url exceeds maximum allowed length (%d)' % model.MAX_URL_LENGTH
                handler.write_and_log_error(self.response, httplib.REQUEST_ENTITY_TOO_LARGE, message)
            else:
                logging.info('url type %s' % url.__class__)
                valid_url = url.encode('utf-8')
        except ValueError as e:
            handler.write_error(self.response, httplib.BAD_REQUEST, e.message)
        except TypeError as e:
            handler.write_error(self.response, httplib.BAD_REQUEST, e.message)
        except StandardError as e:
            handler.write_and_log_error(self.response, httplib.INTERNAL_SERVER_ERROR, e.message)

        return valid_url

    def _post_url(self, url):
        try:
            key = None
            long_url = model.url.LongUrl.get_by_url(url)
            if long_url:
                key = long_url.short_key
                if not key:
                    handler.write_and_log_error(self.response, httplib.CONFLICT)
            else:
                long_url = model.url.LongUrl.construct(url)
                lk = long_url.put()
                if lk:
                    short_url = model.url.ShortUrl()
                    short_url.url = url
                    key = short_url.put()
                    if key:
                        long_url.short_key = key

                        # i contemplated making this an async operation, however ...
                        # ... the first simple test did not work properly ...
                        # as if the entity was stuck waiting for the write to complete
                        long_url.put()

            if key:
                sid = model.short_id.encode(key.id())
                logging.info('created short id (%s) for url (%s)' % (sid, strutil.truncate(url, 128)))

                self.response.set_status(httplib.CREATED)
                self.response.write(json.dumps( {'short_id': sid }))
                self.response.headers.add_header('Content-Type', 'application/json')
                self.response.headers.add_header('Location', os.path.join(handler.host_url(), sid))
            else:
                message = 'Failed to create short url for url (%s)' % strutil.truncate(url, 128)
                handler.write_and_log_error(self.response, httplib.INSUFFICIENT_STORAGE, message=message)
        except ModelError as e:
            handler.write_and_log_error(self.response, httplib.BAD_REQUEST, e.message)
        except StandardError as e:
            handler.write_and_log_error(self.response, httplib.INTERNAL_SERVER_ERROR, e.message)
