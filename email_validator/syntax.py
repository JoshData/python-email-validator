from .exceptions_types import EmailSyntaxError
from .rfc_constants import EMAIL_MAX_LENGTH, LOCAL_PART_MAX_LENGTH, DOMAIN_MAX_LENGTH, \
    DOT_ATOM_TEXT, DOT_ATOM_TEXT_INTL, ATEXT_RE, ATEXT_INTL_RE, ATEXT_HOSTNAME_INTL, DNS_LABEL_LENGTH_LIMIT, DOT_ATOM_TEXT_HOSTNAME, DOMAIN_NAME_REGEX

import re
import unicodedata
import idna  # implements IDNA 2008; Python's codec is only IDNA 2003


def get_length_reason(addr, utf8=False, limit=EMAIL_MAX_LENGTH):
    """Helper function to return an error message related to invalid length."""
    diff = len(addr) - limit
    prefix = "at least " if utf8 else ""
    suffix = "s" if diff > 1 else ""
    return f"({prefix}{diff} character{suffix} too many)"


def safe_character_display(c):
    # Return safely displayable characters in quotes.
    if unicodedata.category(c)[0] in ("L", "N", "P", "S"):
        return repr(c)

    # Construct a hex string in case the unicode name doesn't exist.
    if ord(c) < 0xFFFF:
        h = f"U+{ord(c):04x}".upper()
    else:
        h = f"U+{ord(c):08x}".upper()

    # Return the character name or, if it has no name, the hex string.
    return unicodedata.name(c, h)


def validate_email_local_part(local: str, allow_smtputf8: bool = True, allow_empty_local: bool = False):
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

    # Check the length of the local part by couting characters.
    # (RFC 5321 4.5.3.1.1)
    # We're checking the number of characters here. If the local part
    # is ASCII-only, then that's the same as bytes (octets). If it's
    # internationalized, then the UTF-8 encoding may be longer, but
    # that may not be relevant. We will check the total address length
    # instead.
    if len(local) > LOCAL_PART_MAX_LENGTH:
        reason = get_length_reason(local, limit=LOCAL_PART_MAX_LENGTH)
        raise EmailSyntaxError(f"The email address is too long before the @-sign {reason}.")

    # Check the local part against the non-internationalized regular expression.
    # Most email addresses match this regex so it's probably fastest to check this first.
    # (RFC 2822 3.2.4)
    m = DOT_ATOM_TEXT.match(local)
    if m:
        # It's valid.

        # Return the local part unchanged and flag that SMTPUTF8 is not needed.
        return {
            "local_part": local,
            "ascii_local_part": local,
            "smtputf8": False,
        }

    # The local part failed the ASCII check. Try the extended character set
    # for internationalized addresses. It's the same pattern but with additional
    # characters permitted.
    m = DOT_ATOM_TEXT_INTL.match(local)
    if m:
        # It's valid.

        # But international characters in the local part may not be permitted.
        if not allow_smtputf8:
            # Check for invalid characters against the non-internationalized
            # permitted character set.
            # (RFC 2822 Section 3.2.4 / RFC 5322 Section 3.2.3)
            bad_chars = set(
                safe_character_display(c)
                for c in local
                if not ATEXT_RE.match(c)
            )
            if bad_chars:
                raise EmailSyntaxError("Internationalized characters before the @-sign are not supported: " + ", ".join(sorted(bad_chars)) + ".")

            # Although the check above should always find something, fall back to this just in case.
            raise EmailSyntaxError("Internationalized characters before the @-sign are not supported.")

        # RFC 6532 section 3.1 also says that Unicode NFC normalization should be applied,
        # so we'll return the normalized local part in the return value.
        local = unicodedata.normalize("NFC", local)

        # Check for unsafe characters.
        # Some of this may be redundant with the range U+0080 to U+10FFFF that is checked
        # by DOT_ATOM_TEXT_INTL. Other characters may be permitted by the email specs, but
        # they may not be valid, safe, or sensible Unicode strings.
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

    # It's not a valid local part either non-internationalized or internationalized.
    # Let's find out why.

    # Check for invalid characters.
    # (RFC 2822 Section 3.2.4 / RFC 5322 Section 3.2.3, plus RFC 6531 section 3.3)
    bad_chars = set(
        safe_character_display(c)
        for c in local
        if not ATEXT_INTL_RE.match(c)
    )
    if bad_chars:
        raise EmailSyntaxError("The email address contains invalid characters before the @-sign: " + ", ".join(sorted(bad_chars)) + ".")

    # Check for dot errors imposted by the dot-atom rule.
    # (RFC 2822 3.2.4)
    check_dot_atom(local, 'An email address cannot start with a {}.', 'An email address cannot have a {} immediately before the @-sign.', is_hostname=False)

    # All of the reasons should already have been checked, but just in case
    # we have a fallback message.
    raise EmailSyntaxError("The email address contains invalid characters before the @-sign.")


