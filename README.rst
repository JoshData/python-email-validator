email\_validator
================

A robust email address syntax and deliverability validation library
for Python 2.7/3.x by `Joshua Tauberer <https://razor.occams.info>`__.

This library validates that address are of the form like ``x@y.com``,
e.g. what you would want in a login form on a website. There are other
forms of email addresses, like you would use when composing a message's
To: line e.g. ``My Name <my@address.com>``, that this library does not
accept. For that try `flanker  <https://github.com/mailgun/flanker>`__
instead.

This library is new and not well tested (and so *perhaps* not robust)
yet, but the goal is to be modern and complete.

Usage
-----

If you're validating a user's email address before creating a user
account, you might do this:

::

    from email_validator import validate_email, EmailNotValidError

    email = "my+address@mydomain.tld"

    try:
        validate_email(email)
        # OK, it's valid.
    except EmailNotValidError as e:
        print(str(e))

Support for internationalized email addresses varies. Email addresses
with non-ASCII characters in the *local* part of the address (before the
@-sign) require the `SMTPUTF8 <https://tools.ietf.org/html/rfc6531>`__
extension which may not be supported by your mail submission library or
your outbound mail server. If you know ahead of time that SMTPUTF8 is
not supported then **add the keyword argument ``allow_smtputf8=False``
to fail validation for addresses that would require SMTPUTF8**:

::

        validate_email(email, allow_smtputf8=False)

For a quick test of the library, you can also run it from the command
line:

::

    python3 email_validator.py example@良好mail.中国

Overview
--------

The module provides a function
``validate_email(email_address, allow_smtputf8=True|False)`` which takes
an email address (either a ``str`` or ASCII ``bytes``) and:

-  Raise a ``EmailNotValidError`` with a helpful, human-readable error
   message explaining why the email address is not valid, or

-  Returns a dict with information about the deliverability of the email
   address.

When an email address is not valid, ``validate_email`` raises either an
``EmailSyntaxError`` if the form of the address is invalid or an
``EmailUndeliverableError`` if the domain name does not resolve. Both
exception classes are subclasses of ``EmailNotValidError``, which in
turn is a subclass of ``ValueError``.

But when an email address is valid, a dict is returned containing
information that might aid deliverability.

The validator doesn't permit obsoleted forms of email addresses,
although they are still valid and deliverable, since they will probably
give you grief if you're using email for login. See later in the
document about that. If you need validation against the specs exactly,
you might like https://github.com/michaelherold/pyIsEmail.

There is nothing to be gained by trying to actually contact an SMTP
server, so that's not done here. For privacy, security, and practicality
reasons servers are good at not giving away whether an address is
deliverable or not: accepted mail may still bounce, and bounced mail may
indicate a temporary failure (sometimes an intentional failure, like
greylisting).

Internationalized email addresses
---------------------------------

The email protocol SMTP and the domain name system DNS have historically
only allowed ASCII characters in email addresses and domain names,
respectively. Each has adapted to internationalization in a separate
way, creating two separate aspects to email address
internationalization.

The first is `internationalized domain names (RFC
5891) <https://tools.ietf.org/html/rfc5891>`__. The DNS system has not
been updated with Unicode support. Instead, internationalized domain
names are converted into a special IDNA ASCII form starting with
``xn--``. When an email address has non-ASCII characters in its domain
part, the domain part can and should be replaced with its IDNA ASCII
form. Your mail submission library probably does this for you
transparently.

The second sort of internationalization is internationalization in the
*local* part of the address (before the @-sign). These email addresses
require that your mail submission library and the mail servers along the
route to the destination, including your own outbound mail server, all
support the `SMTPUTF8 (RFC
6531) <https://tools.ietf.org/html/rfc6531>`__ extension. Support for
SMTPUTF8 varies.

By default all internationalized forms are accepted by the validator.
But if you know ahead of time that SMTPUTF8 is not supported by your
mail submission stack, then you must filter out addresses that require
SMTPUTF8 using the ``allow_smtputf8=False`` keyword argument (see
above). This will cause the validation function to raise a
``EmailSyntaxError`` if delivery would require SMTPUTF8. If you do not
set ``allow_smtputf8=False``, you can also check the value of the
``smtputf8`` field in the returned dict.

