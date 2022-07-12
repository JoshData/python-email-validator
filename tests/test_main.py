import dns.resolver
import re
import pytest
from email_validator import EmailSyntaxError, EmailUndeliverableError, \
                            validate_email, validate_email_deliverability, \
                            caching_resolver, ValidatedEmail
# Let's test main but rename it to be clear
from email_validator import main as validator_main


@pytest.mark.parametrize(
    'email_input,output',
    [
        (
            'Abc@example.tld',
            ValidatedEmail(
                local_part='Abc',
                ascii_local_part='Abc',
                smtputf8=False,
                ascii_domain='example.tld',
                domain='example.tld',
                email='Abc@example.tld',
                ascii_email='Abc@example.tld',
            ),
        ),
        (
            'Abc.123@test-example.com',
            ValidatedEmail(
                local_part='Abc.123',
                ascii_local_part='Abc.123',
                smtputf8=False,
                ascii_domain='test-example.com',
                domain='test-example.com',
                email='Abc.123@test-example.com',
                ascii_email='Abc.123@test-example.com',
            ),
        ),
        (
            'user+mailbox/department=shipping@example.tld',
            ValidatedEmail(
                local_part='user+mailbox/department=shipping',
                ascii_local_part='user+mailbox/department=shipping',
                smtputf8=False,
                ascii_domain='example.tld',
                domain='example.tld',
                email='user+mailbox/department=shipping@example.tld',
                ascii_email='user+mailbox/department=shipping@example.tld',
            ),
        ),
        (
            "!#$%&'*+-/=?^_`.{|}~@example.tld",
            ValidatedEmail(
                local_part="!#$%&'*+-/=?^_`.{|}~",
                ascii_local_part="!#$%&'*+-/=?^_`.{|}~",
                smtputf8=False,
                ascii_domain='example.tld',
                domain='example.tld',
                email="!#$%&'*+-/=?^_`.{|}~@example.tld",
                ascii_email="!#$%&'*+-/=?^_`.{|}~@example.tld",
            ),
        ),
        (
            '伊昭傑@郵件.商務',
            ValidatedEmail(
                local_part='伊昭傑',
                smtputf8=True,
                ascii_domain='xn--5nqv22n.xn--lhr59c',
                domain='郵件.商務',
                email='伊昭傑@郵件.商務',
            ),
        ),
        (
            'राम@मोहन.ईन्फो',
            ValidatedEmail(
                local_part='राम',
                smtputf8=True,
                ascii_domain='xn--l2bl7a9d.xn--o1b8dj2ki',
                domain='मोहन.ईन्फो',
                email='राम@मोहन.ईन्फो',
            ),
        ),
        (
            'юзер@екзампл.ком',
            ValidatedEmail(
                local_part='юзер',
                smtputf8=True,
                ascii_domain='xn--80ajglhfv.xn--j1aef',
                domain='екзампл.ком',
                email='юзер@екзампл.ком',
            ),
        ),
        (
            'θσερ@εχαμπλε.ψομ',
            ValidatedEmail(
                local_part='θσερ',
                smtputf8=True,
                ascii_domain='xn--mxahbxey0c.xn--xxaf0a',
                domain='εχαμπλε.ψομ',
                email='θσερ@εχαμπλε.ψομ',
            ),
        ),
        (
            '葉士豪@臺網中心.tw',
            ValidatedEmail(
                local_part='葉士豪',
                smtputf8=True,
                ascii_domain='xn--fiqq24b10vi0d.tw',
                domain='臺網中心.tw',
                email='葉士豪@臺網中心.tw',
            ),
        ),
        (
            'jeff@臺網中心.tw',
            ValidatedEmail(
                local_part='jeff',
                ascii_local_part='jeff',
                smtputf8=False,
                ascii_domain='xn--fiqq24b10vi0d.tw',
                domain='臺網中心.tw',
                email='jeff@臺網中心.tw',
                ascii_email='jeff@xn--fiqq24b10vi0d.tw',
            ),
        ),
        (
            '葉士豪@臺網中心.台灣',
            ValidatedEmail(
                local_part='葉士豪',
                smtputf8=True,
                ascii_domain='xn--fiqq24b10vi0d.xn--kpry57d',
                domain='臺網中心.台灣',
                email='葉士豪@臺網中心.台灣',
            ),
        ),
        (
            'jeff葉@臺網中心.tw',
            ValidatedEmail(
                local_part='jeff葉',
                smtputf8=True,
                ascii_domain='xn--fiqq24b10vi0d.tw',
                domain='臺網中心.tw',
                email='jeff葉@臺網中心.tw',
            ),
        ),
        (
            'ñoñó@example.tld',
            ValidatedEmail(
                local_part='ñoñó',
                smtputf8=True,
                ascii_domain='example.tld',
                domain='example.tld',
                email='ñoñó@example.tld',
            ),
        ),
        (
            '我買@example.tld',
            ValidatedEmail(
                local_part='我買',
                smtputf8=True,
                ascii_domain='example.tld',
                domain='example.tld',
                email='我買@example.tld',
            ),
        ),
        (
            '甲斐黒川日本@example.tld',
            ValidatedEmail(
                local_part='甲斐黒川日本',
                smtputf8=True,
                ascii_domain='example.tld',
                domain='example.tld',
                email='甲斐黒川日本@example.tld',
            ),
        ),
        (
            'чебурашкаящик-с-апельсинами.рф@example.tld',
            ValidatedEmail(
                local_part='чебурашкаящик-с-апельсинами.рф',
                smtputf8=True,
                ascii_domain='example.tld',
                domain='example.tld',
                email='чебурашкаящик-с-апельсинами.рф@example.tld',
            ),
        ),
        (
            'उदाहरण.परीक्ष@domain.with.idn.tld',
            ValidatedEmail(
                local_part='उदाहरण.परीक्ष',
                smtputf8=True,
                ascii_domain='domain.with.idn.tld',
                domain='domain.with.idn.tld',
                email='उदाहरण.परीक्ष@domain.with.idn.tld',
            ),
        ),
        (
            'ιωάννης@εεττ.gr',
            ValidatedEmail(
                local_part='ιωάννης',
                smtputf8=True,
                ascii_domain='xn--qxaa9ba.gr',
                domain='εεττ.gr',
                email='ιωάννης@εεττ.gr',
            ),
        ),
    ],
)
def test_email_valid(email_input, output):
    # print(f'({email_input!r}, {validate_email(email_input, check_deliverability=False)!r}),')
    assert validate_email(email_input, check_deliverability=False) == output


