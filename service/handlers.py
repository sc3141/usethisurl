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
                payload = {
                    'iri': short_url.iri,
                    'url': short_url.url,
                    'short_url': handler.host_path(sid)
                }
                self.response.write(json.dumps(payload))
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
        iri = self._extract_post_url()
        if iri:
            self._post_url(iri)

    def _extract_post_url(self):
        """
        Extracts/Validates url from json payload
        Returns:

        """
        payload_iri = None
        try:
            payload = json.loads(unicode(self.request.body))
            payload_iri = payload.get('url')
            if not payload_iri:
                handler.write_and_log_error(self.response, httplib.BAD_REQUEST, 'empty url')
        except ValueError as e:
            handler.write_error(self.response, httplib.BAD_REQUEST, e.message)
        except TypeError as e:
            handler.write_error(self.response, httplib.BAD_REQUEST, e.message)
        except StandardError as e:
            logging.exception('service POST %s' % self.request.path)
            handler.write_and_log_error(self.response, httplib.INTERNAL_SERVER_ERROR, e.message)

        return payload_iri


    def _post_url(self, iri):
        try:
            short_url_key = None
            dest_iri = model.url.DestinationIri.get_by_iri(iri)
            if dest_iri:
                short_url_key = dest_iri.short_key
                if not short_url_key:
                    handler.write_and_log_error(self.response, httplib.CONFLICT)
            else:
                # a short url has not been created for this destination url - create it
                dest_iri = model.url.DestinationIri.construct(iri)
                dk = dest_iri.put()
                if dk:
                    # create a short url and associate it with destination
                    short_url = model.url.ShortUrl()
                    short_url.iri = iri
                    short_url_key = short_url.put()
                    if short_url_key:
                        dest_iri.short_key = short_url_key

                        # i contemplated making this an async operation, however ...
                        # ... the first simple test did not work properly ...
                        # as if the entity was stuck waiting for the write to complete
                        dest_iri.put()

            if short_url_key:
                sid = model.short_id.encode(short_url_key.id())
                logging.info('created short id (%s) for url (%s)' % (sid, strutil.ellipsicate(iri, 128)))

                self.response.set_status(httplib.CREATED)
                self.response.write(json.dumps({'short_id': sid}))
                self.response.headers.add_header('Content-Type', 'application/json')
                self.response.headers.add_header('Location', os.path.join(handler.host_url(), sid))
            else:
                message = u'Failed to create short url for iri (%s)' % strutil.ellipsicate(iri, 128)
                handler.write_and_log_error(self.response, httplib.INSUFFICIENT_STORAGE, message=message)
        except ModelError as e:
            handler.write_and_log_error(self.response, httplib.BAD_REQUEST, e.message)
        except StandardError as e:
            logging.exception('service POST %s' % self.request.path)
            handler.write_and_log_error(self.response, httplib.INTERNAL_SERVER_ERROR, e.message)

class Maintenance(webapp2.RequestHandler):
    """
    Responds with message regarding 'system down for maintenance'
    """

    def get(self, *args, **kwargs):
        self.response.set_status(httplib.SERVICE_UNAVAILABLE, message='')
        self.response.out.write('System is down for maintenance')

    def post(self, *args, **kwargs):
        self.response.set_status(httplib.SERVICE_UNAVAILABLE, message='')
        self.response.out.write('System is down for maintenance')

