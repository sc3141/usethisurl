import httplib
import json
import logging
import os
import webapp2

import model
from model.model_error import DecodeError, ModelError

from gapplib import handler, strutil, urlutil


class RedirectUrl(webapp2.RequestHandler):
    """
    Issues redirect to destination url
    """

    def get(self, **kwargs):
        sid = kwargs.get('sid', None)
        # if no short id is specified, redirect to main page of the ui
        if not sid:
            ui_url = handler.module_url('ui')
            self.redirect(ui_url)
        else:
            try:
                # convert the short_id into an ndb integer id
                # and retrieve the short url
                kid = model.short_id.decode(sid)
                short_url = model.ShortUrl().get_by_id(kid)
                if short_url:
                    self.redirect(short_url.url)
                else:
                    logging.error("sid %s: kid %d: not found" % (sid, kid))
                    handler.render_error(self.response, httplib.NOT_FOUND, handler.host_path(sid))
            except DecodeError as e:
                handler.render_and_log_error(self.response, httplib.BAD_REQUEST, e.message)
            except StandardError as e:
                logging.exception('service GET %s' % self.request.path)
                handler.render_and_log_error(self.response, httplib.INTERNAL_SERVER_ERROR, e.message)


class QueryUrl(webapp2.RequestHandler):
    """
    Handles requests to get destination url without redirection
    """

    def get(self, **kwargs):
        sid = kwargs.get('sid', None)
        if not sid:
            handler.render_error(self.response, httplib.BAD_REQUEST, 'empty or missing reference to short url')
        else:
            self._get_url(sid)

    def _get_url(self, sid):
        try:
            kid = model.short_id.decode(sid)
            short_url = model.ShortUrl().get_by_id(kid)
            if short_url:
                self.response.set_status(httplib.OK)
                self.response.write(json.dumps({'url': short_url.url, 'short_url': handler.host_path(sid)}))
                self.response.headers.add_header('Content-Type', 'application/json')
                logging.info("query succeeded: sid==%s" % sid)
            else:
                message = "no corresponding short url: short id '%s'" % sid
                handler.write_and_log_error(self.response, httplib.NOT_FOUND, message=message)

        except DecodeError as e:
            handler.write_and_log_error(self.response, httplib.BAD_REQUEST, message=e.message)
        except StandardError as e:
            logging.exception('service GET %s' % self.request.path)
            handler.write_and_log_error(self.response, httplib.INTERNAL_SERVER_ERROR, e.message)


class ShortenUrl(webapp2.RequestHandler):
    """
    Creates a short url which corresponsds to a destination url.  If destination url has already
    been assigned a short url, a reference to the existing is returned.
    """

    def post(self):
        url = self._extract_post_url()
        if url:
            self._post_url(url)

    def _extract_post_url(self):
        """
        Extracts/Validates url from json payload
        Returns:

        """
        payload_url = None
        valid_url = None

        try:
            payload = json.loads(self.request.body)
            payload_url = payload.get('url')
            if not payload_url:
                handler.write_and_log_error(self.response, httplib.BAD_REQUEST, 'empty url')
            else:
                ascii_url = payload_url.encode('ascii')
                urlutil.validate_url(ascii_url)
                valid_url = ascii_url
        except UnicodeDecodeError as e:
            message = 'unconvertible unicode character {\\x{:0>04X}} in url: offset {:d}: {url:.{trunc}<HERE>}'.format(
                ord(payload_url[e.start]), e.start, url=payload_url, trunc=e.start)
            handler.write_error(self.response, httplib.BAD_REQUEST, message)
        except ValueError as e:
            handler.write_error(self.response, httplib.BAD_REQUEST, e.message)
        except TypeError as e:
            handler.write_error(self.response, httplib.BAD_REQUEST, e.message)
        except StandardError as e:
            logging.exception('service POST %s' % self.request.path)
            handler.write_and_log_error(self.response, httplib.INTERNAL_SERVER_ERROR, e.message)

        return valid_url

    def _post_url(self, url):
        try:
            short_url_key = None
            dest_url = model.url.DestinationUrl.get_by_url(url)
            if dest_url:
                short_url_key = dest_url.short_key
                if not short_url_key:
                    handler.write_and_log_error(self.response, httplib.CONFLICT)
            else:
                # a short url has not been created for this destination url - create it
                dest_url = model.url.DestinationUrl.construct(url)
                dk = dest_url.put()
                if dk:
                    # create a short url and associate it with destination
                    short_url = model.url.ShortUrl()
                    short_url.url = url
                    short_url_key = short_url.put()
                    if short_url_key:
                        dest_url.short_key = short_url_key

                        # i contemplated making this an async operation, however ...
                        # ... the first simple test did not work properly ...
                        # as if the entity was stuck waiting for the write to complete
                        dest_url.put()

            if short_url_key:
                sid = model.short_id.encode(short_url_key.id())
                logging.info('created short id (%s) for url (%s)' % (sid, strutil.ellipsicate(url, 128)))

                self.response.set_status(httplib.CREATED)
                self.response.write(json.dumps({'short_id': sid}))
                self.response.headers.add_header('Content-Type', 'application/json')
                self.response.headers.add_header('Location', os.path.join(handler.host_url(), sid))
            else:
                message = 'Failed to create short url for url (%s)' % strutil.ellipsicate(url, 128)
                handler.write_and_log_error(self.response, httplib.INSUFFICIENT_STORAGE, message=message)
        except ModelError as e:
            handler.write_and_log_error(self.response, httplib.BAD_REQUEST, e.message)
        except StandardError as e:
            logging.exception('service POST %s' % self.request.path)
            handler.write_and_log_error(self.response, httplib.INTERNAL_SERVER_ERROR, e.message)
