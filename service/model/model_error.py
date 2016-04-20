"""
Defines error conditions specifically associated with the (data) model
"""

class ModelError(ValueError):
    """
    This class provides a common implementation/mechanis for more specific classes of errors
    of method, decode, is cleaner
    """

    default_reason = "unspecified error"
    ERROR_REASONS = {}

    @classmethod
    def generic_description(cls, code):
        """
        Args:
            code (int): an error code returned from method, decode

        Returns:
            str: a description of the error

        """
        return cls.ERROR_REASONS.get(code, cls.default_reason)

    def __init__(self, code, message = '', **kwargs):
        """
        Args:
            code (int): code which descrbes the error

        Returns:

        """
        # if optional arg, message is non-empty, concatenate it
        message =  ': '.join([s for s in (self.generic_description(code), message) if s])
        super(ModelError, self).__init__(message.format(**kwargs) if kwargs else message)
        self.code = code


class DecodeError(ModelError):
    """
    This class provides for a more organized cessation of decoding upon error: the implementation
    of method, decode, is cleaner
    """

    default_reason = "unspecified decode error"

    ID_TOO_LONG = -1
    INVALID_NUMERAL = -2
    INCOMPLETE_REPEAT = -3
    INVALID_REPEATED_NUMERAL = -4
    INVALID_REPEAT_COUNT_NUMERAL = -5
    REPEAT_OVERFLOWS = -6
    OVERFLOW = -7

    ERROR_REASONS = {
        ID_TOO_LONG: "id length exceeds maximum {max_len}",
        INVALID_NUMERAL: 'a character which is not a numeral was present in the string',
        INCOMPLETE_REPEAT: 'end of string encountered in repeat sequence (=<val><count>)',
        INVALID_REPEATED_NUMERAL: 'the digit specified to be repeated is not a numeral',
        INVALID_REPEAT_COUNT_NUMERAL: 'the repeat count is not a numeral',
        REPEAT_OVERFLOWS: 'repeat sequence would result in number greater than MAX_ID',
        OVERFLOW: 'decoded id is greater than MAX_ID (too many bits or value)'
    }

class DestinationUrlError(ModelError):
    """
    Provides mechanism by which constraits of the model are violated.
    """

    URL_TOO_LONG = -1
    SCHEME_NOT_ALLOWED = -2
    RELATIVE_URL_NOT_ALLOWED = -3
    HOST_OMITTED = -4
    LOCALHOST_NOT_ALLOWED = -5
    RECURSIVE_REDIRECTION_ALLOWED = -6

    ERROR_REASONS = {
        URL_TOO_LONG: "url exceeds maximum allowed length {max_len}",
        SCHEME_NOT_ALLOWED: "url specifies an unsupported protocol",
        RELATIVE_URL_NOT_ALLOWED: "relative urls are not supported. missing //",
        HOST_OMITTED: "implication of localhost by omission of host is not allowed",
        LOCALHOST_NOT_ALLOWED: "redirection to localhost is not allowed",
        RECURSIVE_REDIRECTION_ALLOWED: "recursive redirection to shorturl service is not allowed.",
    }
