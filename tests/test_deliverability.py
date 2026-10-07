from typing import Any, Optional
from types import SimpleNamespace

import dns.exception
import dns.resolver
import pytest
import re
import time

from email_validator import EmailUndeliverableError, \
                            validate_email, caching_resolver
from email_validator.deliverability import validate_email_deliverability

from mocked_dns_response import MockedDnsResponseData, MockedDnsResponseDataCleanup  # noqa: F401

RESOLVER = MockedDnsResponseData.create_resolver()


@pytest.mark.parametrize(
    'domain,expected_response',
    [
        ('gmail.com', {'mx': [(5, 'gmail-smtp-in.l.google.com'), (10, 'alt1.gmail-smtp-in.l.google.com'), (20, 'alt2.gmail-smtp-in.l.google.com'), (30, 'alt3.gmail-smtp-in.l.google.com'), (40, 'alt4.gmail-smtp-in.l.google.com')], 'mx_fallback_type': None}),
        ('pages.github.com', {'mx': [(0, 'pages.github.com')], 'mx_fallback_type': 'A'}),
    ],
)
def test_deliverability_found(domain: str, expected_response: str) -> None:
    response = validate_email_deliverability(domain, domain, dns_resolver=RESOLVER)
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
        ('ipv6only.joshdata.me', 'The domain name {domain} does not accept email'),
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


def test_deliverability_dns_timeout() -> None:
    response = validate_email_deliverability('timeout.com', 'timeout.com', dns_resolver=RESOLVER)
    assert "mx" not in response
    assert response.get("unknown-deliverability") == "timeout"


def test_timeout_and_resolver() -> None:
    with pytest.raises(ValueError, match="It's not valid to pass both timeout and dns_resolver."):
        validate_email_deliverability('timeout.com', 'timeout.com', timeout=1, dns_resolver=RESOLVER)


