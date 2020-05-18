# -*- coding: utf-8 -*-

import sys
import re
import unicodedata
import dns.resolver
import dns.exception
import idna  # implements IDNA 2008; Python's codec is only IDNA 2003


# Based on RFC 2822 section 3.2.4 / RFC 5322 section 3.2.3, these
# characters are permitted in email addresses (not taking into
# account internationalization):
ATEXT = r'a-zA-Z0-9_!#\$%&\'\*\+\-/=\?\^`\{\|\}~'

# A "dot atom text", per RFC 2822 3.2.4:
DOT_ATOM_TEXT = '[' + ATEXT + ']+(?:\\.[' + ATEXT + ']+)*'

# RFC 6531 section 3.3 extends the allowed characters in internationalized
# addresses to also include three specific ranges of UTF8 defined in
# RFC3629 section 4, which appear to be the Unicode code points from
# U+0080 to U+10FFFF.
ATEXT_UTF8 = ATEXT + u"\u0080-\U0010FFFF"
DOT_ATOM_TEXT_UTF8 = '[' + ATEXT_UTF8 + ']+(?:\\.[' + ATEXT_UTF8 + ']+)*'

# The domain part of the email address, after IDNA (ASCII) encoding,
# must also satisfy the requirements of RFC 952/RFC 1123 which restrict
# the allowed characters of hostnames further. The hyphen cannot be at
# the beginning or end of a *dot-atom component* of a hostname either.
ATEXT_HOSTNAME = r'(?:(?:[a-zA-Z0-9][a-zA-Z0-9\-]*)?[a-zA-Z0-9])'

# ease compatibility in type checking
if sys.version_info >= (3,):
    unicode_class = str
else:
    unicode_class = unicode  # noqa: F821

    # turn regexes to unicode (because 'ur' literals are not allowed in Py3)
    ATEXT = ATEXT.decode("ascii")
    DOT_ATOM_TEXT = DOT_ATOM_TEXT.decode("ascii")
    ATEXT_HOSTNAME = ATEXT_HOSTNAME.decode("ascii")

DEFAULT_TIMEOUT = 15  # secs


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
        if self.email == other.email and self.local_part == other.local_part and self.domain == other.domain \
           and self.ascii_email == other.ascii_email and self.ascii_local_part == other.ascii_local_part \
           and self.ascii_domain == other.ascii_domain \
           and self.smtputf8 == other.smtputf8 \
           and repr(sorted(self.mx) if self.mx else self.mx) == repr(sorted(other.mx) if other.mx else other.mx) \
           and self.mx_fallback_type == other.mx_fallback_type:
            return True
        return False

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


