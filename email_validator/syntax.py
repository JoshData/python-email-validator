from .exceptions_types import EmailSyntaxError
from .rfc_constants import EMAIL_MAX_LENGTH, LOCAL_PART_MAX_LENGTH, DOMAIN_MAX_LENGTH, \
    DOT_ATOM_TEXT, DOT_ATOM_TEXT_INTL, ATEXT, ATEXT_INTL, ATEXT_HOSTNAME_INTL, DNS_LABEL_LENGTH_LIMIT, DOT_ATOM_TEXT_HOSTNAME, DOMAIN_NAME_REGEX

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


def safe_character_display(c):
    # Return safely displayable characters in quotes.
    if unicodedata.category(c)[0] in ("L", "N", "P", "S"):
        return repr(c)

    # Construct a hex string in case the unicode name doesn't exist.
    if ord(c) < 0xFFFF:
        h = "U+{:04x}".format(ord(c)).upper()
    else:
        h = "U+{:08x}".format(ord(c)).upper()

    # Return the character name or, if it has no name, the hex string.
    return unicodedata.name(c, h)


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

    # Check for invalid characters.
    atext_re = re.compile('[.' + (ATEXT if not allow_smtputf8 else ATEXT_INTL) + ']')
    bad_chars = set(
        safe_character_display(c)
        for c in local
        if not atext_re.match(c)
    )
    if bad_chars:
        raise EmailSyntaxError("The email address contains invalid characters before the @-sign: " + ", ".join(sorted(bad_chars)) + ".")

    # Check for dot errors imposted by the dot-atom rule.
    check_dot_atom(local, 'An email address cannot start with a {}.', 'An email address cannot have a {} immediately before the @-sign.', is_hostname=False)

    # Check the local part against the regular expression for the older ASCII requirements.
    m = DOT_ATOM_TEXT.match(local)
    if m:
        # Return the local part unchanged and flag that SMTPUTF8 is not needed.
        return {
            "local_part": local,
            "ascii_local_part": local,
            "smtputf8": False,
        }

    else:
        # The local part failed the ASCII check. Now try the extended internationalized requirements.
        # This should already be handled by the bad_chars and check_dot_atom tests above.
        m = DOT_ATOM_TEXT_INTL.match(local)
        if not m:
            raise EmailSyntaxError("The email address contains invalid characters before the @-sign.")
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
        check_unsafe_chars(local)

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


def check_unsafe_chars(s):
    bad_chars = set()
    for i, c in enumerate(s):
        category = unicodedata.category(c)
        if category[0] in ("L", "N", "P", "S"):
            # letters, numbers, punctuation, and symbols are permitted
            pass
        elif category[0] == "M":
            # combining character in first position would combine with something
            # outside of the email address if concatenated to the right, but are
            # otherwise permitted
            if i == 0:
                bad_chars.add(c)
        elif category[0] in ("Z", "C"):
            # spaces and line/paragraph characters (Z) and
            # control, format, surrogate, private use, and unassigned code points (C)
            bad_chars.add(c)
        else:
            # All categories should be handled above, but in case there is something new
            # in the future.
            bad_chars.add(c)
    if bad_chars:
        raise EmailSyntaxError("The email address contains unsafe characters: "
                               + ", ".join(safe_character_display(c) for c in sorted(bad_chars)) + ".")


def check_dot_atom(label, start_descr, end_descr, is_hostname):
    if label.endswith("."):
        raise EmailSyntaxError(end_descr.format("period"))
    if label.startswith("."):
        raise EmailSyntaxError(start_descr.format("period"))
    if ".." in label:
        raise EmailSyntaxError("An email address cannot have two periods in a row.")
    if is_hostname:
        if label.endswith("-"):
            raise EmailSyntaxError(end_descr.format("hyphen"))
        if label.startswith("-"):
            raise EmailSyntaxError(start_descr.format("hyphen"))
        if ".-" in label or "-." in label:
            raise EmailSyntaxError("An email address cannot have a period and a hyphen next to each other.")


def validate_email_domain_part(domain, test_environment=False, globally_deliverable=True):
    """Validates the syntax of the domain part of an email address."""

    # Empty?
    if len(domain) == 0:
        raise EmailSyntaxError("There must be something after the @-sign.")

    # Check for invalid characters before normalization.
    bad_chars = set(
        safe_character_display(c)
        for c in domain
        if not ATEXT_HOSTNAME_INTL.match(c)
    )
    if bad_chars:
        raise EmailSyntaxError("The part after the @-sign contains invalid characters: " + ", ".join(sorted(bad_chars)) + ".")
    check_unsafe_chars(domain)

    # Perform UTS-46 normalization, which includes casefolding, NFC normalization,
    # and converting all label separators (the period/full stop, fullwidth full stop,
    # ideographic full stop, and halfwidth ideographic full stop) to basic periods.
    # It will also raise an exception if there is an invalid character in the input,
    # such as "⒈" which is invalid because it would expand to include a period.
    try:
        domain = idna.uts46_remap(domain, std3_rules=False, transitional=False)
    except idna.IDNAError as e:
        raise EmailSyntaxError("The part after the @-sign contains invalid characters ({}).".format(str(e)))

    # The domain part is made up period-separated "labels." Each label must
    # have at least one character and cannot start or end with dashes, which
    # means there are some surprising restrictions on periods and dashes.
    # Check that before we do IDNA encoding because the IDNA library gives
    # unfriendly errors for these cases, but after UTS-46 normalization because
    # it can insert periods and hyphens (from fullwidth characters).
    check_dot_atom(domain, 'An email address cannot have a {} immediately after the @-sign.', 'An email address cannot end with a {}.', is_hostname=True)
    for label in domain.split("."):
        if re.match(r"(?!xn)..--", label, re.I):  # RFC 5890 invalid R-LDH labels
            raise EmailSyntaxError("An email address cannot have two letters followed by two dashes immediately after the @-sign or after a period, except Punycode.")

    if DOT_ATOM_TEXT_HOSTNAME.match(domain):
        # This is a valid non-internationalized domain.
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
            raise EmailSyntaxError("The part after the @-sign contains invalid characters (%s)." % str(e))

        # Check the syntax of the string returned by idna.encode.
        # It should never fail.
        m = DOT_ATOM_TEXT_HOSTNAME.match(ascii_domain)
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
            raise EmailSyntaxError("On either side of the @-sign, periods cannot be separated by so many characters {}.".format(reason))

    if globally_deliverable:
        # All publicly deliverable addresses have domain named with at least
        # one period, and we'll consider the lack of a period a syntax error
        # since that will match people's sense of what an email address looks
        # like. We'll skip this in test environments to allow '@test' email
        # addresses.
        if "." not in ascii_domain and not (ascii_domain == "test" and test_environment):
            raise EmailSyntaxError("The part after the @-sign is not valid. It should have a period.")

        # We also know that all TLDs currently end with a letter.
        if not DOMAIN_NAME_REGEX.search(ascii_domain):
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
        raise EmailSyntaxError("The part after the @-sign is not valid IDNA ({}).".format(str(e)))

    # Check for invalid characters after normalization. These
    # should never arise.
    bad_chars = set(
        safe_character_display(c)
        for c in domain
        if not ATEXT_HOSTNAME_INTL.match(c)
    )
    if bad_chars:
        raise EmailSyntaxError("The part after the @-sign contains invalid characters: " + ", ".join(sorted(bad_chars)) + ".")
    check_unsafe_chars(domain)

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