def check_unsafe_chars(s):
    # Check for unsafe characters or characters that would make the string
    # invalid or non-sensible Unicode.
    bad_chars = set()
    for i, c in enumerate(s):
        category = unicodedata.category(c)
        if category[0] in ("L", "N", "P", "S"):
            # Letters, numbers, punctuation, and symbols are permitted.
            pass
        elif category[0] == "M":
            # Combining character in first position would combine with something
            # outside of the email address if concatenated, so they are not safe.
            # We also check if this occurs after the @-sign, which would not be
            # sensible.
            if i == 0:
                bad_chars.add(c)
        elif category[0] == "Z":
            # Spaces and line/paragraph characters (Z) outside of the ASCII range
            # are not specifically disallowed as far as I can tell, but they
            # violate the spirit of the non-internationalized specification that
            # email addresses do not contain spaces or line breaks when not quoted.
            bad_chars.add(c)
        elif category[0] == "C":
            # Control, format, surrogate, private use, and unassigned code points (C)
            # are all unsafe in various ways. Control and format characters can affect
            # text rendering if the email address is concatenated with other text.
            # Bidirectional format characters are unsafe, even if used properly, because
            # they cause an email address to render as a different email address.
            # Private use characters do not make sense for publicly deliverable
            # email addresses.
            bad_chars.add(c)
        else:
            # All categories should be handled above, but in case there is something new
            # to the Unicode specification in the future, reject all other categories.
            bad_chars.add(c)
    if bad_chars:
        raise EmailSyntaxError("The email address contains unsafe characters: "
                               + ", ".join(safe_character_display(c) for c in sorted(bad_chars)) + ".")


def check_dot_atom(label, start_descr, end_descr, is_hostname):
    # RFC 2822 3.2.4
    if label.endswith("."):
        raise EmailSyntaxError(end_descr.format("period"))
    if label.startswith("."):
        raise EmailSyntaxError(start_descr.format("period"))
    if ".." in label:
        raise EmailSyntaxError("An email address cannot have two periods in a row.")

    if is_hostname:
        # RFC 952
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
    # (RFC 952 plus RFC 6531 section 3.3 for internationalized addresses)
    bad_chars = set(
        safe_character_display(c)
        for c in domain
        if not ATEXT_HOSTNAME_INTL.match(c)
    )
    if bad_chars:
        raise EmailSyntaxError("The part after the @-sign contains invalid characters: " + ", ".join(sorted(bad_chars)) + ".")

    # Check for unsafe characters.
    # Some of this may be redundant with the range U+0080 to U+10FFFF that is checked
    # by DOT_ATOM_TEXT_INTL. Other characters may be permitted by the email specs, but
    # they may not be valid, safe, or sensible Unicode strings.
    check_unsafe_chars(domain)

    # Perform UTS-46 normalization, which includes casefolding, NFC normalization,
    # and converting all label separators (the period/full stop, fullwidth full stop,
    # ideographic full stop, and halfwidth ideographic full stop) to basic periods.
    # It will also raise an exception if there is an invalid character in the input,
    # such as "⒈" which is invalid because it would expand to include a period.
    try:
        domain = idna.uts46_remap(domain, std3_rules=False, transitional=False)
    except idna.IDNAError as e:
        raise EmailSyntaxError(f"The part after the @-sign contains invalid characters ({e}).")

    # The domain part is made up period-separated "labels." Each label must
    # have at least one character and cannot start or end with dashes, which
    # means there are some surprising restrictions on periods and dashes.
    # Check that before we do IDNA encoding because the IDNA library gives
    # unfriendly errors for these cases, but after UTS-46 normalization because
    # it can insert periods and hyphens (from fullwidth characters).
    # (RFC 952, RFC 2822 3.2.4)
    check_dot_atom(domain, 'An email address cannot have a {} immediately after the @-sign.', 'An email address cannot end with a {}.', is_hostname=True)

    # Check for RFC 5890's invalid R-LDH labels, which are labels that start
    # with two characters other than "xn" and two dashes.
    for label in domain.split("."):
        if re.match(r"(?!xn)..--", label, re.I):
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
            raise EmailSyntaxError(f"The part after the @-sign contains invalid characters ({e}).")

        # Check the syntax of the string returned by idna.encode.
        # It should never fail.
        m = DOT_ATOM_TEXT_HOSTNAME.match(ascii_domain)
        if not m:
            raise EmailSyntaxError("The email address contains invalid characters after the @-sign after IDNA encoding.")

    # Check the length of the domain name in bytes.
    # (RFC 1035 2.3.4 and RFC 5321 4.5.3.1.2)
    # We're checking the number of bytes ("octets") here, which can be much
    # higher than the number of characters in internationalized domains,
    # on the assumption that the domain may be transmitted without SMTPUTF8
    # as IDNA ASCII. (This is also checked by idna.encode, so this exception
    # is never reached for internationalized domains.)
    if len(ascii_domain) > DOMAIN_MAX_LENGTH:
        reason = get_length_reason(ascii_domain, limit=DOMAIN_MAX_LENGTH)
        raise EmailSyntaxError(f"The email address is too long after the @-sign {reason}.")

    # Also check the label length limit.
    # (RFC 1035 2.3.1)
    for label in ascii_domain.split("."):
        if len(label) > DNS_LABEL_LENGTH_LIMIT:
            reason = get_length_reason(label, limit=DNS_LABEL_LENGTH_LIMIT)
            raise EmailSyntaxError(f"After the @-sign, periods cannot be separated by so many characters {reason}.")

    if globally_deliverable:
        # All publicly deliverable addresses have domain named with at least
        # one period, at least for gTLDs created since 2013 (per the ICANN Board
        # New gTLD Program Committee, https://www.icann.org/en/announcements/details/new-gtld-dotless-domain-names-prohibited-30-8-2013-en).
        # We'll consider the lack of a period a syntax error
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
    # See the references in __init__.py.
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
    # This gives us the canonical internationalized form of the domain.
    try:
        domain_i18n = idna.decode(ascii_domain.encode('ascii'))
    except idna.IDNAError as e:
        raise EmailSyntaxError(f"The part after the @-sign is not valid IDNA ({e}).")

    # Check for invalid characters after normalization. These
    # should never arise. See the similar checks above.
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