@pytest.mark.parametrize(
    'email_input,error_msg',
    [
        ('my@localhost', 'The domain name localhost is not valid. It should have a period.'),
        ('my@.leadingdot.com', 'An email address cannot have a period immediately after the @-sign.'),
        ('my@．．leadingfwdot.com', 'An email address cannot have a period immediately after the @-sign.'),
        ('my@..twodots.com', 'An email address cannot have a period immediately after the @-sign.'),
        ('my@twodots..com', 'An email address cannot have two periods in a row.'),
        ('my@baddash.-.com',
         'The domain name baddash.-.com contains invalid characters (Label must not start or end with a hyphen).'),
        ('my@baddash.-a.com',
         'The domain name baddash.-a.com contains invalid characters (Label must not start or end with a hyphen).'),
        ('my@baddash.b-.com',
         'The domain name baddash.b-.com contains invalid characters (Label must not start or end with a hyphen).'),
        ('my@example.com\n',
         'The domain name example.com\n contains invalid characters (Codepoint U+000A at position 4 of '
         '\'com\\n\' not allowed).'),
        ('my@example\n.com',
         'The domain name example\n.com contains invalid characters (Codepoint U+000A at position 8 of '
         '\'example\\n\' not allowed).'),
        ('.leadingdot@domain.com', 'The email address contains invalid characters before the @-sign: FULL STOP.'),
        ('..twodots@domain.com', 'The email address contains invalid characters before the @-sign: FULL STOP.'),
        ('twodots..here@domain.com', 'The email address contains invalid characters before the @-sign: FULL STOP.'),
        ('me@⒈wouldbeinvalid.com',
         "The domain name ⒈wouldbeinvalid.com contains invalid characters (Codepoint U+2488 not allowed "
         "at position 1 in '⒈wouldbeinvalid.com')."),
        ('@example.com', 'There must be something before the @-sign.'),
        ('\nmy@example.com', 'The email address contains invalid characters before the @-sign: \'\\n\'.'),
        ('m\ny@example.com', 'The email address contains invalid characters before the @-sign: \'\\n\'.'),
        ('my\n@example.com', 'The email address contains invalid characters before the @-sign: \'\\n\'.'),
        ('11111111112222222222333333333344444444445555555555666666666677777@example.com', 'The email address is too long before the @-sign (1 character too many).'),
        ('111111111122222222223333333333444444444455555555556666666666777777@example.com', 'The email address is too long before the @-sign (2 characters too many).'),
        ('me@1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.111111111122222222223333333333444444444455555555556.com', 'The email address is too long after the @-sign.'),
        ('my.long.address@1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.11111111112222222222333333333344444.info', 'The email address is too long (2 characters too many).'),
        ('my.long.address@λ111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.11111111112222222222333333.info', 'The email address is too long (when converted to IDNA ASCII).'),
        ('my.long.address@λ111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.1111111111222222222233333333334444.info', 'The email address is too long (at least 1 character too many).'),
        ('my.λong.address@1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.111111111122222222223333333333444.info', 'The email address is too long (when encoded in bytes).'),
        ('my.λong.address@1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.1111111111222222222233333333334444.info', 'The email address is too long (at least 1 character too many).'),
    ],
)
def test_email_invalid_syntax(email_input, error_msg):
    # Since these all have syntax errors, deliverability
    # checks do not arise.
    with pytest.raises(EmailSyntaxError) as exc_info:
        validate_email(email_input)
    # print(f'({email_input!r}, {str(exc_info.value)!r}),')
    assert str(exc_info.value) == error_msg


