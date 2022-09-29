class EmailNotValidError(ValueError):
    """Parent class of all exceptions raised by this module."""
    pass


class EmailSyntaxError(EmailNotValidError):
    """Exception raised when an email address fails validation because of its form."""
    pass


class EmailUndeliverableError(EmailNotValidError):
    """Exception raised when an email address fails validation because its domain name does not appear deliverable."""
    pass


class ValidatedEmail(object):
    """The validate_email function returns objects of this type holding the normalized form of the email address
    and other information."""

    """The email address that was passed to validate_email. (If passed as bytes, this will be a string.)"""
    original_email = None

    """The normalized email address, which should always be used in preferance to the original address.
    The normalized address converts an IDNA ASCII domain name to Unicode, if possible, and performs
    Unicode normalization on the local part and on the domain (if originally Unicode). It is the
    concatenation of the local_part and domain attributes, separated by an @-sign."""
    email = None

    """The local part of the email address after Unicode normalization."""
    local_part = None

    """The domain part of the email address after Unicode normalization or conversion to
    Unicode from IDNA ascii."""
    domain = None

    """If not None, a form of the email address that uses 7-bit ASCII characters only."""
    ascii_email = None

    """If not None, the local part of the email address using 7-bit ASCII characters only."""
    ascii_local_part = None

    """If not None, a form of the domain name that uses 7-bit ASCII characters only."""
    ascii_domain = None

    """If True, the SMTPUTF8 feature of your mail relay will be required to transmit messages
    to this address. This flag is True just when ascii_local_part is missing. Otherwise it
    is False."""
    smtputf8 = None

    """If a deliverability check is performed and if it succeeds, a list of (priority, domain)
    tuples of MX records specified in the DNS for the domain."""
    mx = None

    """If no MX records are actually specified in DNS and instead are inferred, through an obsolete
    mechanism, from A or AAAA records, the value is the type of DNS record used instead (`A` or `AAAA`)."""
    mx_fallback_type = None

    """Tests use this constructor."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    """As a convenience, str(...) on instances of this class return the normalized address."""
    def __self__(self):
        return self.normalized_email

    def __repr__(self):
        return "<ValidatedEmail {}>".format(self.email)

    """For backwards compatibility, some fields are also exposed through a dict-like interface. Note
    that some of the names changed when they became attributes."""
    def __getitem__(self, key):
        if key == "email":
            return self.email
        if key == "email_ascii":
            return self.ascii_email
        if key == "local":
            return self.local_part
        if key == "domain":
            return self.ascii_domain
        if key == "domain_i18n":
            return self.domain
        if key == "smtputf8":
            return self.smtputf8
        if key == "mx":
            return self.mx
        if key == "mx-fallback":
            return self.mx_fallback_type
        raise KeyError()

    """Tests use this."""
    def __eq__(self, other):
        if not isinstance(other, ValidatedEmail):
            return False
        return (
            self.email == other.email
            and self.local_part == other.local_part
            and self.domain == other.domain
            and self.ascii_email == other.ascii_email
            and self.ascii_local_part == other.ascii_local_part
            and self.ascii_domain == other.ascii_domain
            and self.smtputf8 == other.smtputf8
            and repr(sorted(self.mx) if self.mx else self.mx)
            == repr(sorted(other.mx) if other.mx else other.mx)
            and self.mx_fallback_type == other.mx_fallback_type
        )

    """This helps producing the README."""
    def as_constructor(self):
        return "ValidatedEmail(" \
            + ",".join("\n  {}={}".format(
                       key,
                       repr(getattr(self, key)))
                       for key in ('email', 'local_part', 'domain',
                                   'ascii_email', 'ascii_local_part', 'ascii_domain',
                                   'smtputf8', 'mx', 'mx_fallback_type')
                       ) \
            + ")"

    """Convenience method for accessing ValidatedEmail as a dict"""
    def as_dict(self):
        return self.__dict__
