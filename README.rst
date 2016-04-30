email\_validator
================

A robust email address syntax and deliverability validation library
for Python 2.7/3.4 by `Joshua Tauberer <https://razor.occams.info>`__.

This library validates that address are of the form ``x@y.com``. This is
the sort of validation you would want for a login form on a website.

Key features:

* Good for validating email addresses used for logins/identity.
* Friendly error messages when validation fails (appropriate to show to end users).
* (optionally) Checks deliverability: Does the domain name resolve?
* Supports internationalized domain names and (optionally) internationalized local parts.
* Normalizes email addresses (super important for internationalized addresses! see below).

The library is NOT for validation of the To: line in an email message (e.g.
``My Name <my@address.com>``), which `flanker  <https://github.com/mailgun/flanker>`__
is more appropriate for. And this library does NOT permit obsolete
forms of email addresses, so if you need strict validation against the
email specs exactly, use `pyIsEmail  <https://github.com/michaelherold/pyIsEmail>`__.

The current version is 1.0.1 (March 6, 2016).

Installation
------------

This package is on PyPI, so:

::

    pip install email_validator

``pip3`` also works.

Usage
-----

If you're validating a user's email address before creating a user
account, you might do this:

::

    from email_validator import validate_email, EmailNotValidError

    email = "my+address@mydomain.tld"

    try:
        v = validate_email(email) # validate and get info
        email = v["email"] # replace with normalized form
    except EmailNotValidError as e:
        # email is not valid, exception message is human-readable
        print(str(e))

This validates the address and gives you its normalized form. You should
put the normalized form in your database and always normalize before
checking if an address is in your database.

The validator will accept internationalized email addresses, but email
addresses with non-ASCII characters in the *local* part of the address
(before the @-sign) require the `SMTPUTF8 <https://tools.ietf.org/html/rfc6531>`__
extension which may not be supported by your mail submission library or
your outbound mail server. If you know ahead of time that SMTPUTF8 is
not supported then **add the keyword argument allow_smtputf8=False
to fail validation for addresses that would require SMTPUTF8**:

::

        validate_email(email, allow_smtputf8=False)

Overview
--------

The module provides a function ``validate_email(email_address)`` which takes
an email address (either a ``str`` or ASCII ``bytes``) and:

-  Raises a ``EmailNotValidError`` with a helpful, human-readable error
   message explaining why the email address is not valid, or

-  Returns a dict with information about the deliverability of the email
   address.

When an email address is not valid, ``validate_email`` raises either an
``EmailSyntaxError`` if the form of the address is invalid or an
``EmailUndeliverableError`` if the domain name does not resolve. Both
exception classes are subclasses of ``EmailNotValidError``, which in
turn is a subclass of ``ValueError``.

But when an email address is valid, a dict is returned containing
information that might aid deliverability (see below).

The validator doesn't permit obsoleted forms of email addresses that no one
uses anymore even though they are still valid and deliverable, since they
will probably give you grief if you're using email for login. (See later in the
document about that.)

The validator checks that the domain name in the email address resolves.
There is nothing to be gained by trying to actually contact an SMTP
server, so that's not done here. For privacy, security, and practicality
reasons servers are good at not giving away whether an address is
deliverable or not: email addresses that appear to accept mail at first
can bounce mail after a delay, and bounced mail may indicate a temporary
failure of a good email address (sometimes an intentional failure, like
greylisting).

The function also accepts the following keyword arguments (default as
shown):

``allow_smtputf8=True``
  Set to ``False`` to prohibit internationalized
  addresses that would require the `SMTPUTF8 <https://tools.ietf.org/html/rfc6531>`__
  extension.

``check_deliverability=True``
  Set to ``False`` to skip the domain name resolution check.

``allow_empty_local=False``
  Set to ``True`` to allow an empty local
  part (i.e. ``@example.com``), e.g. for validating Postfix aliases.

Internationalized email addresses
---------------------------------

The email protocol SMTP and the domain name system DNS have historically
only allowed ASCII characters in email addresses and domain names,
respectively. Each has adapted to internationalization in a separate
way, creating two separate aspects to email address
internationalization.

Internationalized domain names (IDN)
''''''''''''''''''''''''''''''''''''