@pytest.mark.parametrize(
    'email_input',
    [
        ('me@anything.arpa'),
        ('me@valid.invalid'),
        ('me@link.local'),
        ('me@host.localhost'),
        ('me@onion.onion.onion'),
        ('me@test.test.test'),
    ],
)
def test_email_invalid_reserved_domain(email_input):
    # Since these all fail deliverabiltiy from a static list,
    # DNS deliverability checks do not arise.
    with pytest.raises(EmailSyntaxError) as exc_info:
        validate_email(email_input)
    # print(f'({email_input!r}, {str(exc_info.value)!r}),')
    assert "is a special-use or reserved name" in str(exc_info.value)


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


@pytest.mark.parametrize(
    'email_input',
    [
        ('white space@test'),
        ('\n@test'),
        ('\u2005@test'),  # four-per-em space (Zs)
        ('\u009C@test'),  # string terminator (Cc)
        ('\u200B@test'),  # zero-width space (Cf)
        ('\u202Dforward-\u202Ereversed@test'),  # BIDI (Cf)
        ('\uD800@test'),  # surrogate (Cs)
        ('\uE000@test'),  # private use (Co)
        ('\uFDEF@test'),  # unassigned (Cn)
    ],
)
def test_email_unsafe_character(email_input):
    # Check for various unsafe characters:
    with pytest.raises(EmailSyntaxError) as exc_info:
        validate_email(email_input, test_environment=True)
    assert "invalid character" in str(exc_info.value)


def test_email_test_domain_name_in_test_environment():
    validate_email("anything@test", test_environment=True)
    validate_email("anything@mycompany.test", test_environment=True)