def validate_email(
    email,
    allow_smtputf8=True,
    allow_empty_local=False,
    check_deliverability=True,
    timeout=DEFAULT_TIMEOUT,
):
    """
    Validates an email address, raising an EmailNotValidError if the address is not valid or returning a dict of
    information when the address is valid. The email argument can be a str or a bytes instance,
    but if bytes it must be ASCII-only.
    """

    # Allow email to be a str or bytes instance. If bytes,
    # it must be ASCII because that's how the bytes work
    # on the wire with SMTP.
    if not isinstance(email, (str, unicode_class)):
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
    domain_part_info = validate_email_domain_part(parts[1])
    ret.domain = domain_part_info["domain"]
    ret.ascii_domain = domain_part_info["ascii_domain"]

    # Construct the complete normalized form.
    ret.email = ret.local_part + "@" + ret.domain

    # If the email address has an ASCII form, add it.
    if not ret.smtputf8:
        ret.ascii_email = ret.ascii_local_part + "@" + ret.ascii_domain

    # RFC 3696 + errata 1003 + errata 1690 (https://www.rfc-editor.org/errata_search.php?rfc=3696&eid=1690)
    # explains the maximum length of an email address is 254 octets.
    #
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
    if ret.ascii_email and len(ret.ascii_email) > 254:
        if ret.ascii_email == ret.email:
            reason = " ({} character{} too many)".format(
                len(ret.ascii_email) - 254,
                "s" if (len(ret.ascii_email) - 254 != 1) else ""
            )
        elif len(ret.email) > 254:
            # If there are more than 254 characters, then the ASCII
            # form is definitely going to be too long.
            reason = " (at least {} character{} too many)".format(
                len(ret.email) - 254,
                "s" if (len(ret.email) - 254 != 1) else ""
            )
        else:
            reason = " (when converted to IDNA ASCII)"
        raise EmailSyntaxError("The email address is too long{}.".format(reason))
    if len(ret.email.encode("utf8")) > 254:
        if len(ret.email) > 254:
            # If there are more than 254 characters, then the UTF-8
            # encoding is definitely going to be too long.
            reason = " (at least {} character{} too many)".format(
                len(ret.email) - 254,
                "s" if (len(ret.email) - 254 != 1) else ""
            )
        else:
            reason = " (when encoded in bytes)"
        raise EmailSyntaxError("The email address is too long{}.".format(reason))

    if check_deliverability:
        # Validate the email address's deliverability and update the
        # return dict with metadata.
        deliverability_info = validate_email_deliverability(ret["domain"], ret["domain_i18n"], timeout)
        if "mx" in deliverability_info:
            ret.mx = deliverability_info["mx"]
            ret.mx_fallback_type = deliverability_info["mx-fallback"]

    return ret


def validate_email_local_part(local, allow_smtputf8=True, allow_empty_local=False):
    # Validates the local part of an email address.

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
    if len(local) > 64:
        raise EmailSyntaxError("The email address is too long before the @-sign ({} character{} too many).".format(
            len(local) - 64,
            "s" if (len(local) - 64 != 1) else ""
        ))

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
        m = re.match(DOT_ATOM_TEXT_UTF8 + "\\Z", local)
        if not m:
            # It's not a valid internationalized address either. Report which characters were not valid.
            bad_chars = ', '.join(sorted(set(
                c for c in local if not re.match(u"[" + (ATEXT if not allow_smtputf8 else ATEXT_UTF8) + u"]", c)
            )))
            raise EmailSyntaxError("The email address contains invalid characters before the @-sign: %s." % bad_chars)

        # It would be valid if internationalized characters were allowed by the caller.
        if not allow_smtputf8:
            raise EmailSyntaxError("Internationalized characters before the @-sign are not supported.")

        # It's valid.

        # RFC 6532 section 3.1 also says that Unicode NFC normalization should be applied,
        # so we'll return the normalized local part in the return value.
        local = unicodedata.normalize("NFC", local)

        # Flag that SMTPUTF8 will be required for deliverability.
        return {
            "local_part": local,
            "ascii_local_part": None,  # no ASCII form is possible
            "smtputf8": True,
        }


def validate_email_domain_part(domain):
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

    # Regardless of whether international characters are actually used,
    # first convert to IDNA ASCII. For ASCII-only domains, the transformation
    # does nothing. If internationalized characters are present, the MTA
    # must either support SMTPUTF8 or the mail client must convert the
    # domain name to IDNA before submission.
    #
    # Unfortunately this step incorrectly 'fixes' domain names with leading
    # periods by removing them, so we have to check for this above. It also gives
    # a funky error message ("No input") when there are two periods in a
    # row, also checked separately above.
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

    # RFC 5321 4.5.3.1.2
    # We're checking the number of bytes (octets) here, which can be much
    # higher than the number of characters in internationalized domains,
    # on the assumption that the domain may be transmitted without SMTPUTF8
    # as IDNA ASCII. This is also checked by idna.encode, so this exception
    # is never reached.
    if len(ascii_domain) > 255:
        raise EmailSyntaxError("The email address is too long after the @-sign.")

    # A "dot atom text", per RFC 2822 3.2.4, but using the restricted
    # characters allowed in a hostname (see ATEXT_HOSTNAME above).
    DOT_ATOM_TEXT = ATEXT_HOSTNAME + r'(?:\.' + ATEXT_HOSTNAME + r')*'

    # Check the regular expression. This is probably entirely redundant
    # with idna.decode, which also checks this format.
    m = re.match(DOT_ATOM_TEXT + "\\Z", ascii_domain)
    if not m:
        raise EmailSyntaxError("The email address contains invalid characters after the @-sign.")

    # All publicly deliverable addresses have domain named with at least
    # one period. We also know that all TLDs end with a letter.
    if "." not in ascii_domain:
        raise EmailSyntaxError("The domain name %s is not valid. It should have a period." % domain_i18n)
    if not re.search(r"[A-Za-z]\Z", ascii_domain):
        raise EmailSyntaxError(
            "The domain name %s is not valid. It is not within a valid top-level domain." % domain_i18n
        )

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


