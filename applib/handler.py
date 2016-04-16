"""
Implements useful utilities for use within handlers.
"""

import logging

def is_local(request):
    return request.remote_addr == '127.0.0.1'

def set_status(response, code, message):
    response.set_status(code, message=message)
    response.out.write(message)
    logging.error(message)


