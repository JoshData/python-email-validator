# A command-line tool for testing.
#
# Usage:
#
# python -m email_validator
#
# Provide email addresses to validate either as a command-line argument
# or in STDIN separated by newlines. No output will be given for valid
# email addresses. Validation errors will be printed for invalid email
# addresses.

import json
import sys

from .validate_email import validate_email
from .deliverability import caching_resolver
from .exceptions_types import EmailNotValidError


def main(dns_resolver=None):
    # The dns_resolver argument is for tests.

    if len(sys.argv) == 1:
        # Validate the email addresses pased line-by-line on STDIN.
        dns_resolver = dns_resolver or caching_resolver()
        for line in sys.stdin:
            email = line.strip()
            try:
                validate_email(email, dns_resolver=dns_resolver)
            except EmailNotValidError as e:
                print("{} {}".format(email, e))
    else:
        # Validate the email address passed on the command line.
        email = sys.argv[1]
        try:
            result = validate_email(email, dns_resolver=dns_resolver)
            print(json.dumps(result.as_dict(), indent=2, sort_keys=True, ensure_ascii=False))
        except EmailNotValidError as e:
            print(e)


if __name__ == "__main__":
    main()
