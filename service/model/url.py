import urlparse

from google.appengine.ext import ndb
from google.appengine.ext.ndb.key import _MAX_KEYPART_BYTES

from google.appengine.api.app_identity import app_identity

from gapplib import strutil
from gapplib import urlutil
from model_error import DestinationUrlError

MAX_IRI_LENGTH = 2048
"""Maximum allowable length of a url for which shortening has been requested. the url must be an IRI"""

QUERY_CHUNKS = 4
MAX_QUERY_LENGTH = QUERY_CHUNKS * _MAX_KEYPART_BYTES

DEFAULT_IRI_SCHEME = 'http'
DEFAULT_PATH = '/'
DEFAULT_QUERY = '#'

ALLOWED_SCHEMES = {'http', 'https', 'ftp', 'ftps', 'mailto', 'mms', 'rtmp', 'rtmpt', 'ed2k', 'pop', 'imap', 'nntp',
                   'news', 'ldap', 'dict', 'dns'}

LOCALHOSTS = {'localhost', '127.0.0.1'}


class NormalizedIri(urlparse.SplitResult):

    def __new__(cls, scheme=None, netloc=None, path=None, query=None):
        return super(NormalizedIri, cls).__new__(cls, scheme, netloc, path, query, None)

    def __init__(self, scheme=None, netloc=None, path=None, query=None):
        super(NormalizedIri, self).__init__(scheme, netloc, path, query, None)

    def query_segments(self):
        # key empty query on '?'
        if not self.query:
            yield DEFAULT_QUERY
        else:
            for chunk in strutil.chunk(self.query, _MAX_KEYPART_BYTES):
                yield chunk


class DestinationIri(ndb.Model):
    """
    Model for reprensenting a destination url and its relationship to its short url
    """
    query = ndb.StringProperty(indexed=True)
    short_key = ndb.KeyProperty(kind='ShortUrl')

    @classmethod
    def construct(cls, iri):
        """
        Initializes an instance of DetinationIri for the purposes of operating on the datastore

        Args:
            iri (unicode): unicode representation of an (I)nternational(R)esource(I)dentifier.
               string must contain only valid iri characters

        Returns:

        """
        # construct a key for the kind in the hierarchy which corresponds to url
        kee = cls.construct_key(iri)

        # construct a model
        di = DestinationIri(key=kee)
        return di

    @classmethod
    def get_by_iri(cls, iri):
        """
        Initializes an instance of DetinationIri for the purposes of operating on the datastore

        Args:
            iri (unicode): unicode representation of an (I)nternational(R)esource(I)dentifier.
               string must contain only valid iri characters

        Returns:

        """
        return cls.construct_key(iri).get()

    @classmethod
    def normalize_iri(cls, val):
        """
        Coerces iri to standard allowable form, stripping fragment and rejecting certain conditions
        which are not allowed due to such things as ambiguous destinations or security considerations.

        Validates/Coerces a proposed iri based upon the constraints of model which are:

           Scheme:
              If iri has not scheme, it is assigned 'http'. Certain scehes are not allowed. In particular, data:
              and javascript:.

           Host:
              references to local machine are not allowed in production mode. Thus the model will
              disallow 'localhost', '127.0.0.1'. Relative urls (i.e. empty host) are also not allowed.

        Validation only pertains to logical qualities related to the datamodel. The validation
        includes checks for neither white space nor valid characters

        Args:
            val (unicode): unicode representation of an (I)nternational(R)esource(I)dentifier.
               string must contain only valid iri characters

        Returns:
            urlparse.SplitResult

        Raises:
            ModelConstraintError if and constraints regarding destination urls are violated
        """

        if len(val) > MAX_IRI_LENGTH:
            raise DestinationUrlError(DestinationUrlError.URL_TOO_LONG, max_len=MAX_IRI_LENGTH)

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
        coerced_scheme = original.scheme if original.scheme else DEFAULT_IRI_SCHEME

        if len(original.netloc) > _MAX_KEYPART_BYTES:
            raise DestinationUrlError(
                DestinationUrlError.NETLOC_TOO_LONG, max_len=_MAX_KEYPART_BYTES)
        elif len(original.path) > _MAX_KEYPART_BYTES:
            raise DestinationUrlError(
                DestinationUrlError.PATH_TOO_LONG, max_len=_MAX_KEYPART_BYTES)
        elif len(original.query) > MAX_QUERY_LENGTH:
            raise DestinationUrlError(
                DestinationUrlError.QUERY_TOO_LONG, max_len=MAX_QUERY_LENGTH)

        return NormalizedIri(
            scheme=coerced_scheme,
            netloc=original.netloc,
            path=original.path,
            query=original.query
        )

    @classmethod
    def _hierarchy_path(cls, normalized_iri):
        """
        Generates a list of entity ids which describes a path in the iri name space
        Args:
            normalized_iri(NormalizedIri): a parsed representation of the original iri
               which contains normalized components of an original iri

        Returns:

        """
        yield 'Scheme'
        yield normalized_iri.scheme
        yield 'Netloc'
        yield normalized_iri.netloc
        yield 'Path'
        yield normalized_iri.path if normalized_iri.path else DEFAULT_PATH

        seg_count = 0
        for query_seg in normalized_iri.query_segments():
            yield ''.join([
                'Query',
                ''.join(['Ext', str(seg_count) if seg_count else ''])
            ])
            yield query_seg

    @classmethod
    def construct_key(cls, iri):
        """
        Returns ndb key which describes a path to a DestinationIri in the iri 'space' hierarchy.
        The last path segment of the returned key is always of kind cls.__name__ (i.e. DestinationIri)

        Args:
            iri(unicode): a unicode representation of an (I)nternational(R)esource(I)dentifier

        Returns:
            ndb.Key:

        """
        normalized_iri = cls.normalize_iri(iri)
        path = [arg for arg in cls._hierarchy_path(normalized_iri)]
        path[-2] = cls.__name__

        return ndb.Key(*path)


def validate_dest_iri(iri_prop, val):
    """
    Validator function for use with ndb

    Args:
        iri_prop: the datastore property which will hold the value of the iri
        val: the iri to be stored

    Returns:
        unicode: if the iri was coerced into a normalized form
        None: if the iri was not coerced

    Raises:
        ModelConstraintError if and constraints regarding destination urls are violated
    """
    return urlparse.urlunsplit(DestinationIri.normalize_iri(val))


class IriProperty(ndb.TextProperty):
    """
    Derived property which holds an (I)nternational(R)esource(I)dentifier.
    Purpose of class is the implicit setting in a given entity of the value
    of a peer property, url, which is the quoted version of the iri.
    """
    def __set__(self, entity, value):
        """Descriptor protocol: set the value on the entity."""

        super(ndb.TextProperty, self).__set__(entity, value)
        quoted_iri = urlutil.iri_to_uri(value)
        entity._values['url'] = quoted_iri

class UrlProperty(ndb.BlobProperty):
    """
    Holds a quoted version of an IRI which is suitable for use in the Location header fo
    an HTTP redirection response.  This class enforces the proscription of direct
    assignment of a value to this property.
    """
    def __set__(self, entity, value):
        """Descriptor protocol: set the value on the entity."""
        raise ndb.model.ReadonlyPropertyError(
            "read-only attribute '{}' is computed from '{}'".format(self._name, 'iri'))

class ShortUrl(ndb.Model):
    """A main model for representing a url entry."""

    short_id = ndb.StringProperty(indexed=True)
    iri = IriProperty(validator=validate_dest_iri)
    url = UrlProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)