# This is the pyIsEmail (https://github.com/michaelherold/pyIsEmail) test suite.
#
# The test data was extracted by:
#
# $ wget https://raw.githubusercontent.com/michaelherold/pyIsEmail/master/tests/data/tests.xml
# $ xmllint --xpath '/tests/test/address/text()' tests.xml  > t1
# $ xmllint --xpath "/tests/test[not(address='')]/diagnosis/text()" tests.xml > t2
#
# tests = []
# def fixup_char(c):
#  if ord(c) >= 0x2400 and ord(c) <= 0x2432:
#   c = chr(ord(c)-0x2400)
#  return c
# for email, diagnosis in zip(open("t1"), open("t2")):
#  email = email[:-1] # strip trailing \n but not more because trailing whitespace is significant
#  email = "".join(fixup_char(c) for c in email).replace("&amp;", "&")
#  tests.append([email, diagnosis.strip()])
# print(repr(tests).replace("'], ['", "'],\n['"))
@pytest.mark.parametrize(
    ('email_input', 'status'),
    [
        ['test', 'ISEMAIL_ERR_NODOMAIN'],
        ['@', 'ISEMAIL_ERR_NOLOCALPART'],
        ['test@', 'ISEMAIL_ERR_NODOMAIN'],
        # ['test@io', 'ISEMAIL_VALID'], # we reject domains without a dot, knowing they are not deliverable
        ['@io', 'ISEMAIL_ERR_NOLOCALPART'],
        ['@iana.org', 'ISEMAIL_ERR_NOLOCALPART'],
        ['test@iana.org', 'ISEMAIL_VALID'],
        ['test@nominet.org.uk', 'ISEMAIL_VALID'],
        ['test@about.museum', 'ISEMAIL_VALID'],
        ['a@iana.org', 'ISEMAIL_VALID'],
        ['test.test@iana.org', 'ISEMAIL_VALID'],
        ['.test@iana.org', 'ISEMAIL_ERR_DOT_START'],
        ['test.@iana.org', 'ISEMAIL_ERR_DOT_END'],
        ['test..iana.org', 'ISEMAIL_ERR_CONSECUTIVEDOTS'],
        ['test_exa-mple.com', 'ISEMAIL_ERR_NODOMAIN'],
        ['!#$%&`*+/=?^`{|}~@iana.org', 'ISEMAIL_VALID'],
        ['test\\@test@iana.org', 'ISEMAIL_ERR_EXPECTING_ATEXT'],
        ['123@iana.org', 'ISEMAIL_VALID'],
        ['test@123.com', 'ISEMAIL_VALID'],
        ['abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghiklm@iana.org', 'ISEMAIL_VALID'],
        ['abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghiklmn@iana.org', 'ISEMAIL_RFC5322_LOCAL_TOOLONG'],
        ['test@abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghiklm.com', 'ISEMAIL_RFC5322_LABEL_TOOLONG'],
        ['test@mason-dixon.com', 'ISEMAIL_VALID'],
        ['test@-iana.org', 'ISEMAIL_ERR_DOMAINHYPHENSTART'],
        ['test@iana-.com', 'ISEMAIL_ERR_DOMAINHYPHENEND'],
        ['test@g--a.com', 'ISEMAIL_VALID'],
        ['test@.iana.org', 'ISEMAIL_ERR_DOT_START'],
        ['test@iana.org.', 'ISEMAIL_ERR_DOT_END'],
        ['test@iana..com', 'ISEMAIL_ERR_CONSECUTIVEDOTS'],
        ['abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghiklm@abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghikl.abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghikl.abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghij', 'ISEMAIL_RFC5322_TOOLONG'],
        ['a@abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghikl.abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghikl.abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghikl.abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefg.hij', 'ISEMAIL_RFC5322_TOOLONG'],
        ['a@abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghikl.abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghikl.abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghikl.abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefg.hijk', 'ISEMAIL_RFC5322_DOMAIN_TOOLONG'],
        ['"test"@iana.org', 'ISEMAIL_RFC5321_QUOTEDSTRING'],
        ['""@iana.org', 'ISEMAIL_RFC5321_QUOTEDSTRING'],
        ['"""@iana.org', 'ISEMAIL_ERR_EXPECTING_ATEXT'],
        ['"\\a"@iana.org', 'ISEMAIL_RFC5321_QUOTEDSTRING'],
        ['"\\""@iana.org', 'ISEMAIL_RFC5321_QUOTEDSTRING'],
        ['"\\"@iana.org', 'ISEMAIL_ERR_UNCLOSEDQUOTEDSTR'],
        ['"\\\\"@iana.org', 'ISEMAIL_RFC5321_QUOTEDSTRING'],
        ['test"@iana.org', 'ISEMAIL_ERR_EXPECTING_ATEXT'],
        ['"test@iana.org', 'ISEMAIL_ERR_UNCLOSEDQUOTEDSTR'],
        ['"test"test@iana.org', 'ISEMAIL_ERR_ATEXT_AFTER_QS'],
        ['test"text"@iana.org', 'ISEMAIL_ERR_EXPECTING_ATEXT'],
        ['"test""test"@iana.org', 'ISEMAIL_ERR_EXPECTING_ATEXT'],
        ['"test"."test"@iana.org', 'ISEMAIL_DEPREC_LOCALPART'],
        ['"test\\ test"@iana.org', 'ISEMAIL_RFC5321_QUOTEDSTRING'],
        ['"test".test@iana.org', 'ISEMAIL_DEPREC_LOCALPART'],
        ['"test\x00"@iana.org', 'ISEMAIL_ERR_EXPECTING_QTEXT'],
        ['"test\\\x00"@iana.org', 'ISEMAIL_DEPREC_QP'],
        ['"abcdefghijklmnopqrstuvwxyz abcdefghijklmnopqrstuvwxyz abcdefghj"@iana.org', 'ISEMAIL_RFC5322_LOCAL_TOOLONG'],
        ['"abcdefghijklmnopqrstuvwxyz abcdefghijklmnopqrstuvwxyz abcdefg\\h"@iana.org', 'ISEMAIL_RFC5322_LOCAL_TOOLONG'],
        ['test@[255.255.255.255]', 'ISEMAIL_RFC5321_ADDRESSLITERAL'],
        ['test@a[255.255.255.255]', 'ISEMAIL_ERR_EXPECTING_ATEXT'],
        ['test@[255.255.255]', 'ISEMAIL_RFC5322_DOMAINLITERAL'],
        ['test@[255.255.255.255.255]', 'ISEMAIL_RFC5322_DOMAINLITERAL'],
        ['test@[255.255.255.256]', 'ISEMAIL_RFC5322_DOMAINLITERAL'],
        ['test@[1111:2222:3333:4444:5555:6666:7777:8888]', 'ISEMAIL_RFC5322_DOMAINLITERAL'],
        ['test@[IPv6:1111:2222:3333:4444:5555:6666:7777]', 'ISEMAIL_RFC5322_IPV6_GRPCOUNT'],
        ['test@[IPv6:1111:2222:3333:4444:5555:6666:7777:8888]', 'ISEMAIL_RFC5321_ADDRESSLITERAL'],
        ['test@[IPv6:1111:2222:3333:4444:5555:6666:7777:8888:9999]', 'ISEMAIL_RFC5322_IPV6_GRPCOUNT'],
        ['test@[IPv6:1111:2222:3333:4444:5555:6666:7777:888G]', 'ISEMAIL_RFC5322_IPV6_BADCHAR'],
        ['test@[IPv6:1111:2222:3333:4444:5555:6666::8888]', 'ISEMAIL_RFC5321_IPV6DEPRECATED'],
        ['test@[IPv6:1111:2222:3333:4444:5555::8888]', 'ISEMAIL_RFC5321_ADDRESSLITERAL'],
        ['test@[IPv6:1111:2222:3333:4444:5555:6666::7777:8888]', 'ISEMAIL_RFC5322_IPV6_MAXGRPS'],
        ['test@[IPv6::3333:4444:5555:6666:7777:8888]', 'ISEMAIL_RFC5322_IPV6_COLONSTRT'],
        ['test@[IPv6:::3333:4444:5555:6666:7777:8888]', 'ISEMAIL_RFC5321_ADDRESSLITERAL'],
        ['test@[IPv6:1111::4444:5555::8888]', 'ISEMAIL_RFC5322_IPV6_2X2XCOLON'],
        ['test@[IPv6:::]', 'ISEMAIL_RFC5321_ADDRESSLITERAL'],
        ['test@[IPv6:1111:2222:3333:4444:5555:255.255.255.255]', 'ISEMAIL_RFC5322_IPV6_GRPCOUNT'],
        ['test@[IPv6:1111:2222:3333:4444:5555:6666:255.255.255.255]', 'ISEMAIL_RFC5321_ADDRESSLITERAL'],
        ['test@[IPv6:1111:2222:3333:4444:5555:6666:7777:255.255.255.255]', 'ISEMAIL_RFC5322_IPV6_GRPCOUNT'],
        ['test@[IPv6:1111:2222:3333:4444::255.255.255.255]', 'ISEMAIL_RFC5321_ADDRESSLITERAL'],
        ['test@[IPv6:1111:2222:3333:4444:5555:6666::255.255.255.255]', 'ISEMAIL_RFC5322_IPV6_MAXGRPS'],
        ['test@[IPv6:1111:2222:3333:4444:::255.255.255.255]', 'ISEMAIL_RFC5322_IPV6_2X2XCOLON'],
        ['test@[IPv6::255.255.255.255]', 'ISEMAIL_RFC5322_IPV6_COLONSTRT'],
        [' test @iana.org', 'ISEMAIL_DEPREC_CFWS_NEAR_AT'],
        ['test@ iana .com', 'ISEMAIL_DEPREC_CFWS_NEAR_AT'],
        ['test . test@iana.org', 'ISEMAIL_DEPREC_FWS'],
        ['\r\n test@iana.org', 'ISEMAIL_CFWS_FWS'],
        ['\r\n \r\n test@iana.org', 'ISEMAIL_DEPREC_FWS'],
        ['(comment)test@iana.org', 'ISEMAIL_CFWS_COMMENT'],
        ['((comment)test@iana.org', 'ISEMAIL_ERR_UNCLOSEDCOMMENT'],
        ['(comment(comment))test@iana.org', 'ISEMAIL_CFWS_COMMENT'],
        ['test@(comment)iana.org', 'ISEMAIL_DEPREC_CFWS_NEAR_AT'],
        ['test(comment)test@iana.org', 'ISEMAIL_ERR_ATEXT_AFTER_CFWS'],
        ['test@(comment)[255.255.255.255]', 'ISEMAIL_DEPREC_CFWS_NEAR_AT'],
        ['(comment)abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghiklm@iana.org', 'ISEMAIL_CFWS_COMMENT'],
        ['test@(comment)abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghikl.com', 'ISEMAIL_DEPREC_CFWS_NEAR_AT'],
        ['(comment)test@abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghik.abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghik.abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.abcdefghijklmnopqrstuvwxyzabcdefghijk.abcdefghijklmnopqrstu', 'ISEMAIL_CFWS_COMMENT'],
        ['test@iana.org\n', 'ISEMAIL_ERR_EXPECTING_ATEXT'],
        ['test@xn--hxajbheg2az3al.xn--jxalpdlp', 'ISEMAIL_VALID'],
        ['xn--test@iana.org', 'ISEMAIL_VALID'],
        ['test@iana.org-', 'ISEMAIL_ERR_DOMAINHYPHENEND'],
        ['"test@iana.org', 'ISEMAIL_ERR_UNCLOSEDQUOTEDSTR'],
        ['(test@iana.org', 'ISEMAIL_ERR_UNCLOSEDCOMMENT'],
        ['test@(iana.org', 'ISEMAIL_ERR_UNCLOSEDCOMMENT'],
        ['test@[1.2.3.4', 'ISEMAIL_ERR_UNCLOSEDDOMLIT'],
        ['"test\\"@iana.org', 'ISEMAIL_ERR_UNCLOSEDQUOTEDSTR'],
        ['(comment\\)test@iana.org', 'ISEMAIL_ERR_UNCLOSEDCOMMENT'],
        ['test@iana.org(comment\\)', 'ISEMAIL_ERR_UNCLOSEDCOMMENT'],
        ['test@iana.org(comment\\', 'ISEMAIL_ERR_BACKSLASHEND'],
        ['test@[RFC-5322-domain-literal]', 'ISEMAIL_RFC5322_DOMAINLITERAL'],
        ['test@[RFC-5322]-domain-literal]', 'ISEMAIL_ERR_ATEXT_AFTER_DOMLIT'],
        ['test@[RFC-5322-[domain-literal]', 'ISEMAIL_ERR_EXPECTING_DTEXT'],
        ['test@[RFC-5322-\\\x07-domain-literal]', 'ISEMAIL_RFC5322_DOMLIT_OBSDTEXT'],
        ['test@[RFC-5322-\\\t-domain-literal]', 'ISEMAIL_RFC5322_DOMLIT_OBSDTEXT'],
        ['test@[RFC-5322-\\]-domain-literal]', 'ISEMAIL_RFC5322_DOMLIT_OBSDTEXT'],
        ['test@[RFC-5322-domain-literal\\]', 'ISEMAIL_ERR_UNCLOSEDDOMLIT'],
        ['test@[RFC-5322-domain-literal\\', 'ISEMAIL_ERR_BACKSLASHEND'],
        ['test@[RFC 5322 domain literal]', 'ISEMAIL_RFC5322_DOMAINLITERAL'],
        ['test@[RFC-5322-domain-literal] (comment)', 'ISEMAIL_RFC5322_DOMAINLITERAL'],
        ['\x7f@iana.org', 'ISEMAIL_ERR_EXPECTING_ATEXT'],
        ['test@\x7f.org', 'ISEMAIL_ERR_EXPECTING_ATEXT'],
        ['"\x7f"@iana.org', 'ISEMAIL_DEPREC_QTEXT'],
        ['"\\\x7f"@iana.org', 'ISEMAIL_DEPREC_QP'],
        ['(\x7f)test@iana.org', 'ISEMAIL_DEPREC_CTEXT'],
        ['test@iana.org\r', 'ISEMAIL_ERR_CR_NO_LF'],
        ['\rtest@iana.org', 'ISEMAIL_ERR_CR_NO_LF'],
        ['"\rtest"@iana.org', 'ISEMAIL_ERR_CR_NO_LF'],
        ['(\r)test@iana.org', 'ISEMAIL_ERR_CR_NO_LF'],
        ['test@iana.org(\r)', 'ISEMAIL_ERR_CR_NO_LF'],
        ['\ntest@iana.org', 'ISEMAIL_ERR_EXPECTING_ATEXT'],
        ['"\n"@iana.org', 'ISEMAIL_ERR_EXPECTING_QTEXT'],
        ['"\\\n"@iana.org', 'ISEMAIL_DEPREC_QP'],
        ['(\n)test@iana.org', 'ISEMAIL_ERR_EXPECTING_CTEXT'],
        ['\x07@iana.org', 'ISEMAIL_ERR_EXPECTING_ATEXT'],
        ['test@\x07.org', 'ISEMAIL_ERR_EXPECTING_ATEXT'],
        ['"\x07"@iana.org', 'ISEMAIL_DEPREC_QTEXT'],
        ['"\\\x07"@iana.org', 'ISEMAIL_DEPREC_QP'],
        ['(\x07)test@iana.org', 'ISEMAIL_DEPREC_CTEXT'],
        ['\r\ntest@iana.org', 'ISEMAIL_ERR_FWS_CRLF_END'],
        ['\r\n \r\ntest@iana.org', 'ISEMAIL_ERR_FWS_CRLF_END'],
        [' \r\ntest@iana.org', 'ISEMAIL_ERR_FWS_CRLF_END'],
        [' \r\n test@iana.org', 'ISEMAIL_CFWS_FWS'],
        [' \r\n \r\ntest@iana.org', 'ISEMAIL_ERR_FWS_CRLF_END'],
        [' \r\n\r\ntest@iana.org', 'ISEMAIL_ERR_FWS_CRLF_X2'],
        [' \r\n\r\n test@iana.org', 'ISEMAIL_ERR_FWS_CRLF_X2'],
        ['test@iana.org\r\n ', 'ISEMAIL_CFWS_FWS'],
        ['test@iana.org\r\n \r\n ', 'ISEMAIL_DEPREC_FWS'],
        ['test@iana.org\r\n', 'ISEMAIL_ERR_FWS_CRLF_END'],
        ['test@iana.org\r\n \r\n', 'ISEMAIL_ERR_FWS_CRLF_END'],
        ['test@iana.org \r\n', 'ISEMAIL_ERR_FWS_CRLF_END'],
        ['test@iana.org \r\n ', 'ISEMAIL_CFWS_FWS'],
        ['test@iana.org \r\n \r\n', 'ISEMAIL_ERR_FWS_CRLF_END'],
        ['test@iana.org \r\n\r\n', 'ISEMAIL_ERR_FWS_CRLF_X2'],
        ['test@iana.org \r\n\r\n ', 'ISEMAIL_ERR_FWS_CRLF_X2'],
        [' test@iana.org', 'ISEMAIL_CFWS_FWS'],
        ['test@iana.org ', 'ISEMAIL_CFWS_FWS'],
        ['test@[IPv6:1::2:]', 'ISEMAIL_RFC5322_IPV6_COLONEND'],
        ['"test\\©"@iana.org', 'ISEMAIL_ERR_EXPECTING_QPAIR'],
        ['test@iana/icann.org', 'ISEMAIL_RFC5322_DOMAIN'],
        ['test.(comment)test@iana.org', 'ISEMAIL_DEPREC_COMMENT']
    ]
)
def test_pyisemail_tests(email_input, status):
    if status == "ISEMAIL_VALID":
        # All standard email address forms should not raise an exception.
        validate_email(email_input, test_environment=True)
    elif "_ERR_" in status or "_TOOLONG" in status \
         or "_CFWS_FWS" in status or "_CFWS_COMMENT" in status \
         or "_IPV6" in status or status == "ISEMAIL_RFC5322_DOMAIN":
        # Invalid syntax, extranous whitespace, and "(comments)" should be rejected.
        # The _IPV6_ diagnoses appear to represent syntactically invalid domain literals.
        # The ISEMAIL_RFC5322_DOMAIN diagnosis appears to be a syntactically invalid domain.
        with pytest.raises(EmailSyntaxError):
            validate_email(email_input, test_environment=True)
    elif "_DEPREC_" in status \
         or "RFC5321_QUOTEDSTRING" in status \
         or "DOMAINLITERAL" in status or "_DOMLIT_" in status or "_ADDRESSLITERAL" in status:
        # Quoted strings in the local part, domain literals (IP addresses in brackets),
        # and other deprecated syntax are valid email addresses and are accepted by pyIsEmail,
        # but we reject them.
        with pytest.raises(EmailSyntaxError):
            validate_email(email_input, test_environment=True)
    else:
        raise ValueError("status {} is not recognized".format(status))


