from .exceptions_types import EmailSyntaxError, ValidatedEmail
from .syntax import validate_email_local_part, validate_email_domain_part, get_length_reason
from .rfc_constants import EMAIL_MAX_LENGTH


def validate_email(
    email,
    # /, # not supported in Python 3.6, 3.7
    *,
    allow_smtputf8=None,
    allow_empty_local=False,
    check_deliverability=None,
    test_environment=None,
    globally_deliverable=None,
    timeout=None,
    dns_resolver=None
):
    """
    Validates an email address, raising an EmailNotValidError if the address is not valid or returning a dict of
    information when the address is valid. The email argument can be a str or a bytes instance,
    but if bytes it must be ASCII-only. This is the main method of this library.
    """

    # Fill in default values of arguments.
    from . import ALLOW_SMTPUTF8, CHECK_DELIVERABILITY, TEST_ENVIRONMENT, GLOBALLY_DELIVERABLE, DEFAULT_TIMEOUT
    if allow_smtputf8 is None:
        allow_smtputf8 = ALLOW_SMTPUTF8
    if check_deliverability is None:
        check_deliverability = CHECK_DELIVERABILITY
    if test_environment is None:
        test_environment = TEST_ENVIRONMENT
    if globally_deliverable is None:
        globally_deliverable = GLOBALLY_DELIVERABLE
    if timeout is None:
        timeout = DEFAULT_TIMEOUT

    # Allow email to be a str or bytes instance. If bytes,
    # it must be ASCII because that's how the bytes work
    # on the wire with SMTP.
    if not isinstance(email, str):
        try:
            email = email.decode("ascii")
        except ValueError:
            raise EmailSyntaxError("The email address is not valid ASCII.")

    # At-sign.
    parts = email.split('@')
    if len(parts) != 2:
        raise EmailSyntaxError("The email address is not valid. It must have exactly one @-sign.")

    # Collect return values in this instance.
    ret = ValidatedEmail()
    ret.original_email = email

    # Validate the email address's local part syntax and get a normalized form.
    local_part_info = validate_email_local_part(parts[0],
                                                allow_smtputf8=allow_smtputf8,
                                                allow_empty_local=allow_empty_local)
    ret.local_part = local_part_info["local_part"]
    ret.ascii_local_part = local_part_info["ascii_local_part"]
    ret.smtputf8 = local_part_info["smtputf8"]

    # Validate the email address's domain part syntax and get a normalized form.
    domain_part_info = validate_email_domain_part(parts[1], test_environment=test_environment, globally_deliverable=globally_deliverable)
    ret.domain = domain_part_info["domain"]
    ret.ascii_domain = domain_part_info["ascii_domain"]

    # Construct the complete normalized form.
    ret.email = ret.local_part + "@" + ret.domain

    # If the email address has an ASCII form, add it.
    if not ret.smtputf8:
        ret.ascii_email = ret.ascii_local_part + "@" + ret.ascii_domain

    # If the email address has an ASCII representation, then we assume it may be
    # transmitted in ASCII (we can't assume SMTPUTF8 will be used on all hops to
    # the destination) and the length limit applies to ASCII characters (which is
    # the same as octets). The number of characters in the internationalized form
    # may be many fewer (because IDNA ASCII is verbose) and could be less than 254
    # Unicode characters, and of course the number of octets over the limit may
    # not be the number of characters over the limit, so if the email address is
    # internationalized, we can't give any simple information about why the address
    # is too long.
    #
    # In addition, check that the UTF-8 encoding (i.e. not IDNA ASCII and not
    # Unicode characters) is at most 254 octets. If the addres is transmitted using
    # SMTPUTF8, then the length limit probably applies to the UTF-8 encoded octets.
    # If the email address has an ASCII form that differs from its internationalized
    # form, I don't think the internationalized form can be longer, and so the ASCII
    # form length check would be sufficient. If there is no ASCII form, then we have
    # to check the UTF-8 encoding. The UTF-8 encoding could be up to about four times
    # longer than the number of characters.
    #
    # See the length checks on the local part and the domain.
    if ret.ascii_email and len(ret.ascii_email) > EMAIL_MAX_LENGTH:
        if ret.ascii_email == ret.email:
            reason = get_length_reason(ret.ascii_email)
        elif len(ret.email) > EMAIL_MAX_LENGTH:
            # If there are more than 254 characters, then the ASCII
            # form is definitely going to be too long.
            reason = get_length_reason(ret.email, utf8=True)
        else:
            reason = "(when converted to IDNA ASCII)"
        raise EmailSyntaxError(f"The email address is too long {reason}.")
    if len(ret.email.encode("utf8")) > EMAIL_MAX_LENGTH:
        if len(ret.email) > EMAIL_MAX_LENGTH:
            # If there are more than 254 characters, then the UTF-8
            # encoding is definitely going to be too long.
            reason = get_length_reason(ret.email, utf8=True)
        else:
            reason = "(when encoded in bytes)"
        raise EmailSyntaxError(f"The email address is too long {reason}.")

    if check_deliverability and not test_environment:
        # Validate the email address's deliverability using DNS
        # and update the return dict with metadata.

        # Lazy load `deliverability` as it is slow to import (due to dns.resolver)
        from .deliverability import validate_email_deliverability
        deliverability_info = validate_email_deliverability(
            ret["domain"], ret["domain_i18n"], timeout, dns_resolver
        )
        for key, value in deliverability_info.items():
            setattr(ret, key, value)

    return ret