@pytest.fixture
def dns_clock(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    elapsed = [0.0]
    monkeypatch.setattr(time, 'monotonic', lambda: elapsed[0])
    return elapsed


@pytest.mark.parametrize('supplied_resolver', [False, True])
def test_dns_timeout_shared_across_queries(monkeypatch: pytest.MonkeyPatch, dns_clock: list[float], supplied_resolver: bool) -> None:
    resolver = MockedDnsResponseData.create_resolver()
    resolver.lifetime = 10 if supplied_resolver else 50
    calls: list[tuple[str, Optional[float]]] = []

    def resolve(domain: str, record_type: str, *, lifetime: Optional[float] = None) -> Any:
        calls.append((record_type, lifetime))
        budget = resolver.lifetime if lifetime is None else lifetime
        if budget < 9:
            dns_clock[0] += max(0, budget)
            raise dns.exception.Timeout
        dns_clock[0] += 9
        if record_type == 'AAAA':
            return [SimpleNamespace(address='2001:4860:4860::8888')]
        raise dns.resolver.NoAnswer

    monkeypatch.setattr(resolver, 'resolve', resolve)
    monkeypatch.setattr(dns.resolver, 'get_default_resolver', lambda: resolver)
    for _ in range(2):
        if supplied_resolver:
            response = validate_email_deliverability('deadline.example', 'deadline.example', dns_resolver=resolver)
        else:
            response = validate_email_deliverability('deadline.example', 'deadline.example', timeout=10)
        assert response == {'unknown-deliverability': 'timeout'}

    assert calls == [('MX', 10), ('A', 1)] * 2
    assert dns_clock[0] == 20
    assert resolver.lifetime == (10 if supplied_resolver else 50)


@pytest.mark.parametrize('supplied_resolver', [False, True])
@pytest.mark.parametrize('timeout', [0, -1, 10])
def test_cached_answers_preserve_resolver_lifetime(monkeypatch: pytest.MonkeyPatch, supplied_resolver: bool, timeout: int) -> None:
    resolver = MockedDnsResponseData.create_resolver()
    resolver.lifetime = timeout if supplied_resolver else 50
    monkeypatch.setattr(dns.resolver, 'get_default_resolver', lambda: resolver)
    if supplied_resolver:
        response = validate_email_deliverability('gmail.com', 'gmail.com', dns_resolver=resolver)
    else:
        response = validate_email_deliverability('gmail.com', 'gmail.com', timeout=timeout)

    assert response == {'mx': [(5, 'gmail-smtp-in.l.google.com'), (10, 'alt1.gmail-smtp-in.l.google.com'), (20, 'alt2.gmail-smtp-in.l.google.com'), (30, 'alt3.gmail-smtp-in.l.google.com'), (40, 'alt4.gmail-smtp-in.l.google.com')], 'mx_fallback_type': None}
    assert resolver.lifetime == (timeout if supplied_resolver else 50)


@pytest.mark.parametrize('supplied_resolver', [False, True])
def test_resolver_override_forwards_remaining_lifetime(monkeypatch: pytest.MonkeyPatch, dns_clock: list[float], supplied_resolver: bool) -> None:
    calls: list[tuple[str, Optional[float]]] = []

    class RecordingResolver(dns.resolver.Resolver):
        def resolve(self, qname: Any, rdtype: Any = 'A', *args: Any, **kwargs: Any) -> dns.resolver.Answer:
            calls.append((rdtype, kwargs.get('lifetime')))
            dns_clock[0] += 4
            return super().resolve(qname, rdtype, *args, **kwargs)

    resolver = RecordingResolver(configure=False)
    cache = MockedDnsResponseData.create_resolver().cache
    resolver.cache = cache
    resolver.lifetime = 10 if supplied_resolver else 50
    original_timeout = resolver.timeout
    monkeypatch.setattr(dns.resolver, 'get_default_resolver', lambda: resolver)
    monkeypatch.setattr('email_validator.DEFAULT_TIMEOUT', 10)
    if supplied_resolver:
        response = validate_email_deliverability('pages.github.com', 'pages.github.com', dns_resolver=resolver)
    else:
        response = validate_email_deliverability('pages.github.com', 'pages.github.com')

    assert response == {'mx': [(0, 'pages.github.com')], 'mx_fallback_type': 'A'}
    assert calls == [('MX', 10), ('A', 6), ('TXT', 2)]
    assert resolver.lifetime == (10 if supplied_resolver else 50)
    assert resolver.timeout == original_timeout
    assert resolver.cache is cache


@pytest.mark.parametrize('fallback', ['A', 'AAAA'])
@pytest.mark.parametrize('query_delay', [4, 10])
def test_dns_budget_allows_cached_fallback_after_expiry(monkeypatch: pytest.MonkeyPatch, dns_clock: list[float], fallback: str, query_delay: int) -> None:
    resolver = MockedDnsResponseData.create_resolver()
    resolver.lifetime = 10
    calls: list[tuple[str, Optional[float]]] = []

    def resolve(domain: str, record_type: str, *, lifetime: Optional[float] = None) -> Any:
        calls.append((record_type, lifetime))
        dns_clock[0] += query_delay
        if record_type == fallback:
            return [SimpleNamespace(address='2001:4860:4860::8888')]
        raise dns.resolver.NoAnswer

    monkeypatch.setattr(resolver, 'resolve', resolve)
    response = validate_email_deliverability('deadline.example', 'deadline.example', dns_resolver=resolver)
    assert response == {'mx': [(0, 'deadline.example')], 'mx_fallback_type': fallback}
    if query_delay == 10:
        if fallback == 'A':
            assert calls == [('MX', 10), ('A', 0), ('TXT', 0)]
        else:
            assert calls == [('MX', 10), ('A', 0), ('AAAA', 0), ('TXT', 0)]
    elif fallback == 'A':
        assert calls == [('MX', 10), ('A', 6), ('TXT', 2)]
    else:
        assert calls == [('MX', 10), ('A', 6), ('AAAA', 2), ('TXT', 0)]


@pytest.mark.parametrize('fallback', ['A', 'AAAA'])
def test_dns_timeout_discards_partial_fallback(monkeypatch: pytest.MonkeyPatch, dns_clock: list[float], fallback: str) -> None:
    resolver = MockedDnsResponseData.create_resolver()
    resolver.lifetime = 2 if fallback == 'A' else 3
    calls: list[tuple[str, Optional[float]]] = []

    def resolve(domain: str, record_type: str, *, lifetime: Optional[float] = None) -> Any:
        calls.append((record_type, lifetime))
        if record_type == 'TXT':
            raise dns.exception.Timeout
        dns_clock[0] += 1
        if record_type == fallback:
            return [SimpleNamespace(address='2001:4860:4860::8888')]
        raise dns.resolver.NoAnswer

    monkeypatch.setattr(resolver, 'resolve', resolve)
    response = validate_email_deliverability('deadline.example', 'deadline.example', dns_resolver=resolver)
    assert response == {'unknown-deliverability': 'timeout'}
    if fallback == 'A':
        assert calls == [('MX', 2), ('A', 1), ('TXT', 0)]
    else:
        assert calls == [('MX', 3), ('A', 2), ('AAAA', 1), ('TXT', 0)]


@pytest.mark.network
def test_caching_dns_resolver() -> None:
    class TestCache:
        def __init__(self) -> None:
            self.cache: dict[Any, Any] = {}

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
