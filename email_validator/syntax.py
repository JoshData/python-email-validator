from .exceptions import EmailSyntaxError
from .types import ValidatedEmail
from .rfc_constants import EMAIL_MAX_LENGTH, LOCAL_PART_MAX_LENGTH, DOMAIN_MAX_LENGTH, \
    DOT_ATOM_TEXT, DOT_ATOM_TEXT_INTL, ATEXT_RE, ATEXT_INTL_DOT_RE, ATEXT_HOSTNAME_INTL, QTEXT_INTL, \
    DNS_LABEL_LENGTH_LIMIT, DOT_ATOM_TEXT_HOSTNAME, DOMAIN_NAME_REGEX, DOMAIN_LITERAL_CHARS

import re
import unicodedata
import idna  # implements IDNA 2008; Python's codec is only IDNA 2003
import ipaddress
from typing import Optional, Tuple, TypedDict, Union


def split_email(email: str) -> Tuple[Optional[str], str, str, bool]:
    # Return the display name, unescaped local part, and domain part
    # of the address, and whether the local part was quoted. If no
    # display name was present and angle brackets do not surround
    # the address, display name will be None; otherwise, it will be
    # set to the display name or the empty string if there were
    # angle brackets but no display name.

    # Typical email addresses have a single @-sign and no quote
    # characters, but the awkward "quoted string" local part form
    # (RFC 5321 4.1.2) allows @-signs and escaped quotes to appear
    # in the local part if the local part is quoted.

    # A `display name <addr>` format is also present in MIME messages
    # (RFC 5322 3.4) and this format is also often recognized in
    # mail UIs. It's not allowed in SMTP commands or in typical web
    # login forms, but parsing it has been requested, so it's done
    # here as a convenience. It's implemented in the spirit but not
    # the letter of RFC 5322 3.4 because MIME messages allow newlines
    # and comments as a part of the CFWS rule, but this is typically
    # not allowed in mail UIs (although comment syntax was requested
    # once too).
    #
    # Display names are either basic characters (the same basic characters
    # permitted in email addresses, but periods are not allowed and spaces
    # are allowed; see RFC 5322 Appendix A.1.2), or or a quoted string with
    # the same rules as a quoted local part. (Multiple quoted strings might
    # be allowed? Unclear.) Optional space (RFC 5322 3.4 CFWS) and then the
    # email address follows in angle brackets.
    #
    # An initial quote is ambiguous between starting a display name or
    # a quoted local part --- fun.
    #
    # We assume the input string is already stripped of leading and
    # trailing CFWS.

    def split_string_at_unquoted_special(text: str, specials: Tuple[str, ...]) -> Tuple[str, str]:
        # Split the string at the first character in specials (an @-sign
        # or left angle bracket) that does not occur within quotes and
        # is not followed by a Unicode combining character.
        # If no special character is found, raise an error.
        inside_quote = False
        escaped = False
        left_part = ""
        for i, c in enumerate(text):
            # < plus U+0338 (Combining Long Solidus Overlay) normalizes to
            # ≮ U+226E (Not Less-Than), and  it would be confusing to treat
            # the < as the start of "<email>" syntax in that case. Likewise,
            # if anything combines with an @ or ", we should probably not
            # treat it as a special character.
            if unicodedata.normalize("NFC", text[i:])[0] != c:
                left_part += c

            elif inside_quote:
                left_part += c
                if c == '\\' and not escaped:
                    escaped = True
                elif c == '"' and not escaped:
                    # The only way to exit the quote is an unescaped quote.
                    inside_quote = False
                    escaped = False
                else:
                    escaped = False
            elif c == '"':
                left_part += c
                inside_quote = True
            elif c in specials:
                # When unquoted, stop before a special character.
                break
            else:
                left_part += c

        # No special symbol found. The special symbols always
        # include an at-sign, so this always indicates a missing
        # at-sign. The other symbol is optional.
        if len(left_part) == len(text):
            # The full-width at-sign might occur in CJK contexts.
            # We can't accept it because we only accept addresess
            # that are actually valid. But if this is common we
            # may want to consider accepting and normalizing full-
            # width characters for the other special symbols (and
            # full-width dot is already accepted in internationalized
            # domains) with a new option.
            # See https://news.ycombinator.com/item?id=42235268.
            if "＠" in text:
                raise EmailSyntaxError("The email address has the \"full-width\" at-sign (@) character instead of a regular at-sign.")

            # Check another near-homoglyph for good measure because
            # homoglyphs in place of required characters could be
            # very confusing. We may want to consider checking for
            # homoglyphs anywhere we look for a special symbol.
            if "﹫" in text:
                raise EmailSyntaxError('The email address has the "small commercial at" character instead of a regular at-sign.')

            raise EmailSyntaxError("An email address must have an @-sign.")

        # The right part is whatever is left.
        right_part = text[len(left_part):]

        return left_part, right_part

    def unquote_quoted_string(text: str) -> Tuple[str, bool]:
        # Remove surrounding quotes and unescape escaped backslashes
        # and quotes. Escapes are parsed liberally. I think only
        # backslashes and quotes can be escaped but we'll allow anything
        # to be.
        quoted = False
        escaped = False
        value = ""
        for i, c in enumerate(text):
            if quoted:
                if escaped:
                    value += c
                    escaped = False
                elif c == '\\':
                    escaped = True
                elif c == '"':
                    if i != len(text) - 1:
                        raise EmailSyntaxError("Extra character(s) found after close quote: "
                                               + ", ".join(safe_character_display(c) for c in text[i + 1:]))
                    break
                else:
                    value += c
            elif i == 0 and c == '"':
                quoted = True
            else:
                value += c

        return value, quoted

    # Split the string at the first unquoted @-sign or left angle bracket.
    left_part, right_part = split_string_at_unquoted_special(email, ("@", "<"))

    # If the right part starts with an angle bracket,
    # then the left part is a display name and the rest
    # of the right part up to the final right angle bracket
    # is the email address, .
    if right_part.startswith("<"):
        # Remove space between the display name and angle bracket.
        left_part = left_part.rstrip()

        # Unquote and unescape the display name.
        display_name, display_name_quoted = unquote_quoted_string(left_part)

        # Check that only basic characters are present in a
        # non-quoted display name.
        if not display_name_quoted:
            bad_chars = {
                safe_character_display(c)
                for c in display_name
                if (not ATEXT_RE.match(c) and c != ' ') or c == '.'
            }
            if bad_chars:
                raise EmailSyntaxError("The display name contains invalid characters when not quoted: " + ", ".join(sorted(bad_chars)) + ".")

        # Check for other unsafe characters.
        check_unsafe_chars(display_name, allow_space=True)

        # Check that the right part ends with an angle bracket
        # but allow spaces after it, I guess.
        if ">" not in right_part:
            raise EmailSyntaxError("An open angle bracket at the start of the email address has to be followed by a close angle bracket at the end.")
        right_part = right_part.rstrip(" ")
        if right_part[-1] != ">":
            raise EmailSyntaxError("There can't be anything after the email address.")

        # Remove the initial and trailing angle brackets.
        addr_spec = right_part[1:].rstrip(">")

        # Split the email address at the first unquoted @-sign.
        local_part, domain_part = split_string_at_unquoted_special(addr_spec, ("@",))

    # Otherwise there is no display name. The left part is the local
    # part and the right part is the domain.
    else:
        display_name = None
        local_part, domain_part = left_part, right_part

    if domain_part.startswith("@"):
        domain_part = domain_part[1:]

    # Unquote the local part if it is quoted.
    local_part, is_quoted_local_part = unquote_quoted_string(local_part)

    return display_name, local_part, domain_part, is_quoted_local_part


