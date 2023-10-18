# A command-line tool for testing.
#
# Usage:
#
# python -m email_validator test@example.org
# python -m email_validator < LIST_OF_ADDRESSES.TXT
#
# Provide email addresses to validate either as a single command-line argument
# or on STDIN separated by newlines.
#
# When passing an email address on the command line, if the email address
# is valid, information about it will be printed to STDOUT. If the email
# address is invalid, an error message will be printed to STDOUT and
# the exit code will be set to 1.
#
# When passsing email addresses on STDIN, validation errors will be printed
# for invalid email addresses. No output is given for valid email addresses.
# Validation errors are preceded by the email address that failed and a tab
# character. It is the user's responsibility to ensure email addresses
# do not contain tab or newline characters.
#
# Keyword arguments to validate_email can be set in environment variables
# of the same name but upprcase (see below).

import itertools
import json
import os
import sys
from typing import Any, Dict

from .deliverability import caching_async_resolver
from .exceptions_types import EmailNotValidError


def main_command_line(email_address, options, dns_resolver):
    # Validate the email address passed on the command line.

    from . import validate_email

    try:
        result = validate_email(email_address, dns_resolver=dns_resolver, **options)
        print(json.dumps(result.as_dict(), indent=2, sort_keys=True, ensure_ascii=False))
        return True
    except EmailNotValidError as e:
        print(e)
        return False


async def main_stdin(options, dns_resolver):
    # Validate the email addresses pased line-by-line on STDIN.
    # Chunk the addresses and call the async version of validate_email
    # for all the addresses in the chunk, and wait for the chunk
    # to complete.

    import asyncio

    from . import validate_email_async as validate_email

    dns_resolver = dns_resolver or caching_async_resolver()

    # https://stackoverflow.com/a/312467
    def split_seq(iterable, size):
        it = iter(iterable)
        item = list(itertools.islice(it, size))
        while item:
            yield item
            item = list(itertools.islice(it, size))

    CHUNK_SIZE = 25

    async def process_line(line):
        email = line.strip()
        try:
            await validate_email(email, dns_resolver=dns_resolver, **options)
            # If the email was valid, do nothing.
            return None
        except EmailNotValidError as e:
            return (email, e)

    chunks = split_seq(sys.stdin, CHUNK_SIZE)
    for chunk in chunks:
        awaitables = [process_line(line) for line in chunk]
        errors = await asyncio.gather(*awaitables)
        for error in errors:
            if error is not None:
                print(*error, sep='\t')


def main(dns_resolver=None):
    # The dns_resolver argument is for tests.

    # Set options from environment variables.
    options: Dict[str, Any] = {}
    for varname in ('ALLOW_SMTPUTF8', 'ALLOW_QUOTED_LOCAL', 'ALLOW_DOMAIN_LITERAL',
                    'GLOBALLY_DELIVERABLE', 'CHECK_DELIVERABILITY', 'TEST_ENVIRONMENT'):
        if varname in os.environ:
            options[varname.lower()] = bool(os.environ[varname])
    for varname in ('DEFAULT_TIMEOUT',):
        if varname in os.environ:
            options[varname.lower()] = float(os.environ[varname])

    if len(sys.argv) == 2:
        return main_command_line(sys.argv[1], options, dns_resolver)
    else:
        import asyncio
        asyncio.run(main_stdin(options, dns_resolver))
        return True


if __name__ == "__main__":
    if not main():
        sys.exit(1)
