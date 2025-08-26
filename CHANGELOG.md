2.3.0 (August 26, 2025)
-----------------------

* The package name is changed from using an underscore (email_validator) to a dash (email-validator) to match PyPi's normalized package name.
* The library no longer checks that the local part is at most 64 characters because a more careful reading of RFC 5321 indicates the limit is optional and such email addresses have been found in the wild. However the check can be restored using a new `strict=True` parameter, and the overall 254 character email address length limit is still in place.
* New EmailSyntaxError messages are used for some exiting syntax errors related to @-sign homoglyphs and invalid characters in internationalized domains.
* When using `allow_display_name=True`, display names are now returned with Unicode NFC normalization.
* TypeError is now raised if something other than str (or bytes) is passed as the email address.

2.2.0 (June 20, 2024)
---------------------

* Email addresses with internationalized local parts could, with rare Unicode characters, be returned as valid but actually be invalid in their normalized form (returned in the `normalized` field). In particular, it is possible to get a normalized address with a ";" character, which is not valid and could change the interpretation of the address. Local parts now re-validated after Unicode NFC normalization to ensure that invalid characters cannot be injected into the normalized address and that characters with length-increasing NFC normalizations cannot cause a local part to exceed the maximum length after normalization. Thanks to khanh@calif.io from https://calif.io for reporting the issue.
* The length check for email addresses with internationalized local parts is now also applied to the original address string prior to Unicode NFC normalization, which may be longer and could exceed the maximum email address length, to protect callers who do not use the returned normalized address.
* Improved error message for IDNA domains that are too long or have invalid characters after Unicode normalization.
* A new option to parse `My Name <address@domain>` strings, i.e. a display name plus an email address in angle brackets, is now available. It is off by default.
* Improvements to Python typing.
* Some additional tests added.

2.1.2 (June 16, 2024)
---------------------

* The domain name length limit is corrected from 255 to 253 IDNA ASCII characters. I misread the RFCs.
* When a domain name has no MX record but does have an A or AAAA record, if none of the IP addresses in the response are globally reachable (i.e. not Private-Use, Loopback, etc.), the response is treated as if there was no A/AAAA response and the email address will fail the deliverability check.
* When a domain name has no MX record but does have an A or AAAA record, the mx field in the object returned by validate_email incorrectly held the IP addresses rather than the domain itself.
* Fixes in tests.

2.1.1 (February 26, 2024)
-------------------------

* Fixed typo 'marking' instead of 'marketing' in case-insensitive mailbox name list.
* When DNS-based deliverability checks fail, in some cases exceptions are now thrown with `raise ... from` for better nested exception tracking.
* Fixed tests to work when no local resolver can be configured.
* This project is now licensed under the Unlicense (instead of CC0).
* Minor improvements to tests.
* Minor improvements to code style.

2.1.0 (October 22, 2023)
------------------------

* Python 3.8+ is now required (support for Python 3.7 was dropped).
* The old `email` field on the returned `ValidatedEmail` object, which in the previous version was superseded by `normalized`, will now raise a deprecation warning if used. See https://stackoverflow.com/q/879173 for strategies to suppress the DeprecationWarning.
* A `__version__` module attribute is added.
* The email address argument to validate_email is now marked as positional-only to better reflect the documented usage using the new Python 3.8 feature.

2.0.0 (April 15, 2023)
----------------------

This is a major update to the library, but since email address specs haven't changed there should be no significant changes to which email addresses are considered valid or invalid with default options. There are new options for accepting unusual email addresses that were previously always rejected, some changes to how DNS errors are handled, many changes in error message text, and major internal improvements including the addition of type annotations. Python 3.7+ is now required. Details follow:

* Python 2.x and 3.x versions through 3.6, and dnspython 1.x, are no longer supported. Python 3.7+ with dnspython 2.x are now required.
* The dnspython package is no longer required if DNS checks are not used, although it will install automatically.
* NoNameservers and NXDOMAIN DNS errors are now handled differently: NoNameservers no longer fails validation, and NXDOMAIN now skips checking for an A/AAAA fallback and goes straight to failing validation.
* Some syntax error messages have changed because they are now checked explicitly rather than as a part of other checks.
* The quoted-string local part syntax (e.g. multiple @-signs, spaces, etc. if surrounded by quotes) and domain-literal addresses (e.g. @[192.XXX...] or @[IPv6:...]) are now parsed but not considered valid by default. Better error messages are now given for these addresses since it can be confusing for a technically valid address to be rejected, and new allow_quoted_local and allow_domain_literal options are added to allow these addresses if you really need them.
* Some other error messages have changed to not repeat the email address in the error message.
* The `email` field on the returned `ValidatedEmail` object has been renamed to `normalized` to be clearer about its importance, but access via `.email` is also still supported.
* Some mailbox names like `postmaster` are now normalized to lowercase per RFC 2142.
* The library has been reorganized internally into smaller modules.
* The tests have been reorganized and expanded. Deliverability tests now mostly use captured DNS responses so they can be run off-line.
* The __main__ tool now reads options to validate_email from environment variables.
* Type annotations have been added to the exported methods and the ValidatedEmail class and some internal methods.
* The old dict-like pattern for the return value of validate_email is deprecated.

