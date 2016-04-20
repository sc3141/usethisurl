from collections import namedtuple
from itertools import chain
import urlparse
import logging

from google.appengine.ext import ndb
from google.appengine.api.app_identity import app_identity

from model_error import DestinationUrlError

MAX_URL_LENGTH = 2048

DEFAULT_URL_SCHEME = 'http'
DEFAULT_PATH = '/'
DEFAULT_QUERY = '?'

ALLOWED_SCHEMES = {'http', 'https', 'ftp', 'ftps', 'mailto', 'mms', 'rtmp', 'rtmpt', 'ed2k', 'pop', 'imap', 'nntp',
                   'news', 'ldap', 'dict', 'dns'}

LOCALHOSTS = {'localhost', '127.0.0.1'}

NormalizedUrl = namedtuple('NormalizedUrl', ['scheme', 'netloc', 'path', 'query'])

class DestinationUrl(ndb.Model):
    """
    Model for reprensenting a destination url and its relationship to its short url
    """
    query = ndb.StringProperty(indexed=True)
    short_key = ndb.KeyProperty(kind='ShortUrl')

    @classmethod
    def _construct_parent_key(cls, normalized_url_parts):
        """

        Args:
            normalized_url_parts(NormalizedUrl): a parsed representation of the original url
               which contains normalized components of an original url

        Returns:
            ndb.Key:

        """
        return ndb.Key(
            'UrlScheme', normalized_url_parts.scheme,
            'UrlNetloc', normalized_url_parts.netloc,
            'UrlPath', normalized_url_parts.path if normalized_url_parts.path else DEFAULT_PATH)

    @classmethod
    def construct(cls, url):
        """
        Initializes an instance of LongUrl for the purposes of operating on the datastore

        Args:
            url:

        Returns:

        """
        normal = cls.normalize_dest_url(url)
        lu = DestinationUrl(
            parent=cls._construct_parent_key(normal),
            id = normal.query if normal.query else DEFAULT_QUERY)
        return lu

    @classmethod
    def get_by_url(cls, url):
        """
        Initializes an instance of LongUrl for the purposes of operating on the datastore

        Args:
            url:

        Returns:

        """
        normal = cls.normalize_dest_url(url)
        return DestinationUrl.get_by_id(
            parent=cls._construct_parent_key(normal),
            id = normal.query if normal.query else DEFAULT_QUERY)


    @classmethod
    def normalize_dest_url(cls, val):
        """
        Coerces url to standard allowable form, stripping fragment and rejecting certain conditions
        which are not allowed due to such things as ambiguous destinations or security considerations.

        Validates/Coerces a proposed url based upon the constraints of model which are:

           Scheme:
              If url has not scheme, it is assigned 'http'. Certain scehes are not allowed. In particular, data:
              and javascript:.

           Host:
              references to local machine are not allowed in production mode. Thus the model will
              disallow 'localhost', '127.0.0.1'. Relative urls (i.e. empty host) are also not allowed.

        Validation only pertains to logical qualities related to the datamodel. The validation
        includes checks for neither white space nor valid characters

        Args:
            val (str): string representation of a url. string must contain only valid url characters

        Returns:
            urlparse.SplitResult

        Raises:
            ModelConstraintError if and constraints regarding destination urls are violated
        """

        if len(val) > MAX_URL_LENGTH:
            raise DestinationUrlError(DestinationUrlError.URL_TOO_LONG, max_len=MAX_URL_LENGTH)

        original = urlparse.urlsplit(val)
        if not original.netloc:
            if val.startswith(original.scheme):
                raise DestinationUrlError(DestinationUrlError.RELATIVE_URL_NOT_ALLOWED)
            else:
                raise DestinationUrlError(DestinationUrlError.HOST_OMITTED)

        if not original.hostname or original.hostname in LOCALHOSTS:
            raise DestinationUrlError(DestinationUrlError.LOCALHOST_NOT_ALLOWED)
        elif -1 != original.hostname.find(app_identity.get_default_version_hostname()):
            raise DestinationUrlError(DestinationUrlError.RECURSIVE_REDIRECTION_ALLOWED)

        if original.scheme:
            if original.scheme not in ALLOWED_SCHEMES:
                raise DestinationUrlError(DestinationUrlError.SCHEME_NOT_ALLOWED, original.scheme)
        coerced_scheme = original.scheme if original.scheme else DEFAULT_URL_SCHEME

        return NormalizedUrl(
            scheme=coerced_scheme,
            netloc=original.netloc,
            path=original.path,
            query=original.query)


def validate_dest_url(url_prop, val):
    """
    Validator function for use with ndb

    Args:
        url_prop: the datastore property which will hold the value of the url
        val: the url to be stored

    Returns:
        str: if the url was coerced into a normalized form
        None: if the url was not coerced

    Raises:
        ModelConstraintError if and constraints regarding destination urls are violated
    """
    return urlparse.urlunsplit(chain(DestinationUrl.normalize_dest_url(val), (None,)))


class ShortUrl(ndb.Model):
    """A main model for representing a url entry."""
    short_id= ndb.StringProperty(indexed=True)
    url = ndb.BlobProperty(indexed=False, validator=validate_dest_url)
    date = ndb.DateTimeProperty(auto_now_add=True)


