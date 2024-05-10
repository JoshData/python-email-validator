from typing import Any, Dict, Iterator, Optional

import dns.exception
import dns.rdataset
import dns.resolver
import json
import os.path
import pytest

from email_validator.deliverability import caching_resolver

# To run deliverability checks without actually making
# DNS queries, we use a caching resolver where the cache
# is pre-loaded with DNS responses.

# When False, all DNS queries must come from the mocked
# data. When True, tests are run with live DNS queries
# and the DNS responses are saved to a file.
BUILD_MOCKED_DNS_RESPONSE_DATA = False


# This class implements the 'get' and 'put' methods
# expected for a dns.resolver.Resolver's cache.
class MockedDnsResponseData:
    DATA_PATH = os.path.dirname(__file__) + "/mocked-dns-answers.json"

    INSTANCE = None

    @staticmethod
    def create_resolver() -> dns.resolver.Resolver:
        if MockedDnsResponseData.INSTANCE is None:
            # Create a singleton instance of this class and load the saved DNS responses.
            # Except when BUILD_MOCKED_DNS_RESPONSE_DATA is true, don't load the data.
            singleton = MockedDnsResponseData()
            if not BUILD_MOCKED_DNS_RESPONSE_DATA:
                singleton.load()
            MockedDnsResponseData.INSTANCE = singleton

        # Return a new dns.resolver.Resolver configured for caching
        # using the singleton instance.
        dns_resolver = dns.resolver.Resolver(configure=BUILD_MOCKED_DNS_RESPONSE_DATA)
        return caching_resolver(cache=MockedDnsResponseData.INSTANCE, dns_resolver=dns_resolver)

    def __init__(self) -> None:
        self.data: Dict[dns.resolver.CacheKey, Optional[MockedDnsResponseData.Ans]] = {}

    # Loads the saved DNS response data from the JSON file and
    # re-structures it into dnspython classes.
    class Ans:  # mocks the dns.resolver.Answer class
        def __init__(self, rrset: dns.rdataset.Rdataset) -> None:
            self.rrset = rrset

        def __iter__(self) -> Iterator[Any]:
            return iter(self.rrset)

    def load(self) -> None:
        with open(self.DATA_PATH) as f:
            data = json.load(f)
            for item in data:
                key = (dns.name.from_text(item["query"]["name"] + "."),
                       dns.rdatatype.from_text(item["query"]["type"]),
                       dns.rdataclass.from_text(item["query"]["class"]))
                rdatas = [
                    dns.rdata.from_text(rdtype=key[1], rdclass=key[2], tok=rr)
                    for rr in item["answer"]
                ]
                if item["answer"]:
                    self.data[key] = MockedDnsResponseData.Ans(dns.rdataset.from_rdata_list(0, rdatas=rdatas))
                else:
                    self.data[key] = None

    def save(self) -> None:
        # Re-structure as a list with basic data types.
        data = [
            {
                "query": {
                    "name": key[0].to_text(omit_final_dot=True),
                    "type": dns.rdatatype.to_text(key[1]),
                    "class": dns.rdataclass.to_text(key[2]),
                },
                "answer": sorted([
                    rr.to_text()
                    for rr in value
                ])
            }
            for key, value in self.data.items()
            if value is not None
        ]
        with open(self.DATA_PATH, "w") as f:
            json.dump(data, f, indent=True)

    def get(self, key: dns.resolver.CacheKey) -> Optional[Ans]:
        # Special-case a domain to create a timeout.
        if key[0].to_text() == "timeout.com.":
            raise dns.exception.Timeout()  # type: ignore [no-untyped-call]

        # When building the DNS response database, return
        # a cache miss.
        if BUILD_MOCKED_DNS_RESPONSE_DATA:
            return None

        # Query the data for a matching record.
        if key in self.data:
            if not self.data[key]:
                raise dns.resolver.NoAnswer()  # type: ignore [no-untyped-call]
            return self.data[key]

        # Query the data for a response to an ANY query.
        ANY = dns.rdatatype.from_text("ANY")
        if (key[0], ANY, key[2]) in self.data and self.data[(key[0], ANY, key[2])] is None:
            raise dns.resolver.NXDOMAIN()  # type: ignore [no-untyped-call]

        raise ValueError(f"Saved DNS data did not contain query: {key}")

    def put(self, key: dns.resolver.CacheKey, value: Ans) -> None:
        # Build the DNS data by saving the live query response.
        if not BUILD_MOCKED_DNS_RESPONSE_DATA:
            raise ValueError("Should not get here.")
        self.data[key] = value


@pytest.fixture(scope="session", autouse=True)
def MockedDnsResponseDataCleanup(request: pytest.FixtureRequest) -> None:
    def cleanup_func() -> None:
        if BUILD_MOCKED_DNS_RESPONSE_DATA and MockedDnsResponseData.INSTANCE is not None:
            MockedDnsResponseData.INSTANCE.save()
    request.addfinalizer(cleanup_func)