def get_length_reason(addr: str, limit: int) -> str:
    """Helper function to return an error message related to invalid length."""
    diff = len(addr) - limit
    suffix = "s" if diff > 1 else ""
    return f"({diff} character{suffix} too many)"


def safe_character_display(c: str) -> str:
    # Return safely displayable characters in quotes.
    if c == '\\':
        return f"\"{c}\""  # can't use repr because it escapes it
    if unicodedata.category(c)[0] in ("L", "N", "P", "S"):
        return repr(c)

    # Construct a hex string in case the unicode name doesn't exist.
    if ord(c) < 0xFFFF:
        h = f"U+{ord(c):04x}".upper()
    else:
        h = f"U+{ord(c):08x}".upper()

    # Return the character name or, if it has no name, the hex string.
    return unicodedata.name(c, h)


class LocalPartValidationResult(TypedDict):
    local_part: str
    ascii_local_part: Optional[str]
    smtputf8: bool


def validate_email_local_part(local: str, allow_smtputf8: bool = True, allow_empty_local: bool = False,
                              quoted_local_part: bool = False) -> LocalPartValidationResult:
    """Validates the syntax of the local part of an email address."""

    if len(local) == 0:
        if not allow_empty_local:
            raise EmailSyntaxError("There must be something before the @-sign.")

        # The caller allows an empty local part. Useful for validating certain
        # Postfix aliases.
        return {
            "local_part": local,
            "ascii_local_part": local,
            "smtputf8": False,
        }

    # Check the length of the local part by counting characters.
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
    # (RFC 5322 3.2.3)
    # All local parts matching the dot-atom rule are also valid as a quoted string
    # so if it was originally quoted (quoted_local_part is True) and this regex matches,
    # it's ok.
    # (RFC 5321 4.1.2 / RFC 5322 3.2.4).
    if DOT_ATOM_TEXT.match(local):
        # It's valid. And since it's just the permitted ASCII characters,
        # it's normalized and safe. If the local part was originally quoted,
        # the quoting was unnecessary and it'll be returned as normalized to
        # non-quoted form.

        # Return the local part and flag that SMTPUTF8 is not needed.
        return {
            "local_part": local,
            "ascii_local_part": local,
            "smtputf8": False,
        }

    # The local part failed the basic dot-atom check. Try the extended character set
    # for internationalized addresses. It's the same pattern but with additional
    # characters permitted.
    # RFC 6531 section 3.3.
    valid: Optional[str] = None
    requires_smtputf8 = False
    if DOT_ATOM_TEXT_INTL.match(local):
        # But international characters in the local part may not be permitted.
        if not allow_smtputf8:
            # Check for invalid characters against the non-internationalized
            # permitted character set.
            # (RFC 5322 3.2.3)
            bad_chars = {
                safe_character_display(c)
                for c in local
                if not ATEXT_RE.match(c)
            }
            if bad_chars:
                raise EmailSyntaxError("Internationalized characters before the @-sign are not supported: " + ", ".join(sorted(bad_chars)) + ".")

            # Although the check above should always find something, fall back to this just in case.
            raise EmailSyntaxError("Internationalized characters before the @-sign are not supported.")

        # It's valid.
        valid = "dot-atom"
        requires_smtputf8 = True

    # There are no syntactic restrictions on quoted local parts, so if
    # it was originally quoted, it is probably valid. More characters
    # are allowed, like @-signs, spaces, and quotes, and there are no
    # restrictions on the placement of dots, as in dot-atom local parts.
    elif quoted_local_part:
        # Check for invalid characters in a quoted string local part.
        # (RFC 5321 4.1.2. RFC 5322 lists additional permitted *obsolete*
        # characters which are *not* allowed here. RFC 6531 section 3.3
        # extends the range to UTF8 strings.)
        bad_chars = {
            safe_character_display(c)
            for c in local
            if not QTEXT_INTL.match(c)
        }
        if bad_chars:
            raise EmailSyntaxError("The email address contains invalid characters in quotes before the @-sign: " + ", ".join(sorted(bad_chars)) + ".")

        # See if any characters are outside of the ASCII range.
        bad_chars = {
            safe_character_display(c)
            for c in local
            if not (32 <= ord(c) <= 126)
        }
        if bad_chars:
            requires_smtputf8 = True

            # International characters in the local part may not be permitted.
            if not allow_smtputf8:
                raise EmailSyntaxError("Internationalized characters before the @-sign are not supported: " + ", ".join(sorted(bad_chars)) + ".")

        # It's valid.
        valid = "quoted"

    # If the local part matches the internationalized dot-atom form or was quoted,
    # perform additional checks for Unicode strings.
    if valid:
        # Check that the local part is a valid, safe, and sensible Unicode string.
        # Some of this may be redundant with the range U+0080 to U+10FFFF that is checked
        # by DOT_ATOM_TEXT_INTL and QTEXT_INTL. Other characters may be permitted by the
        # email specs, but they may not be valid, safe, or sensible Unicode strings.
        # See the function for rationale.
        check_unsafe_chars(local, allow_space=(valid == "quoted"))

        # Try encoding to UTF-8. Failure is possible with some characters like
        # surrogate code points, but those are checked above. Still, we don't
        # want to have an unhandled exception later.
        try:
            local.encode("utf8")
        except ValueError as e:
            raise EmailSyntaxError("The email address contains an invalid character.") from e

        # If this address passes only by the quoted string form, re-quote it
        # and backslash-escape quotes and backslashes (removing any unnecessary
        # escapes). Per RFC 5321 4.1.2, "all quoted forms MUST be treated as equivalent,
        # and the sending system SHOULD transmit the form that uses the minimum quoting possible."
        if valid == "quoted":
            local = '"' + re.sub(r'(["\\])', r'\\\1', local) + '"'

        return {
            "local_part": local,
            "ascii_local_part": local if not requires_smtputf8 else None,
            "smtputf8": requires_smtputf8,
        }

    # It's not a valid local part. Let's find out why.
    # (Since quoted local parts are all valid or handled above, these checks
    # don't apply in those cases.)

    # Check for invalid characters.
    # (RFC 5322 3.2.3, plus RFC 6531 3.3)
    bad_chars = {
        safe_character_display(c)
        for c in local
        if not ATEXT_INTL_DOT_RE.match(c)
    }
    if bad_chars:
        raise EmailSyntaxError("The email address contains invalid characters before the @-sign: " + ", ".join(sorted(bad_chars)) + ".")

    # Check for dot errors imposted by the dot-atom rule.
    # (RFC 5322 3.2.3)
    check_dot_atom(local, 'An email address cannot start with a {}.', 'An email address cannot have a {} immediately before the @-sign.', is_hostname=False)

    # All of the reasons should already have been checked, but just in case
    # we have a fallback message.
    raise EmailSyntaxError("The email address contains invalid characters before the @-sign.")


