import sys

# These constants are defined by the email specifications.

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
ATEXT_INTL = ATEXT + u"\u0080-\U0010FFFF"
DOT_ATOM_TEXT_INTL = '[' + ATEXT_INTL + ']+(?:\\.[' + ATEXT_INTL + ']+)*'

# The domain part of the email address, after IDNA (ASCII) encoding,
# must also satisfy the requirements of RFC 952/RFC 1123 which restrict
# the allowed characters of hostnames further. The hyphen cannot be at
# the beginning or end of a *dot-atom component* of a hostname either.
ATEXT_HOSTNAME = r'(?:(?:[a-zA-Z0-9][a-zA-Z0-9\-]*)?[a-zA-Z0-9])'

# Length constants
# RFC 3696 + errata 1003 + errata 1690 (https://www.rfc-editor.org/errata_search.php?rfc=3696&eid=1690)
# explains the maximum length of an email address is 254 octets.
EMAIL_MAX_LENGTH = 254
LOCAL_PART_MAX_LENGTH = 64
DOMAIN_MAX_LENGTH = 255


# In Python 2.x, turn the regexes above from bytes regexes into unicode
# regexes. If Python 3.x had a "ur" string literal prefix we'd use that instead.
if sys.version_info < (3,):
    ATEXT = ATEXT.decode("ascii")
    DOT_ATOM_TEXT = DOT_ATOM_TEXT.decode("ascii")
    ATEXT_HOSTNAME = ATEXT_HOSTNAME.decode("ascii")
