import pytest

from email_validator import validate_email, EmailSyntaxError
# Let's test main but rename it to be clear
from email_validator.__main__ import main as validator_command_line_tool

from mocked_dns_response import MockedDnsResponseData, MockedDnsResponseDataCleanup  # noqa: F401

RESOLVER = MockedDnsResponseData.create_resolver()


def test_dict_accessor():
    input_email = "testaddr@example.tld"
    valid_email = validate_email(input_email, check_deliverability=False)
    assert isinstance(valid_email.as_dict(), dict)
    assert valid_email.as_dict()["original"] == input_email


def test_main_single_good_input(monkeypatch, capsys):
    import json
    test_email = "google@google.com"
    monkeypatch.setattr('sys.argv', ['email_validator', test_email])
    validator_command_line_tool(dns_resolver=RESOLVER)
    stdout, _ = capsys.readouterr()
    output = json.loads(str(stdout))
    assert isinstance(output, dict)
    assert validate_email(test_email, dns_resolver=RESOLVER).original == output["original"]


def test_main_single_bad_input(monkeypatch, capsys):
    bad_email = 'test@..com'
    monkeypatch.setattr('sys.argv', ['email_validator', bad_email])
    validator_command_line_tool(dns_resolver=RESOLVER)
    stdout, _ = capsys.readouterr()
    assert stdout == 'An email address cannot have a period immediately after the @-sign.\n'


def test_main_multi_input(monkeypatch, capsys):
    import io
    test_cases = ["google1@google.com", "google2@google.com", "test@.com", "test3@.com"]
    test_input = io.StringIO("\n".join(test_cases))
    monkeypatch.setattr('sys.stdin', test_input)
    monkeypatch.setattr('sys.argv', ['email_validator'])
    validator_command_line_tool(dns_resolver=RESOLVER)
    stdout, _ = capsys.readouterr()
    assert test_cases[0] not in stdout
    assert test_cases[1] not in stdout
    assert test_cases[2] in stdout
    assert test_cases[3] in stdout


def test_bytes_input():
    input_email = b"testaddr@example.tld"
    valid_email = validate_email(input_email, check_deliverability=False)
    assert isinstance(valid_email.as_dict(), dict)
    assert valid_email.as_dict()["normalized"] == input_email.decode("utf8")

    input_email = "testaddr中example.tld".encode("utf32")
    with pytest.raises(EmailSyntaxError):
        validate_email(input_email, check_deliverability=False)