def check_unsafe_chars(s: str, allow_space: bool = False) -> None:
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
            # sensible because it would modify the @-sign.
            if i == 0:
                bad_chars.add(c)
        elif category == "Zs":
            # Spaces outside of the ASCII range are not specifically disallowed in
            # internationalized addresses as far as I can tell, but they violate
            # the spirit of the non-internationalized specification that email
            # addresses do not contain ASCII spaces when not quoted. Excluding
            # ASCII spaces when not quoted is handled directly by the atom regex.
            #
            # In quoted-string local parts, spaces are explicitly permitted, and
            # the ASCII space has category Zs, so we must allow it here, and we'll
            # allow all Unicode spaces to be consistent.
            if not allow_space:
                bad_chars.add(c)
        elif category[0] == "Z":
            # The two line and paragraph separator characters (in categories Zl and Zp)
            # are not specifically disallowed in internationalized addresses
            # as far as I can tell, but they violate the spirit of the non-internationalized
            # specification that email addresses do not contain line breaks when not quoted.
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


def check_dot_atom(label: str, start_descr: str, end_descr: str, is_hostname: bool) -> None:
    # RFC 5322 3.2.3
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


class DomainNameValidationResult(TypedDict):
    ascii_domain: str
    domain: str


def validate_email_domain_name(domain: str, test_environment: bool = False, globally_deliverable: bool = True) -> DomainNameValidationResult:
    """Validates the syntax of the domain part of an email address."""

    # Check for invalid characters.
    # (RFC 952 plus RFC 6531 section 3.3 for internationalized addresses)
    bad_chars = {
        safe_character_display(c)
        for c in domain
        if not ATEXT_HOSTNAME_INTL.match(c)
    }
    if bad_chars:
        raise EmailSyntaxError("The part after the @-sign contains invalid characters: " + ", ".join(sorted(bad_chars)) + ".")

    # Check for unsafe characters.
    # Some of this may be redundant with the range U+0080 to U+10FFFF that is checked
    # by DOT_ATOM_TEXT_INTL. Other characters may be permitted by the email specs, but
    # they may not be valid, safe, or sensible Unicode strings.
    check_unsafe_chars(domain)

    # Perform UTS-46 normalization, which includes casefolding, NFC normalization,
    # and converting all label separators (the period/full stop, fullwidth full stop,
    # ideographic full stop, and halfwidth ideographic full stop) to regular dots.
    # It will also raise an exception if there is an invalid character in the input,
    # such as "⒈" which is invalid because it would expand to include a dot and
    # U+1FEF which normalizes to a backtick, which is not an allowed hostname character.
    # Since several characters *are* normalized to a dot, this has to come before
    # checks related to dots, like check_dot_atom which comes next.
    original_domain = domain
    try:
        domain = idna.uts46_remap(domain, std3_rules=False, transitional=False)
    except idna.IDNAError as e:
        raise EmailSyntaxError(f"The part after the @-sign contains invalid characters ({e}).") from e

    # Check for invalid characters after Unicode normalization which are not caught
    # by uts46_remap (see tests for examples).
    bad_chars = {
        safe_character_display(c)
        for c in domain
        if not ATEXT_HOSTNAME_INTL.match(c)
    }
    if bad_chars:
        raise EmailSyntaxError("The part after the @-sign contains invalid characters after Unicode normalization: " + ", ".join(sorted(bad_chars)) + ".")

    # The domain part is made up dot-separated "labels." Each label must
    # have at least one character and cannot start or end with dashes, which
    # means there are some surprising restrictions on periods and dashes.
    # Check that before we do IDNA encoding because the IDNA library gives
    # unfriendly errors for these cases, but after UTS-46 normalization because
    # it can insert periods and hyphens (from fullwidth characters).
    # (RFC 952, RFC 1123 2.1, RFC 5322 3.2.3)
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
        # For ASCII-only domains, the transformation does nothing and is safe to
        # apply. However, to ensure we don't rely on the idna library for basic
        # syntax checks, we don't use it if it's not needed.
        #
        # idna.encode also checks the domain name length after encoding but it
        # doesn't give a nice error, so we call the underlying idna.alabel method
        # directly. idna.alabel checks label length and doesn't give great messages,
        # but we can't easily go to lower level methods.
        try:
            ascii_domain = ".".join(
                idna.alabel(label).decode("ascii")
                for label in domain.split(".")
            )
        except idna.IDNAError as e:
            # Some errors would have already been raised by idna.uts46_remap.
            raise EmailSyntaxError(f"The part after the @-sign is invalid ({e}).") from e

        # Check the syntax of the string returned by idna.encode.
        # It should never fail.
        if not DOT_ATOM_TEXT_HOSTNAME.match(ascii_domain):
            raise EmailSyntaxError("The email address contains invalid characters after the @-sign after IDNA encoding.")

    # Check the length of the domain name in bytes.
    # (RFC 1035 2.3.4 and RFC 5321 4.5.3.1.2)
    # We're checking the number of bytes ("octets") here, which can be much
    # higher than the number of characters in internationalized domains,
    # on the assumption that the domain may be transmitted without SMTPUTF8
    # as IDNA ASCII. (This is also checked by idna.encode, so this exception
    # is never reached for internationalized domains.)
    if len(ascii_domain) > DOMAIN_MAX_LENGTH:
        if ascii_domain == original_domain:
            reason = get_length_reason(ascii_domain, limit=DOMAIN_MAX_LENGTH)
            raise EmailSyntaxError(f"The email address is too long after the @-sign {reason}.")
        else:
            diff = len(ascii_domain) - DOMAIN_MAX_LENGTH
            s = "" if diff == 1 else "s"
            raise EmailSyntaxError(f"The email address is too long after the @-sign ({diff} byte{s} too many after IDNA encoding).")

    # Also check the label length limit.
    # (RFC 1035 2.3.1)
    for label in ascii_domain.split("."):
        if len(label) > DNS_LABEL_LENGTH_LIMIT:
            reason = get_length_reason(label, limit=DNS_LABEL_LENGTH_LIMIT)
            raise EmailSyntaxError(f"After the @-sign, periods cannot be separated by so many characters {reason}.")

    if globally_deliverable:
        # All publicly deliverable addresses have domain names with at least
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
    # This gives us the canonical internationalized form of the domain,
    # which we return to the caller as a part of the normalized email
    # address.
    try:
        domain_i18n = idna.decode(ascii_domain.encode('ascii'))
    except idna.IDNAError as e:
        raise EmailSyntaxError(f"The part after the @-sign is not valid IDNA ({e}).") from e

    # Check that this normalized domain name has not somehow become
    # an invalid domain name. All of the checks before this point
    # using the idna package probably guarantee that we now have
    # a valid international domain name in most respects. But it
    # doesn't hurt to re-apply some tests to be sure. See the similar
    # tests above.

    # Check for invalid and unsafe characters. We have no test
    # case for this.
    bad_chars = {
        safe_character_display(c)
        for c in domain
        if not ATEXT_HOSTNAME_INTL.match(c)
    }
    if bad_chars:
        raise EmailSyntaxError("The part after the @-sign contains invalid characters: " + ", ".join(sorted(bad_chars)) + ".")
    check_unsafe_chars(domain)

    # Check that it can be encoded back to IDNA ASCII. We have no test
    # case for this.
    try:
        idna.encode(domain_i18n)
    except idna.IDNAError as e:
        raise EmailSyntaxError(f"The part after the @-sign became invalid after normalizing to international characters ({e}).") from e

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


