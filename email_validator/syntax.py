from .exceptions_types import EmailSyntaxError
from .rfc_constants import EMAIL_MAX_LENGTH, LOCAL_PART_MAX_LENGTH, DOMAIN_MAX_LENGTH, \
    DOT_ATOM_TEXT, DOT_ATOM_TEXT_INTL, ATEXT, ATEXT_INTL, DNS_LABEL_LENGTH_LIMIT, DOT_ATOM_TEXT_HOSTNAME

import re
import unicodedata
import idna  # implements IDNA 2008; Python's codec is only IDNA 2003


def get_length_reason(addr, utf8=False, limit=EMAIL_MAX_LENGTH):
    """Helper function to return an error message related to invalid length."""
    diff = len(addr) - limit
    reason = "({}{} character{} too many)"
    prefix = "at least " if utf8 else ""
    suffix = "s" if diff > 1 else ""
    return reason.format(prefix, diff, suffix)


def validate_email_local_part(local, allow_smtputf8=True, allow_empty_local=False):
    """Validates the syntax of the local part of an email address."""

    if len(local) == 0:
        if not allow_empty_local:
            raise EmailSyntaxError("There must be something before the @-sign.")
        else:
            # The caller allows an empty local part. Useful for validating certain
            # Postfix aliases.
            return {
                "local_part": local,
                "ascii_local_part": local,
                "smtputf8": False,
            }

    # RFC 5321 4.5.3.1.1
    # We're checking the number of characters here. If the local part
    # is ASCII-only, then that's the same as bytes (octets). If it's
    # internationalized, then the UTF-8 encoding may be longer, but
    # that may not be relevant. We will check the total address length
    # instead.
    if len(local) > LOCAL_PART_MAX_LENGTH:
        reason = get_length_reason(local, limit=LOCAL_PART_MAX_LENGTH)
        raise EmailSyntaxError("The email address is too long before the @-sign {}.".format(reason))

    # Check the local part against the regular expression for the older ASCII requirements.
    m = re.match(DOT_ATOM_TEXT + "\\Z", local)
    if m:
        # Return the local part unchanged and flag that SMTPUTF8 is not needed.
        return {
            "local_part": local,
            "ascii_local_part": local,
            "smtputf8": False,
        }

    else:
        # The local part failed the ASCII check. Now try the extended internationalized requirements.
        m = re.match(DOT_ATOM_TEXT_INTL + "\\Z", local)
        if not m:
            # It's not a valid internationalized address either. Report which characters were not valid.
            bad_chars = ', '.join(sorted(set(
                unicodedata.name(c, repr(c)) for c in local if not re.match(u"[" + (ATEXT if not allow_smtputf8 else ATEXT_INTL) + u"]", c)
            )))
            raise EmailSyntaxError("The email address contains invalid characters before the @-sign: %s." % bad_chars)

        # It would be valid if internationalized characters were allowed by the caller.
        if not allow_smtputf8:
            raise EmailSyntaxError("Internationalized characters before the @-sign are not supported.")

        # It's valid.

        # RFC 6532 section 3.1 also says that Unicode NFC normalization should be applied,
        # so we'll return the normalized local part in the return value.
        local = unicodedata.normalize("NFC", local)

        # Check for unsafe characters.
        # Some of this may be redundant with the range U+0080 to U+10FFFF that is checked
        # by DOT_ATOM_TEXT_INTL.
        for i, c in enumerate(local):
            category = unicodedata.category(c)
            if category[0] in ("L", "N", "P", "S"):
                # letters, numbers, punctuation, and symbols are permitted
                pass
            elif category[0] == "M":
                # combining character in first position would combine with something
                # outside of the email address if concatenated to the right, but are
                # otherwise permitted
                if i == 0:
                    raise EmailSyntaxError("The email address contains an initial invalid character (%s)."
                                           % unicodedata.name(c, repr(c)))
            elif category[0] in ("Z", "C"):
                # spaces and line/paragraph characters (Z) and
                # control, format, surrogate, private use, and unassigned code points (C)
                raise EmailSyntaxError("The email address contains an invalid character (%s)."
                                       % unicodedata.name(c, repr(c)))
            else:
                # All categories should be handled above, but in case there is something new
                # in the future.
                raise EmailSyntaxError("The email address contains a character (%s; category %s) that may not be safe."
                                       % (unicodedata.name(c, repr(c)), category))

        # Try encoding to UTF-8. Failure is possible with some characters like
        # surrogate code points, but those are checked above. Still, we don't
        # want to have an unhandled exception later.
        try:
            local.encode("utf8")
        except ValueError:
            raise EmailSyntaxError("The email address contains an invalid character.")

        # Flag that SMTPUTF8 will be required for deliverability.
        return {
            "local_part": local,
            "ascii_local_part": None,  # no ASCII form is possible
            "smtputf8": True,
        }


