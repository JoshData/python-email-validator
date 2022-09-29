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


def __utf8_input_shim(input_str):
    if sys.version_info < (3,):
        return input_str.decode("utf-8")
    return input_str


def __utf8_output_shim(output_str):
    if sys.version_info < (3,):
        return unicode_class(output_str).encode("utf-8")
    return output_str


def main():
    if len(sys.argv) == 1:
        # Validate the email addresses pased line-by-line on STDIN.
        dns_resolver = caching_resolver()
        for line in sys.stdin:
            email = __utf8_input_shim(line.strip())
            try:
                validate_email(email, dns_resolver=dns_resolver)
            except EmailNotValidError as e:
                print(__utf8_output_shim("{} {}".format(email, e)))
    else:
        # Validate the email address passed on the command line.
        email = __utf8_input_shim(sys.argv[1])
        try:
            result = validate_email(email)
            print(json.dumps(result.as_dict(), indent=2, sort_keys=True, ensure_ascii=False))
        except EmailNotValidError as e:
            print(__utf8_output_shim(e))


if __name__ == "__main__":
    main()
