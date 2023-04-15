from typing import Optional, Union

from .exceptions_types import EmailSyntaxError, ValidatedEmail
from .syntax import validate_email_local_part, validate_email_domain_name, validate_email_domain_literal, get_length_reason
from .rfc_constants import EMAIL_MAX_LENGTH, QUOTED_LOCAL_PART_ADDR, CASE_INSENSITIVE_MAILBOX_NAMES


def validate_email(
    email: Union[str, bytes],
    # /, # not supported in Python 3.6, 3.7
    *,
    allow_smtputf8: Optional[bool] = None,
    allow_empty_local: bool = False,
    allow_quoted_local: Optional[bool] = None,
    allow_domain_literal: Optional[bool] = None,
    check_deliverability: Optional[bool] = None,
    test_environment: Optional[bool] = None,
    globally_deliverable: Optional[bool] = None,
    timeout: Optional[int] = None,
    dns_resolver: Optional[object] = None
) -> ValidatedEmail:
    """
    Validates an email address, raising an EmailNotValidError if the address is not valid or returning a dict of
    information when the address is valid. The email argument can be a str or a bytes instance,
    but if bytes it must be ASCII-only. This is the main method of this library.
    """

    # Fill in default values of arguments.
    from . import ALLOW_SMTPUTF8, ALLOW_QUOTED_LOCAL, ALLOW_DOMAIN_LITERAL, \
        GLOBALLY_DELIVERABLE, CHECK_DELIVERABILITY, TEST_ENVIRONMENT, DEFAULT_TIMEOUT
    if allow_smtputf8 is None:
        allow_smtputf8 = ALLOW_SMTPUTF8
    if allow_quoted_local is None:
        allow_quoted_local = ALLOW_QUOTED_LOCAL
    if allow_domain_literal is None:
        allow_domain_literal = ALLOW_DOMAIN_LITERAL
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

    # Typical email addresses have a single @-sign, but the
    # awkward "quoted string" local part form (RFC 5321 4.1.2)
    # allows @-signs (and escaped quotes) to appear in the local
    # part if the local part is quoted. If the address is quoted,
    # split it at a non-escaped @-sign and unescape the escaping.
    quoted_local_part = False
    m = QUOTED_LOCAL_PART_ADDR.match(email)
    if m:
        quoted_local_part = True
        local_part, domain_part = m.groups()

        # Remove backslashes.
        import re
        local_part = re.sub(r"\\(.)", "\\1", local_part)

    else:
        # Split at the one and only at-sign.
        parts = email.split('@')
        if len(parts) != 2:
            raise EmailSyntaxError("The email address is not valid. It must have exactly one @-sign.")
        local_part, domain_part = parts

    # Collect return values in this instance.
    ret = ValidatedEmail()
    ret.original = email

    # Validate the email address's local part syntax and get a normalized form.
    # If the original address was quoted and the decoded local part is a valid
    # unquoted local part, then we'll get back a normalized (unescaped) local
    # part.
    local_part_info = validate_email_local_part(local_part,
                                                allow_smtputf8=allow_smtputf8,
                                                allow_empty_local=allow_empty_local,
                                                quoted_local_part=quoted_local_part)
    if quoted_local_part and not allow_quoted_local:
        raise EmailSyntaxError("Quoting the part before the @-sign is not allowed here.")
    ret.local_part = local_part_info["local_part"]
    ret.ascii_local_part = local_part_info["ascii_local_part"]
    ret.smtputf8 = local_part_info["smtputf8"]

    # Some local parts are required to be case-insensitive, so we should normalize
    # to lowercase.
    # RFC 2142
    if ret.ascii_local_part is not None \
       and ret.ascii_local_part.lower() in CASE_INSENSITIVE_MAILBOX_NAMES \
       and ret.local_part is not None:
        ret.ascii_local_part = ret.ascii_local_part.lower()
        ret.local_part = ret.local_part.lower()

    # Validate the email address's domain part syntax and get a normalized form.
    is_domain_literal = False
    if len(domain_part) == 0:
        raise EmailSyntaxError("There must be something after the @-sign.")

    elif domain_part.startswith("[") and domain_part.endswith("]"):
        # Parse the address in the domain literal and get back a normalized domain.
        domain_part_info = validate_email_domain_literal(domain_part[1:-1], allow_domain_literal=allow_domain_literal)
        ret.domain = domain_part_info["domain"]
        ret.ascii_domain = domain_part_info["domain"]  # Domain literals are always ASCII.
        ret.domain_address = domain_part_info["domain_address"]
        is_domain_literal = True  # Prevent deliverability checks.

    else:
        # Check the syntax of the domain and get back a normalized
        # internationalized and ASCII form.
        domain_part_info = validate_email_domain_name(domain_part, test_environment=test_environment, globally_deliverable=globally_deliverable)
        ret.domain = domain_part_info["domain"]
        ret.ascii_domain = domain_part_info["ascii_domain"]

    # Construct the complete normalized form.
    ret.normalized = ret.local_part + "@" + ret.domain

    # If the email address has an ASCII form, add it.
    if not ret.smtputf8:
        if not ret.ascii_domain:
            raise Exception("Missing ASCII domain.")
        ret.ascii_email = (ret.ascii_local_part or "") + "@" + ret.ascii_domain
    else:
        ret.ascii_email = None

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
        if ret.ascii_email == ret.normalized:
            reason = get_length_reason(ret.ascii_email)
        elif len(ret.normalized) > EMAIL_MAX_LENGTH:
            # If there are more than 254 characters, then the ASCII
            # form is definitely going to be too long.
            reason = get_length_reason(ret.normalized, utf8=True)
        else:
            reason = "(when converted to IDNA ASCII)"
        raise EmailSyntaxError(f"The email address is too long {reason}.")
    if len(ret.normalized.encode("utf8")) > EMAIL_MAX_LENGTH:
        if len(ret.normalized) > EMAIL_MAX_LENGTH:
            # If there are more than 254 characters, then the UTF-8
            # encoding is definitely going to be too long.
            reason = get_length_reason(ret.normalized, utf8=True)
        else:
            reason = "(when encoded in bytes)"
        raise EmailSyntaxError(f"The email address is too long {reason}.")

    if check_deliverability and not test_environment:
        # Validate the email address's deliverability using DNS
        # and update the return dict with metadata.

        if is_domain_literal:
            # There is nothing to check --- skip deliverability checks.
            return ret

        # Lazy load `deliverability` as it is slow to import (due to dns.resolver)
        from .deliverability import validate_email_deliverability
        deliverability_info = validate_email_deliverability(
            ret.ascii_domain, ret.domain, timeout, dns_resolver
        )
        for key, value in deliverability_info.items():
            setattr(ret, key, value)

    return ret
