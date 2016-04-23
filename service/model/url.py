from itertools import chain
import urlparse

from google.appengine.ext import ndb
from google.appengine.ext.ndb.key import _MAX_KEYPART_BYTES

from google.appengine.api.app_identity import app_identity

from gapplib import strutil
from model_error import DestinationUrlError

MAX_URL_LENGTH = 2048
QUERY_CHUNKS = 4
MAX_QUERY_LENGTH = QUERY_CHUNKS * _MAX_KEYPART_BYTES

DEFAULT_URL_SCHEME = 'http'
DEFAULT_PATH = '/'
DEFAULT_QUERY = '#'

ALLOWED_SCHEMES = {'http', 'https', 'ftp', 'ftps', 'mailto', 'mms', 'rtmp', 'rtmpt', 'ed2k', 'pop', 'imap', 'nntp',
                   'news', 'ldap', 'dict', 'dns'}

LOCALHOSTS = {'localhost', '127.0.0.1'}


class NormalizedUrl(urlparse.SplitResult):

    def __new__(cls, scheme=None, netloc=None, path=None, query=None):
        return super(NormalizedUrl, cls).__new__(cls, scheme, netloc, path, query, None)

    def __init__(self, scheme=None, netloc=None, path=None, query=None):
        super(NormalizedUrl, self).__init__(scheme, netloc, path, query, None)

    def query_segments(self):
        # key empty query on '?'
        if not self.query:
            yield DEFAULT_QUERY
        else:
            for chunk in strutil.chunk(self.query, _MAX_KEYPART_BYTES):
                yield chunk


class DestinationUrl(ndb.Model):
    """
    Model for reprensenting a destination url and its relationship to its short url
    """
    query = ndb.StringProperty(indexed=True)
    short_key = ndb.KeyProperty(kind='ShortUrl')

    @classmethod
    def construct(cls, url):
        """
        Initializes an instance of LongUrl for the purposes of operating on the datastore

        Args:
            url:

        Returns:

        """
        # normalize url
        normal = cls.normalize_url(url)

        # construct a key for the kind in the hierarchy which corresponds to url
        kee = cls._construct_key(normal)

        # construct a model
        du = DestinationUrl(key=kee)
        return du

    @classmethod
    def get_by_url(cls, url):
        """
        Initializes an instance of LongUrl for the purposes of operating on the datastore

        Args:
            url:

        Returns:

        """
        normal = cls.normalize_url(url)
        return cls._construct_key(normal).get()

    @classmethod
    def normalize_url(cls, val):
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

        if len(original.netloc) > _MAX_KEYPART_BYTES:
            raise DestinationUrlError(
                DestinationUrlError.NETLOC_TOO_LONG, max_len=_MAX_KEYPART_BYTES)
        elif len(original.path) > _MAX_KEYPART_BYTES:
            raise DestinationUrlError(
                DestinationUrlError.PATH_TOO_LONG, max_len=_MAX_KEYPART_BYTES)
        elif len(original.query) > MAX_QUERY_LENGTH:
            raise DestinationUrlError(
                DestinationUrlError.QUERY_TOO_LONG, max_len=MAX_QUERY_LENGTH)

        return NormalizedUrl(
            scheme=coerced_scheme,
            netloc=original.netloc,
            path=original.path,
            query=original.query
        )

    @classmethod
    def _hierarchy_path(cls, normalized_url):
        """
        Generates a list of entity ids which describes a path in the url name space
        Args:
            normalized_url(NormalizedUrl): a parsed representation of the original url
               which contains normalized components of an original url

        Returns:

        """
        yield 'Scheme'
        yield normalized_url.scheme
        yield 'Netloc'
        yield normalized_url.netloc
        yield 'Path'
        yield normalized_url.path if normalized_url.path else DEFAULT_PATH

        seg_count = 0
        for query_seg in normalized_url.query_segments():
            yield ''.join([
                'Query',
                ''.join(['Ext', str(seg_count) if seg_count else ''])
            ])
            yield query_seg

    @classmethod
    def _construct_key(cls, normalized_url):
        """
        Returns ndb key which describes a path to a DestinationUrl in the url 'space' hierarchy.
        The last path segment of the returned key is always of kind cls.__name__ (i.e. DestinationUrl)

        Args:
            normalized_url(NormalizedUrl): a parsed representation of the original url
               which contains normalized components of an original url

        Returns:
            ndb.Key:

        """
        path = [arg for arg in cls._hierarchy_path(normalized_url)]
        path[-2] = cls.__name__

        return ndb.Key(*path)


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
    return urlparse.urlunsplit(DestinationUrl.normalize_url(val))


class ShortUrl(ndb.Model):
    """A main model for representing a url entry."""
    short_id = ndb.StringProperty(indexed=True)
    url = ndb.BlobProperty(indexed=False, validator=validate_dest_url)
    date = ndb.DateTimeProperty(auto_now_add=True)


