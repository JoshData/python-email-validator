# -*- coding: utf-8 -*-

class EmailNotValidError(ValueError):
    """Parent class of all exceptions raised by this module."""
    pass


class EmailSyntaxError(EmailNotValidError):
    """Parent class of exceptions raised when an email address fails validation because of its form."""
    pass



# Syntax errors pertaining to the email address as a whole
class EmailInvalidAsciiError(EmailSyntaxError):
    """Exception raised when an email address fails validation because it is not valid ASCII."""
    pass

class EmailNoAtSignError(EmailSyntaxError):
    """Exception raised when an email address fails validation because it does not contain an @-sign"""
    pass

class EmailMultipleAtSignsError(EmailSyntaxError):
    """Exception raised when an email address fails validation because it contains more than one @-sign"""
    pass



# Syntax errors pertaining to the email address being too long
class EmailTooLongError(EmailSyntaxError):
    """Parent class of exceptions raised when an email address fails validation because it is too long."""
    pass

class EmailTooLongAsciiError(EmailTooLongError):
    """Exception raised when an email address fails validation because it is too long when converted to IDNA ASCII.
    May contain a second argument with the integer number of characters the email address exceeds the allowed length."""
    pass

class EmailTooLongUtf8Error(EmailTooLongError):
    """Exception raised when an email address fails validation because it is too long when encoded in bytes.
    May contain a second argument with the integer number of characters the email address exceeds the allowed length."""
    pass



# Syntax errors pertaining to the local part of the email (i.e. before the @-sign)
class EmailLocalPartError(EmailSyntaxError):
    """Parent class of exceptions raised when an email address fails validation because of its local part."""
    pass

class EmailLocalPartEmptyError(EmailLocalPartError):
    """Exception raised when an email address fails validation because it contains no characters before the @-sign."""
    pass

class EmailLocalPartTooLongError(EmailLocalPartError):
    """Exception raised when an email address fails validation because the part before the @-sign is too long when converted to IDNA ASCII.
    May contain a second argument with the integer number of characters the email address exceeds the allowed length."""
    pass

class EmailLocalPartInvalidCharactersError(EmailLocalPartError):
    """Exception raised when an email address fails validation because it contains invalid characters before the @-sign."""
    pass

class EmailLocalPartInternationalizedCharactersError(EmailLocalPartError):
    """Exception raised when an email address fails validation because it contains internationalized characters before the @-sign."""
    pass



# Syntax errors pertaining to the domain part of the email (i.e. after the @-sign)
class EmailDomainPartError(EmailSyntaxError):
    """Parent class of exceptions raised when an email address fails validation because of its local part."""
    pass

class EmailDomainPartEmptyError(EmailDomainPartError):
    """Exception raised when an email address fails validation because it contains no characters after the @-sign."""
    pass

class EmailDomainInvalidCharactersError(EmailDomainPartError):
    """Exception raised when an email address fails validation because it contains invalid characters after the @-sign."""
    pass

class EmailDomainInvalidIdnaError(EmailDomainInvalidCharactersError):
    """Exception raised when an email address fails validation because it contains invalid characters after the @-sign.
    Contains the original IDNA error as a second argument."""
    pass

class EmailDomainEndsWithPeriodError(EmailDomainPartError):
    """Exception raised when an email address fails validation because it ends with a period."""
    pass

class EmailDomainStartsWithPeriodError(EmailDomainPartError):
    """Exception raised when an email address fails validation because it has a period immediately after the @-sign."""
    pass

class EmailDomainMultiplePeriodsInARowError(EmailDomainPartError):
    """Exception raised when an email address fails validation because it contains two or more periods in a row after the @-sign."""
    pass

class EmailDomainTooLongError(EmailDomainPartError):
    """Exception raised when an email address fails validation because the part after the @-sign is too long."""
    pass

class EmailDomainNoPeriodError(EmailDomainPartError):
    """Exception raised when an email address fails validation because it does not contain a period after the @-sign."""
    pass

class EmailDomainNoValidTldError(EmailDomainPartError):
    """Exception raised when an email address fails validation because it does not contain a valid top-level domain (TLD) after the @-sign."""
    pass



# Errors determined heuristically from DNS queries
# The parent class name is retained for backwards-compatibility
class EmailUndeliverableError(EmailNotValidError):
    """Parent class of exceptions raised when an email address fails validation because its domain name does not appear deliverable."""
    pass

class EmailDomainNameDoesNotExistError(EmailUndeliverableError):
    """Exception raised when an email address fails validation because its domain name does not exist."""
    pass

class EmailDomainUnhandledDnsExceptionError(EmailUndeliverableError):
    """Exception raised when an email address fails validation because the DNS query of its domain name has raised an exception.
    Contains the DNS exception (from the Python dns module) as the second argument."""
    pass

