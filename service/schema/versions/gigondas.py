import os
import logging

from google.appengine.ext import deferred
from google.appengine.ext import ndb

from service.model import url
from service.schema import update_message

BATCH_SIZE = 100  # ideal batch size may vary based on entity size.

def update_schema(cursor=None, num_updated=0):
    query = url.ShortUrl.query()
    fetched, cur, more = query.fetch_page(BATCH_SIZE, start_cursor=cursor)

    to_put = []
    for shorturl in fetched:
        # where iri is None, set it to the value of url
        if not shorturl.iri:
            shorturl.iri = shorturl.url
        to_put.append(shorturl)

    if to_put:
        ndb.put_multi(to_put)
        num_updated += len(to_put)
        logging.debug(
            'Put %d entities to Datastore for a total of %d',
            len(to_put), num_updated)
        if more:
            deferred.defer(
                update_schema, cursor=cur, num_updated=num_updated)
    else:
        logging.debug(
            update_message(vers=__name__, msg="complete with {:d} updates!".format(num_updated)))