def validate_email_length(addrinfo: ValidatedEmail) -> None:
    # There are three forms of the email address whose length must be checked:
    #
    # 1) The original email address string. Since callers may continue to use
    #    this string, even though we recommend using the normalized form, we
    #    should not pass validation when the original input is not valid. This
    #    form is checked first because it is the original input.
    # 2) The normalized email address. We perform Unicode NFC normalization of
    #    the local part, we normalize the domain to internationalized characters
    #    (if originally IDNA ASCII) which also includes Unicode normalization,
    #    and we may remove quotes in quoted local parts. We recommend that
    #    callers use this string, so it must be valid.
    # 3) The email address with the IDNA ASCII representation of the domain
    #    name, since this string may be used with email stacks that don't
    #    support UTF-8. Since this is the least likely to be used by callers,
    #    it is checked last. Note that ascii_email will only be set if the
    #    local part is ASCII, but conceivably the caller may combine a
    #    internationalized local part with an ASCII domain, so we check this
    #    on that combination also. Since we only return the normalized local
    #    part, we use that (and not the unnormalized local part).
    #
    # In all cases, the length is checked in UTF-8 because the SMTPUTF8
    # extension to SMTP validates the length in bytes.

    addresses_to_check = [
        (addrinfo.original, None),
        (addrinfo.normalized, "after normalization"),
        ((addrinfo.ascii_local_part or addrinfo.local_part or "") + "@" + addrinfo.ascii_domain, "when the part after the @-sign is converted to IDNA ASCII"),
    ]

    for addr, reason in addresses_to_check:
        addr_len = len(addr)
        addr_utf8_len = len(addr.encode("utf8"))
        diff = addr_utf8_len - EMAIL_MAX_LENGTH
        if diff > 0:
            if reason is None and addr_len == addr_utf8_len:
                # If there is no normalization or transcoding,
                # we can give a simple count of the number of
                # characters over the limit.
                reason = get_length_reason(addr, limit=EMAIL_MAX_LENGTH)
            elif reason is None:
                # If there is no normalization but there is
                # some transcoding to UTF-8, we can compute
                # the minimum number of characters over the
                # limit by dividing the number of bytes over
                # the limit by the maximum number of bytes
                # per character.
                mbpc = max(len(c.encode("utf8")) for c in addr)
                mchars = max(1, diff // mbpc)
                suffix = "s" if diff > 1 else ""
                if mchars == diff:
                    reason = f"({diff} character{suffix} too many)"
                else:
                    reason = f"({mchars}-{diff} character{suffix} too many)"
            else:
                # Since there is normalization, the number of
                # characters in the input that need to change is
                # impossible to know.
                suffix = "s" if diff > 1 else ""
                reason += f" ({diff} byte{suffix} too many)"
            raise EmailSyntaxError(f"The email address is too long {reason}.")


class DomainLiteralValidationResult(TypedDict):
    domain_address: Union[ipaddress.IPv4Address, ipaddress.IPv6Address]
    domain: str


def validate_email_domain_literal(domain_literal: str) -> DomainLiteralValidationResult:
    # This is obscure domain-literal syntax. Parse it and return
    # a compressed/normalized address.
    # RFC 5321 4.1.3 and RFC 5322 3.4.1.

    addr: Union[ipaddress.IPv4Address, ipaddress.IPv6Address]

    # Try to parse the domain literal as an IPv4 address.
    # There is no tag for IPv4 addresses, so we can never
    # be sure if the user intends an IPv4 address.
    if re.match(r"^[0-9\.]+$", domain_literal):
        try:
            addr = ipaddress.IPv4Address(domain_literal)
        except ValueError as e:
            raise EmailSyntaxError(f"The address in brackets after the @-sign is not valid: It is not an IPv4 address ({e}) or is missing an address literal tag.") from e

        # Return the IPv4Address object and the domain back unchanged.
        return {
            "domain_address": addr,
            "domain": f"[{addr}]",
        }

    # If it begins with "IPv6:" it's an IPv6 address.
    if domain_literal.startswith("IPv6:"):
        try:
            addr = ipaddress.IPv6Address(domain_literal[5:])
        except ValueError as e:
            raise EmailSyntaxError(f"The IPv6 address in brackets after the @-sign is not valid ({e}).") from e

        # Return the IPv6Address object and construct a normalized
        # domain literal.
        return {
            "domain_address": addr,
            "domain": f"[IPv6:{addr.compressed}]",
        }

    # Nothing else is valid.

    if ":" not in domain_literal:
        raise EmailSyntaxError("The part after the @-sign in brackets is not an IPv4 address and has no address literal tag.")

    # The tag (the part before the colon) has character restrictions,
    # but since it must come from a registry of tags (in which only "IPv6" is defined),
    # there's no need to check the syntax of the tag. See RFC 5321 4.1.2.

    # Check for permitted ASCII characters. This actually doesn't matter
    # since there will be an exception after anyway.
    bad_chars = {
        safe_character_display(c)
        for c in domain_literal
        if not DOMAIN_LITERAL_CHARS.match(c)
    }
    if bad_chars:
        raise EmailSyntaxError("The part after the @-sign contains invalid characters in brackets: " + ", ".join(sorted(bad_chars)) + ".")

    # There are no other domain literal tags.
    # https://www.iana.org/assignments/address-literal-tags/address-literal-tags.xhtml
    raise EmailSyntaxError("The part after the @-sign contains an invalid address literal tag in brackets.")