The first is `internationalized domain names (RFC
5891) <https://tools.ietf.org/html/rfc5891>`__, a.k.a IDNA 2008. The DNS system has not
been updated with Unicode support. Instead, internationalized domain
names are converted into a special IDNA ASCII form starting with
``xn--``. When an email address has non-ASCII characters in its domain
part, the domain part is replaced with its IDNA ASCII equivalent form
in the process of mail transmission. Your mail submission library probably
does this for you transparently. Note that most web browsers are currently
in transition between IDNA 2003 (RFC 3490) and IDNA 2008 (RFC 5891) and
`compliance around the web is not very good <http://archives.miloush.net/michkap/archive/2012/02/27/10273315.html>`__
in any case, so be aware that edge cases are handled differently by different
applications and libraries. This library conforms to IDNA 2008 using the
`idna <https://github.com/kjd/idna>`__ module by Kim Davies.

Internationalized local parts
'''''''''''''''''''''''''''''

The second sort of internationalization is internationalization in the
*local* part of the address (before the @-sign). These email addresses
require that your mail submission library and the mail servers along the
route to the destination, including your own outbound mail server, all
support the `SMTPUTF8 (RFC
6531) <https://tools.ietf.org/html/rfc6531>`__ extension. Support for
SMTPUTF8 varies.

How this module works
'''''''''''''''''''''

By default all internationalized forms are accepted by the validator.
But if you know ahead of time that SMTPUTF8 is not supported by your
mail submission stack, then you must filter out addresses that require
SMTPUTF8 using the ``allow_smtputf8=False`` keyword argument (see
above). This will cause the validation function to raise a
``EmailSyntaxError`` if delivery would require SMTPUTF8. That's just
in those cases where non-ASCII characters appear before the @-sign.
If you do not set ``allow_smtputf8=False``, you can also check the
value of the ``smtputf8`` field in the returned dict.

If your mail submission library doesn't support Unicode at all --- even
in the domain part of the address --- then immediately prior to mail
submission you must replace the email address with its ASCII-ized
form. This library gives you back the ASCII-ized form in the
``email_ascii`` field in the returned dict, which you can get like this:

::

    v = validate_email(email, allow_smtputf8=False)
    email = v['email_ascii']

The local part is left alone (if it has internationalized characters
``allow_smtputf8=False`` will force validation to fail) and the domain
part is converted to `IDNA
ASCII <https://tools.ietf.org/html/rfc5891>`__. (You probably should not
do this at account creation time so you don't change the user's login
information without telling them.)

Normalization
-------------

The use of Unicode in email addresses introduced a normalization problem.
Different Unicode strings can look identical and have the same semantic
meaning to the user. The ``email`` field returned on successful validation
provides the correctly normalized form of the given email address:

::

    v = validate_email(email)
    email = v['email']

Because you may get an email address in a variety of forms, you ought to replace
it with its normalized form immediately prior to going into your database
(during account creation), querying your database (during login), or sending
outbound mail.

The normalizations include lowercasing the domain part of the email address
(domain names are case-insensitive), `Unicode "NFC" normalization <https://en.wikipedia.org/wiki/Unicode_equivalence>`__
of the whole address (which turns characters plus `combining characters <https://en.wikipedia.org/wiki/Combining_character>`__
into precomposed characters where possible and replaces certain Unicode characters
(such as angstrom and ohm) with other equivalent code points (a-with-ring and omega,
respectively)), replacement of `fullwidth and halfwidth characters <https://en.wikipedia.org/wiki/Halfwidth_and_fullwidth_forms>`__
in the domain part, and possibly other `UTS46 <http://unicode.org/reports/tr46>`__ mappings
on the domain part.

(See `RFC 6532 (internationalized email) section 3.1 <https://tools.ietf.org/html/rfc6532#section-3.1>`__
and `RFC 5895 (IDNA 2008) section 2 <http://www.ietf.org/rfc/rfc5895.txt>`__.)

Examples
--------

For the email address ``test@example.org``, the returned dict is:

::

    {
      "email": "test@example.org",
      "email_ascii": "test@example.org",
      "local": "test",
      "domain": "example.org",
      "domain_i18n": "example.org",

      "smtputf8": false,

      "mx": [
        [
          0,
          "93.184.216.34"
        ]
      ],
      "mx-fallback": "A"
    }

For the fictitious address ``example@良好Mail.中国``, which has an
internationalized domain but ASCII local part, the returned dict is:

::

    {
      "email": "example@良好mail.中国",
      "email_ascii": "example@xn--mail-p86gl01s.xn--fiqs8s",
      "local": "example",
      "domain": "xn--mail-p86gl01s.xn--fiqs8s",
      "domain_i18n": "良好mail.中国",

      "smtputf8": false,

      "mx": [
        [
          0,
          "218.241.116.40"
        ]
      ],
      "mx-fallback": "A"
    }

Note that ``smtputf8`` is ``False`` even though the domain part is
internationalized because
`SMTPUTF8 <https://tools.ietf.org/html/rfc6531>`__ is only 
needed if the local part of the address is internationalized (the domain
part can be converted to IDNA ASCII). Also note that the ``email`` and
``domain_i18n`` fields provide a normalized form of the email address
and domain name (casefolding and Unicode normalization as required by
IDNA 2008).

For the fictitious address ``树大@occams.info``, which has an
internationalized local part, the returned dict is:

::

    {
      "email": "树大@occams.info",
      "local": "树大",
      "domain": "occams.info",
      "domain_i18n": "occams.info",

      "smtputf8": true,

      "mx": [
        [
          10,
          "box.occams.info"
        ]
      ],
      "mx-fallback": false
    }

Now ``smtputf8`` is ``True`` and ``email_ascii`` is missing because the
local part of the address is internationalized. The ``local`` and ``email``
fields return the normalized form of the address: certain Unicode characters
(such as angstrom and ohm) may be replaced by other equivalent code points
(a-with-ring and omega).

Return value
------------

When an email address passes validation, the fields in the returned dict
are:

``email``
   The canonical form of the email address, mostly useful for
   display purposes. This merely combines the ``local`` and
   ``domain_i18n`` fields (see below).

``email_ascii``
   If present, an ASCII-only form of the email address
   by replacing the domain part with `IDNA
   ASCII <https://tools.ietf.org/html/rfc5891>`__. This field will be
   present when an ASCII-only form of the email address exists
   (including if the email address is already ASCII). If the local part
   of the email address contains internationalized characters,
   ``email_ascii`` will not be present.

``local``
   The local part of the given email address (before the
   @-sign) with Unicode NFC normalization applied.

``domain``
   The `IDNA ASCII <https://tools.ietf.org/html/rfc5891>`__-encoded form of the
   domain part of the given email address (after the @-sign), as it
   would be transmitted on the wire.

``domain_i18n``
   The canonical internationalized form of
   the domain part of the address, by round-tripping through IDNA ASCII.
   If the returned string contains non-ASCII characters, either the
   `SMTPUTF8 <https://tools.ietf.org/html/rfc6531>`__ feature of MTAs
   will be required to transmit the message or else the email address('s
   domain part) must be converted to IDNA ASCII first (given in the
   returned ``domain`` field).

``smtputf8``
   A boolean indicating that the `SMTPUTF8 <https://tools.ietf.org/html/rfc6531>`__
   feature of MTAs will be required to transmit messages to this address because the
   local part of the address has non-ASCII characters (the local part
   cannot be IDNA-encoded). If ``allow_smtputf8=False`` is passed as an
   argument, this flag will always be false because an exception is raised
   if it would have been true.

``mx``
   A list of `(priority, domain)` tuples of MX records specified
   in the DNS for the domain (see `RFC 5321 section
   5 <https://tools.ietf.org/html/rfc5321#section-5>`__).

``mx-fallback``
   ``None`` if an ``MX`` record is found. If no MX
   records are actually specified in DNS and instead are inferred,
   through an obsolete mechanism, from A or AAAA records, the value is
   the type of DNS record used instead (``A`` or ``AAAA``).

Assumptions
-----------

By design, this validator does not pass all email addresses that
strictly conform to the standards. Many email address forms are obsolete
or likely to cause trouble:

-  The validator assumes the email address is intended to be deliverable
   on the public Internet using DNS, and so the domain part of the email
   address must be a resolvable domain name.
-  The "quoted string" form of the local part of the email address (RFC
   5321 4.1.2) is not permitted --- no one uses this anymore anyway.
   Quoted forms allow multiple @-signs, space characters, and other
   troublesome conditions.
-  The "literal" form for the domain part of an email address (an IP
   address) is not accepted --- no one uses this anymore anyway.

Testing
-------

A handful of valid email addresses are pasted in ``test_pass.txt``. Run
them through the validator (without deliverability checks) like so:

::

    python3 email_validator/__init__.py --tests < test_pass.txt

