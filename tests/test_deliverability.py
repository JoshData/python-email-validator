import dns.resolver
import pytest
import re

from email_validator import EmailUndeliverableError, \
                            validate_email
from email_validator.deliverability import caching_resolver, validate_email_deliverability


def test_deliverability_found():
    response = validate_email_deliverability('gmail.com', 'gmail.com')
    assert response.keys() == {'mx', 'mx_fallback_type'}
    assert response['mx_fallback_type'] is None
    assert len(response['mx']) > 1
    assert len(response['mx'][0]) == 2
    assert isinstance(response['mx'][0][0], int)
    assert response['mx'][0][1].endswith('.com')


def test_deliverability_fails():
    # No MX record.
    domain = 'xkxufoekjvjfjeodlfmdfjcu.com'
    with pytest.raises(EmailUndeliverableError, match='The domain name {} does not exist'.format(domain)):
        validate_email_deliverability(domain, domain)

    # Null MX record.
    domain = 'example.com'
    with pytest.raises(EmailUndeliverableError, match='The domain name {} does not accept email'.format(domain)):
        validate_email_deliverability(domain, domain)


@pytest.mark.parametrize(
    'email_input',
    [
        ('me@mail.example'),
        ('me@example.com'),
        ('me@mail.example.com'),
    ],
)
def test_email_example_reserved_domain(email_input):
    # Since these all fail deliverabiltiy from a static list,
    # DNS deliverability checks do not arise.
    with pytest.raises(EmailUndeliverableError) as exc_info:
        validate_email(email_input)
    # print(f'({email_input!r}, {str(exc_info.value)!r}),')
    assert re.match(r"The domain name [a-z\.]+ does not (accept email|exist)\.", str(exc_info.value)) is not None


def test_deliverability_dns_timeout():
    validate_email_deliverability.TEST_CHECK_TIMEOUT = True
    response = validate_email_deliverability('gmail.com', 'gmail.com')
    assert "mx" not in response
    assert response.get("unknown-deliverability") == "timeout"
    validate_email('test@gmail.com')
    del validate_email_deliverability.TEST_CHECK_TIMEOUT


def test_validate_email__with_caching_resolver():
    # unittest.mock.patch("dns.resolver.LRUCache.get") doesn't
    # work --- it causes get to always return an empty list.
    # So we'll mock our own way.
    class MockedCache:
        get_called = False
        put_called = False

        def get(self, key):
            self.get_called = True
            return None

        def put(self, key, value):
            self.put_called = True

    # Test with caching_resolver helper method.
    mocked_cache = MockedCache()
    dns_resolver = caching_resolver(cache=mocked_cache)
    validate_email("test@gmail.com", dns_resolver=dns_resolver)
    assert mocked_cache.put_called
    validate_email("test@gmail.com", dns_resolver=dns_resolver)
    assert mocked_cache.get_called

    # Test with dns.resolver.Resolver instance.
    dns_resolver = dns.resolver.Resolver()
    dns_resolver.lifetime = 10
    dns_resolver.cache = MockedCache()
    validate_email("test@gmail.com", dns_resolver=dns_resolver)
    assert mocked_cache.put_called
    validate_email("test@gmail.com", dns_resolver=dns_resolver)
    assert mocked_cache.get_called