def test_dict_accessor():
    input_email = "testaddr@example.tld"
    valid_email = validate_email(input_email, check_deliverability=False)
    assert isinstance(valid_email.as_dict(), dict)
    assert valid_email.as_dict()["original_email"] == input_email


def test_deliverability_found():
    response = validate_email_deliverability('gmail.com', 'gmail.com')
    assert response.keys() == {'mx', 'mx_fallback_type', 'spf'}
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


def test_deliverability_dns_timeout():
    validate_email_deliverability.TEST_CHECK_TIMEOUT = True
    response = validate_email_deliverability('gmail.com', 'gmail.com')
    assert "mx" not in response
    assert response.get("unknown-deliverability") == "timeout"
    validate_email('test@gmail.com')
    del validate_email_deliverability.TEST_CHECK_TIMEOUT


def test_main_single_good_input(monkeypatch, capsys):
    import json
    test_email = "google@google.com"
    monkeypatch.setattr('sys.argv', ['email_validator', test_email])
    validator_main()
    stdout, _ = capsys.readouterr()
    output = json.loads(str(stdout))
    assert isinstance(output, dict)
    assert validate_email(test_email).original_email == output["original_email"]


def test_main_single_bad_input(monkeypatch, capsys):
    bad_email = 'test@..com'
    monkeypatch.setattr('sys.argv', ['email_validator', bad_email])
    validator_main()
    stdout, _ = capsys.readouterr()
    assert stdout == 'An email address cannot have a period immediately after the @-sign.\n'