def validate_email_deliverability(domain, domain_i18n, timeout=DEFAULT_TIMEOUT):
    # Check that the domain resolves to an MX record. If there is no MX record,
    # try an A or AAAA record which is a deprecated fallback for deliverability.

    # Add a trailing period to ensure the domain name is treated as fully qualified.
    domain += '.'

    try:
        # We need a way to check how timeouts are handled in the tests. So we
        # have a secret variable that if set makes this method always test the
        # handling of a timeout.
        if getattr(validate_email_deliverability, 'TEST_CHECK_TIMEOUT', False):
            raise dns.exception.Timeout()

        resolver = dns.resolver.get_default_resolver()

        if timeout:
            resolver.lifetime = timeout

        try:
            # Try resolving for MX records and get them in sorted priority order.
            response = dns.resolver.query(domain, "MX")
            mtas = sorted([(r.preference, str(r.exchange).rstrip('.')) for r in response])
            mx_fallback = None
        except (dns.resolver.NoNameservers, dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):

            # If there was no MX record, fall back to an A record.
            try:
                response = dns.resolver.query(domain, "A")
                mtas = [(0, str(r)) for r in response]
                mx_fallback = "A"
            except (dns.resolver.NoNameservers, dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):

                # If there was no A record, fall back to an AAAA record.
                try:
                    response = dns.resolver.query(domain, "AAAA")
                    mtas = [(0, str(r)) for r in response]
                    mx_fallback = "AAAA"
                except (dns.resolver.NoNameservers, dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):

                    # If there was no MX, A, or AAAA record, then mail to
                    # this domain is not deliverable.
                    raise EmailUndeliverableError("The domain name %s does not exist." % domain_i18n)

    except dns.exception.Timeout:
        # A timeout could occur for various reasons, so don't treat it as a failure.
        return {
            "unknown-deliverability": "timeout",
        }

    except EmailUndeliverableError:
        # Don't let these get clobbered by the wider except block below.
        raise

    except Exception as e:
        # Unhandled conditions should not propagate.
        raise EmailUndeliverableError(
            "There was an error while checking if the domain name in the email address is deliverable: " + str(e)
        )

    return {
        "mx": mtas,
        "mx-fallback": mx_fallback,
    }


def main():
    import sys
    import json

    if len(sys.argv) == 1:
        # Read lines for STDIN and validate the email address on each line.
        allow_smtputf8 = True
        for line in sys.stdin:
            try:
                email = line.strip()
                if sys.version_info < (3,):
                    email = email.decode("utf8")  # assume utf8 in input
                validate_email(email, allow_smtputf8=allow_smtputf8)
            except EmailNotValidError as e:
                print(email, e)
    else:
        # Validate the email address passed on the command line.
        email = sys.argv[1]
        allow_smtputf8 = True
        check_deliverability = True
        if sys.version_info < (3,):
            email = email.decode("utf8")  # assume utf8 in input
        try:
            result = validate_email(email, allow_smtputf8=allow_smtputf8, check_deliverability=check_deliverability)
            print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        except EmailNotValidError as e:
            if sys.version_info < (3,):
                print(unicode_class(e).encode("utf8"))
            else:
                print(e)


if __name__ == "__main__":
    main()
