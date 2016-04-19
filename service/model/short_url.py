import logging
import urlparse

from google.appengine.api.app_identity import app_identity
from google.appengine.ext import ndb

from model_error import ModelContraintError

MAX_URL_LENGTH = 4096

ALLOWED_SCHEMES = set([
    'http',
    'https',
    'ftp',
    'ftps',
    'mailto',
    'mms',
    'rtmp',
    'rtmpt',
    'ed2k',
    'pop',
    'imap',
    'nntp',
    'news',
    'ldap',
    'gopher',
    'dict',
    'dns'
])

LOCALHOSTS = set([
    'localhost', '127.0.0.1',
])


def normalize_long_url(val):
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

    Args:
        val:

    Returns:
        urlparse.SplitResult

    Raises:
        ModelConstraintError if and constraints regarding long urls are violated
    """

    if len(val) > MAX_URL_LENGTH:
        raise ModelContraintError(ModelContraintError.URL_TOO_LONG)

    original = urlparse.urlsplit(val)
    if not original.netloc:
        if val.startswith(original.scheme):
            raise ModelContraintError(ModelContraintError.RELATIVE_URL_NOT_ALLOWED)
        else:
            raise ModelContraintError(ModelContraintError.HOST_OMITTED)

    if not original.hostname or original.hostname in LOCALHOSTS:
        raise ModelContraintError(ModelContraintError.LOCALHOST_NOT_ALLOWED)
    elif -1 != original.hostname.find(app_identity.get_default_version_hostname()):
        raise ModelContraintError(ModelContraintError.RECURSIVE_REDIRECTION_ALLOWED)

    if original.scheme:
        if original.scheme not in ALLOWED_SCHEMES:
            raise ModelContraintError(ModelContraintError.SCHEME_NOT_ALLOWED, original.scheme)
    coerced_scheme = original.scheme if original.scheme else 'http'

    return urlparse.SplitResult(
        coerced_scheme,
        original.netloc,
        original.path,
        original.query,
        None)

def validate_long_url(url_prop, val):
    """
    Validator function for use with ndb

    Args:
        url_prop: the datastore property which will hold the value of the url
        val: the url to be stored

    Returns:
        str: if the url was coerced into a normalized form
        None: if the url was not coerced

    Raises:
        ModelConstraintError if and constraints regarding long urls are violated
    """
    return urlparse.urlunsplit(normalize_long_url(val))


class ShortUrl(ndb.Model):
    """A main model for representing a url entry."""
    short_id= ndb.StringProperty(indexed=True)
    url = ndb.BlobProperty(indexed=False, validator=validate_long_url)
    date = ndb.DateTimeProperty(auto_now_add=True)