def test_main_multi_input(monkeypatch, capsys):
    import io
    test_cases = ["google1@google.com", "google2@google.com", "test@.com", "test3@.com"]
    test_input = io.StringIO("\n".join(test_cases))
    monkeypatch.setattr('sys.stdin', test_input)
    monkeypatch.setattr('sys.argv', ['email_validator'])
    validator_main()
    stdout, _ = capsys.readouterr()
    assert test_cases[0] not in stdout
    assert test_cases[1] not in stdout
    assert test_cases[2] in stdout
    assert test_cases[3] in stdout


def test_main_input_shim(monkeypatch, capsys):
    import json
    monkeypatch.setattr('sys.version_info', (2, 7))
    test_email = b"google@google.com"
    monkeypatch.setattr('sys.argv', ['email_validator', test_email])
    validator_main()
    stdout, _ = capsys.readouterr()
    output = json.loads(str(stdout))
    assert isinstance(output, dict)
    assert validate_email(test_email).original_email == output["original_email"]


def test_main_output_shim(monkeypatch, capsys):
    monkeypatch.setattr('sys.version_info', (2, 7))
    test_email = b"test@.com"
    monkeypatch.setattr('sys.argv', ['email_validator', test_email])
    validator_main()
    stdout, _ = capsys.readouterr()

    # This looks bad but it has to do with the way python 2.7 prints vs py3
    # The \n is part of the print statement, not part of the string, which is what the b'...' is
    # Since we're mocking py 2.7 here instead of actually using 2.7, this was the closest I could get
    assert stdout == "b'An email address cannot have a period immediately after the @-sign.'\n"


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