Versions 2.0.0.post1 and 2.0.0.post2 corrected some packaging issues. 2.0.0.post2 also added a check for an invalid combination of arguments.

Version 1.3.1 (January 21, 2023)
--------------------------------

* The new SPF 'v=spf1 -all' (reject-all) deliverability check is removed in most cases. It now is performed only for domains that do not have MX records but do have an A/AAAA fallback record.

Version 1.3.0 (September 18, 2022)
----------------------------------

* Deliverability checks now check for 'v=spf1 -all' SPF records as a way to reject more bad domains.
* Special use domain names now raise EmailSyntaxError instead of EmailUndeliverableError since they are performed even if check_deliverability is off.
* New module-level attributes are added to override the default values of the keyword arguments and the special-use domains list.
* The keyword arguments of the public methods are now marked as keyword-only, ending support for Python 2.x.
* [pyIsEmail](https://github.com/michaelherold/pyIsEmail)'s test cases are added to the tests.
* Recommend that check_deliverability be set to False for validation on login pages.
* Added an undocumented globally_deliverable option.

Version 1.2.1 (May 1, 2022)
---------------------------

* example.com/net/org are removed from the special-use reserved domain names list so that they do not raise exceptions if check_deliverability is off.
* Improved README.

Version 1.2.0 (April 24, 2022)
------------------------------

* Reject domains with NULL MX records (when deliverability checks
  are turned on).
* Reject unsafe unicode characters. (Some of these checks you should
  be doing on all of your user inputs already!)
* Reject most special-use reserved domain names with EmailUndeliverableError. A new `test_environment` option is added for using `@*.test` domains.
* Improved safety of exception text by not repeating an unsafe input character in the message.
* Minor fixes in tests.
* Invoking the module as a standalone program now caches DNS queries.
* Improved README.

Version 1.1.3 (June 12, 2021)
-----------------------------

* Allow passing a custom dns_resolver so that a DNS cache and a custom timeout can be set.

Version 1.1.2 (Nov 5, 2020)
---------------------------

* Fix invoking the module as a standalone program.
* Fix deprecation warning in Python 3.8.
* Code improvements.
* Improved README.

Version 1.1.1 (May 19, 2020)
----------------------------

* Fix exception when DNS queries time-out.
* Improved README.

Version 1.1.0 (Spril 30, 2020)
------------------------------

* The main function now returns an object with attributes rather than a dict with keys, but accessing the object in the old way is still supported.
* Added overall email address length checks.
* Minor tweak to regular expressions.
* Improved error messages.
* Added tests.
* Linted source code files; changed README to Markdown.

Version 1.0.5 (Oct 18, 2019)
----------------------------

* Prevent resolving domain names as if they were not fully qualified using a local search domain settings.

Version 1.0.4 (May 2, 2019)
---------------------------

* Added a timeout argument for DNS queries.
* The wheel distribution is now a universal wheel.
* Improved README.

Version 1.0.3 (Sept 12, 2017)
-----------------------------

* Added a wheel distribution for easier installation.

Version 1.0.2 (Dec 30, 2016)
----------------------------

* Fix dnspython package name in Python 3.
* Improved README.

Version 1.0.1 (March 6, 2016)
-----------------------------

* Fixed minor errors.

Version 1.0.0 (Sept 5, 2015)
----------------------------

* Fail domains with a leading period.
* Improved error messages.
* Added tests.

Version 0.5.0 (June 15, 2015)
-----------------------------

* Use IDNA 2008 instead of IDNA 2003 and use the idna package's UTS46 normalization instead of our own.
* Fixes for Python 2.
* Improved error messages.
* Improved README.

Version 0.1.0 (April 21, 2015)
------------------------------

Initial release!