If your mail submission library doesn't support Unicode at all --- even
in the domain part of the address --- then immediately prior to mail
submission you should replace the email address with the ASCII-ized
form. This library gives you back the ASCII-ized form in the
``email_ascii`` field in the returned dict, which you can get like this:

::

    email = validate_email(email, allow_smtputf8=False)['email_ascii']

The local part is left alone (if it has internationalized characters
``allow_smtputf8=False`` will force validation to fail) and the domain
part is converted to `IDNA
ASCII <https://tools.ietf.org/html/rfc5891>`__. (You probably should not
do this at account creation time so you don't change the user's login
information without telling them.)

If your mail submission library does support Unicode but doesn't
canonicalize addresses, you may want to replace addresses with their
canonical form immediately prior to mail submission or in other cases
when address rewriting is permitted:

::

    email = validate_email(email)['email']

Examples
--------

For the email address ``test@example.org``, the returned dict is:

::

    {
      "email": "test@example.org",
      "email_ascii": "test@example.org",
      "local": "test",
      "domain": "example.org",
      "domain_internationalized": "example.org",

      "smtputf8": false,

      "mx": [
        [
          0,
          "93.184.216.34"
        ]
      ],
      "mx-fallback": "A"
    }

For the fictitious address ``example@良好mail.中国``, which has an
internationalized domain but ASCII local part, the returned dict is:

::

    {
      "email": "example@良好mail.中国",
      "email_ascii": "example@xn--mail-p86gl01s.xn--fiqs8s",
      "local": "example",
      "domain": "xn--mail-p86gl01s.xn--fiqs8s",
      "domain_internationalized": "良好mail.中国",

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
`SMTPUTF8 <https://tools.ietf.org/html/rfc6531>`__ is only strictly
needed if the local part of the address is internationalized (the domain
part can be converted to IDNA ASCII).

For the fictitious address ``树大@occams.info``, which has an
internationalized local part, the returned dict is:

::

    {
      "local": "树大",
      "domain": "occams.info",
      "domain_internationalized": null,
      "smtputf8": True,

      "mx": [
        [
          10,
          "box.occams.info"
        ]
      ],
      "mx-fallback": False
    }

Now ``smtputf8`` is ``True`` and ``email_ascii`` is missing because the
local part of the address is internationalized.

Return value
------------

When an email address passes validation, the fields in the returned dict
are:

-  ``email``: The canonical form of the email address, mostly useful for
   display purposes. This merely combines the ``local`` and
   ``domain_internationalized`` fields.
-  ``email_ascii``: If present, an ASCII-only form of the email address
   by replacing the domain part with `IDNA
   ASCII <https://tools.ietf.org/html/rfc5891>`__. This field will be
   present when an ASCII-only form of the email address exists
   (including if the email address is already ASCII). If the local part
   of the email address contains internationalized characters,
   ``email_ascii`` will not be present.
-  ``local``: The local part of the given email address (before the
   @-sign) with Unicode NFC normalization applied, as suggested by `RFC
   6532 section
   3.1 <https://tools.ietf.org/html/rfc6532#section-3.1>`__.
-  ``domain``: The `IDNA
   ASCII <https://tools.ietf.org/html/rfc5891>`__-encoded form of the
   domain part of the given email address (after the @-sign), as it
   would be transmitted on the wire.
-  ``domain_internationalized``: The canonical internationalized form of
   the domain part of the address, by round-tripping through IDNA ASCII.
   If the returned string contains non-ASCII characters, either the
   `SMTPUTF8 <https://tools.ietf.org/html/rfc6531>`__ feature of MTAs
   will be required to transmit the message or else the email address('s
   domain part) must be converted to IDNA ASCII first (given in the
   returned ``domain`` field).
-  ``smtputf8`` is a boolean indicating that the
   `SMTPUTF8 <https://tools.ietf.org/html/rfc6531>`__ feature of MTAs
   will be required to transmit messages to this address because the
   local part of the address has non-ASCII characters (the local part
   cannot be IDNA-encoded).
-  ``mx`` is a list of (priority, domain) tuples of MX records specified
   in the DNS for the domain (see `RFC 5321 section
   5 <https://tools.ietf.org/html/rfc5321#section-5>`__).
-  ``mx-fallback`` is ``None`` if an ``MX`` record is found. If no MX
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

    python3 email_validator.py --test-pass < test_pass.txt

