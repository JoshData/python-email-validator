from typing import Any, Dict

import pytest
import re

from email_validator import EmailUndeliverableError, \
                            validate_email, caching_resolver
from email_validator.deliverability import validate_email_deliverability as validate_email_deliverability_async

from mocked_dns_response import MockedDnsResponseData, MockedDnsResponseDataCleanup  # noqa: F401

RESOLVER = MockedDnsResponseData.create_resolver()


async def validate_email_deliverability(*args, **kwargs):
    # The internal validate_email_deliverability method is
    # asynchronous but has no awaits if not passed an
    # async loop. To call it synchronously in tests,
    # we can drive a manual loop.
    try:
        validate_email_deliverability_async(*args, **kwargs).send(None)
        raise RuntimeError("validate_email_deliverability did not run synchronously.")
    except StopIteration as e:
        sync_result = e.value
    except Exception as e:
        sync_result = e

    # Do the same thing again asynchronously.
    try:
        async_result = await validate_email_deliverability_async(*args, **kwargs)
    except Exception as e:
        async_result = e

    # Check that the results match.
    # Not sure if repr() is really sufficient here.
    assert repr(sync_result) == repr(async_result)

    # Return the synchronous result for the caller's asserts.
    if isinstance(sync_result, Exception):
        raise sync_result
    return sync_result


@pytest.mark.parametrize(
    'domain,expected_response',
    [
        ('gmail.com', {'mx': [(5, 'gmail-smtp-in.l.google.com'), (10, 'alt1.gmail-smtp-in.l.google.com'), (20, 'alt2.gmail-smtp-in.l.google.com'), (30, 'alt3.gmail-smtp-in.l.google.com'), (40, 'alt4.gmail-smtp-in.l.google.com')], 'mx_fallback_type': None}),
        ('pages.github.com', {'mx': [(0, 'pages.github.com')], 'mx_fallback_type': 'A'}),
    ],
)
async def test_deliverability_found(domain: str, expected_response: str) -> None:
    response = await validate_email_deliverability(domain, domain, dns_resolver=RESOLVER)
    assert response == expected_response


@pytest.mark.parametrize(
    'domain,error',
    [
        ('xkxufoekjvjfjeodlfmdfjcu.com', 'The domain name {domain} does not exist'),
        ('example.com', 'The domain name {domain} does not accept email'),  # Null MX record
        ('g.mail.com', 'The domain name {domain} does not accept email'),  # No MX record but invalid AAAA record fallback (issue #134)
        ('nellis.af.mil', 'The domain name {domain} does not send email'),  # No MX record, A record fallback, reject-all SPF record.

        # No MX or A/AAAA records, but some other DNS records must
        # exist such that the response is NOANSWER instead of NXDOMAIN.
        ('justtxt.joshdata.me', 'The domain name {domain} does not accept email'),
    ],
)
def test_deliverability_fails(domain: str, error: str) -> None:
    with pytest.raises(EmailUndeliverableError, match=error.format(domain=domain)):
        validate_email_deliverability(domain, domain, dns_resolver=RESOLVER)


@pytest.mark.parametrize(
    'email_input',
    [
        ('me@mail.example'),
        ('me@example.com'),
        ('me@mail.example.com'),
    ],
)
def test_email_example_reserved_domain(email_input: str) -> None:
    # Since these all fail deliverabiltiy from a static list,
    # DNS deliverability checks do not arise.
    with pytest.raises(EmailUndeliverableError) as exc_info:
        validate_email(email_input, dns_resolver=RESOLVER)
    # print(f'({email_input!r}, {str(exc_info.value)!r}),')
    assert re.match(r"The domain name [a-z\.]+ does not (accept email|exist)\.", str(exc_info.value)) is not None


async def test_deliverability_dns_timeout() -> None:
    response = await validate_email_deliverability('timeout.com', 'timeout.com', dns_resolver=RESOLVER)
    assert "mx" not in response
    assert response.get("unknown-deliverability") == "timeout"


@pytest.mark.network
async def test_caching_dns_resolver() -> None:
    class TestCache:
        def __init__(self) -> None:
            self.cache: Dict[Any, Any] = {}

        def get(self, key: Any) -> Any:
            return self.cache.get(key)

        def put(self, key: Any, value: Any) -> Any:
            self.cache[key] = value

    cache = TestCache()
    resolver = caching_resolver(timeout=1, cache=cache)
    validate_email("test@gmail.com", dns_resolver=resolver)
    assert len(cache.cache) == 1

    validate_email("test@gmail.com", dns_resolver=resolver)
    assert len(cache.cache) == 1
