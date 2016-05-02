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
    to_delete = []
    for shorturl in fetched:
        # where iri is None, set it to the value of url
        if not shorturl.iri:
            try:
                shorturl.iri = shorturl.url
            except ValueError as e:
                to_delete.append(shorturl)
            else:
                to_put.append(shorturl)

    if to_put:
        ndb.put_multi(to_put)
        num_updated += len(to_put)
        logging.debug(
            'Put %d entities to Datastore for a total updated of %d',
            len(to_put), num_updated)

    if to_delete:
        ndb.delete_multi([s.key for s  in to_delete])

        to_prune = []
        for s in to_delete:
            try:
                key = url.DestinationIri.construct_key(s.url)
                to_prune.append(key)
            except ValueError as e:
                logging.info("update_schema-->gigondas: unable to construct key for dest iri (%s): %s" % (s.url, e.message))

        ndb.delete_multi(to_prune)

        num_updated += len(to_delete)
        logging.debug(
            'Deleted %d entities to Datastore for a total updated of %d',
            len(to_delete), num_updated)

    if more:
        deferred.defer(
            update_schema, cursor=cur, num_updated=num_updated)
    else:
        logging.debug(
            update_message(vers=__name__, msg="complete with {:d} updates!".format(num_updated)))