def validate_email_domain_part(domain, test_environment=False, globally_deliverable=True):
    """Validates the syntax of the domain part of an email address."""

    # Empty?
    if len(domain) == 0:
        raise EmailSyntaxError("There must be something after the @-sign.")

    # Perform UTS-46 normalization, which includes casefolding, NFC normalization,
    # and converting all label separators (the period/full stop, fullwidth full stop,
    # ideographic full stop, and halfwidth ideographic full stop) to basic periods.
    # It will also raise an exception if there is an invalid character in the input,
    # such as "⒈" which is invalid because it would expand to include a period.
    try:
        domain = idna.uts46_remap(domain, std3_rules=False, transitional=False)
    except idna.IDNAError as e:
        raise EmailSyntaxError("The domain name %s contains invalid characters (%s)." % (domain, str(e)))

    # Now we can perform basic checks on the use of periods (since equivalent
    # symbols have been mapped to periods). These checks are needed because the
    # IDNA library doesn't handle well domains that have empty labels (i.e. initial
    # dot, trailing dot, or two dots in a row).
    if domain.endswith("."):
        raise EmailSyntaxError("An email address cannot end with a period.")
    if domain.startswith("."):
        raise EmailSyntaxError("An email address cannot have a period immediately after the @-sign.")
    if ".." in domain:
        raise EmailSyntaxError("An email address cannot have two periods in a row.")

    if re.match(DOT_ATOM_TEXT_HOSTNAME + "\\Z", domain):
        ascii_domain = domain
    else:
        # If international characters are present in the domain name, convert
        # the domain to IDNA ASCII. If internationalized characters are present,
        # the MTA must either support SMTPUTF8 or the mail client must convert the
        # domain name to IDNA before submission.
        #
        # Unfortunately this step incorrectly 'fixes' domain names with leading
        # periods by removing them, so we have to check for this above. It also gives
        # a funky error message ("No input") when there are two periods in a
        # row, also checked separately above.
        #
        # For ASCII-only domains, the transformation does nothing and is safe to
        # apply. However, to ensure we don't rely on the idna library for basic
        # syntax checks, we don't use it if it's not needed.
        try:
            ascii_domain = idna.encode(domain, uts46=False).decode("ascii")
        except idna.IDNAError as e:
            if "Domain too long" in str(e):
                # We can't really be more specific because UTS-46 normalization means
                # the length check is applied to a string that is different from the
                # one the user supplied. Also I'm not sure if the length check applies
                # to the internationalized form, the IDNA ASCII form, or even both!
                raise EmailSyntaxError("The email address is too long after the @-sign.")
            raise EmailSyntaxError("The domain name %s contains invalid characters (%s)." % (domain, str(e)))

        # Check the syntax of the string returned by idna.encode.
        # It should never fail.
        m = re.match(DOT_ATOM_TEXT_HOSTNAME + "\\Z", ascii_domain)
        if not m:
            raise EmailSyntaxError("The email address contains invalid characters after the @-sign after IDNA encoding.")

    # RFC 5321 4.5.3.1.2
    # We're checking the number of bytes (octets) here, which can be much
    # higher than the number of characters in internationalized domains,
    # on the assumption that the domain may be transmitted without SMTPUTF8
    # as IDNA ASCII. (This is also checked by idna.encode, so this exception
    # is never reached for internationalized domains.)
    if len(ascii_domain) > DOMAIN_MAX_LENGTH:
        reason = get_length_reason(ascii_domain, limit=DOMAIN_MAX_LENGTH)
        raise EmailSyntaxError("The email address is too long after the @-sign {}.".format(reason))
    for label in ascii_domain.split("."):
        if len(label) > DNS_LABEL_LENGTH_LIMIT:
            reason = get_length_reason(label, limit=DNS_LABEL_LENGTH_LIMIT)
            raise EmailSyntaxError("The part of the email address \"{}\" is too long {}.".format(label, reason))

    if globally_deliverable:
        # All publicly deliverable addresses have domain named with at least
        # one period, and we'll consider the lack of a period a syntax error
        # since that will match people's sense of what an email address looks
        # like. We'll skip this in test environments to allow '@test' email
        # addresses.
        if "." not in ascii_domain and not (ascii_domain == "test" and test_environment):
            raise EmailSyntaxError("The part after the @-sign is not valid. It should have a period.")

        # We also know that all TLDs currently end with a letter.
        if not re.search(r"[A-Za-z]\Z", ascii_domain):
            raise EmailSyntaxError("The part after the @-sign is not valid. It is not within a valid top-level domain.")

    # Check special-use and reserved domain names.
    # Some might fail DNS-based deliverability checks, but that
    # can be turned off, so we should fail them all sooner.
    from . import SPECIAL_USE_DOMAIN_NAMES
    for d in SPECIAL_USE_DOMAIN_NAMES:
        # See the note near the definition of SPECIAL_USE_DOMAIN_NAMES.
        if d == "test" and test_environment:
            continue

        if ascii_domain == d or ascii_domain.endswith("." + d):
            raise EmailSyntaxError("The part after the @-sign is a special-use or reserved name that cannot be used with email.")

    # We may have been given an IDNA ASCII domain to begin with. Check
    # that the domain actually conforms to IDNA. It could look like IDNA
    # but not be actual IDNA. For ASCII-only domains, the conversion out
    # of IDNA just gives the same thing back.
    #
    # This gives us the canonical internationalized form of the domain,
    # which we should use in all error messages.
    try:
        domain_i18n = idna.decode(ascii_domain.encode('ascii'))
    except idna.IDNAError as e:
        raise EmailSyntaxError("The domain name %s is not valid IDNA (%s)." % (ascii_domain, str(e)))

    # Return the IDNA ASCII-encoded form of the domain, which is how it
    # would be transmitted on the wire (except when used with SMTPUTF8
    # possibly), as well as the canonical Unicode form of the domain,
    # which is better for display purposes. This should also take care
    # of RFC 6532 section 3.1's suggestion to apply Unicode NFC
    # normalization to addresses.
    return {
        "ascii_domain": ascii_domain,
        "domain": domain_i18n,
    }
