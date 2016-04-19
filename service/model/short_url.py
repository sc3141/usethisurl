import urlparse

from google.appengine.ext import ndb

MAX_URL_LENGTH = 4096

class ShortUrl(ndb.Model):
    """A main model for representing a url entry."""
    short_id= ndb.StringProperty(indexed=True)
    url = ndb.BlobProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)


def validate_long_url(url_prop, val):
    """
    Validates/Coerces a proposed url based upon the constraints of model which are:

       Scheme:
          If url has not scheme, it is assigned 'http'

       Host:
          references to local machine are not allowed in production mode. Thus the model will
          disallow 'localhost', '127.0.0.1' and relative urls (i.e. empty host)

    Args:
        url_prop: the datastore property which will hold the value of the url
        val: the url to be stored

    Returns:

    """
    parts = urlparse.urlsplit(val)

