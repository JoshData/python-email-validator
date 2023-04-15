import pytest

from email_validator import EmailSyntaxError, \
                            validate_email, \
                            ValidatedEmail


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
                normalized='Abc@example.tld',
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
                normalized='Abc.123@test-example.com',
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
                normalized='user+mailbox/department=shipping@example.tld',
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
                normalized="!#$%&'*+-/=?^_`.{|}~@example.tld",
                ascii_email="!#$%&'*+-/=?^_`.{|}~@example.tld",
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
                normalized='jeff@臺網中心.tw',
                ascii_email='jeff@xn--fiqq24b10vi0d.tw',
            ),
        ),
    ],
)
def test_email_valid(email_input, output):
    # These addresses do not require SMTPUTF8. See test_email_valid_intl_local_part
    # for addresses that are valid but require SMTPUTF8. Check that it passes with
    # allow_smtput8 both on and off.
    emailinfo = validate_email(email_input, check_deliverability=False, allow_smtputf8=False)
    assert emailinfo == output
    assert validate_email(email_input, check_deliverability=False, allow_smtputf8=True) == output

    # Check that the old way to access the normalized form still works.
    assert emailinfo.email == emailinfo.normalized


@pytest.mark.parametrize(
    'email_input,output',
    [
        (
            '伊昭傑@郵件.商務',
            ValidatedEmail(
                local_part='伊昭傑',
                smtputf8=True,
                ascii_domain='xn--5nqv22n.xn--lhr59c',
                domain='郵件.商務',
                normalized='伊昭傑@郵件.商務',
            ),
        ),
        (
            'राम@मोहन.ईन्फो',
            ValidatedEmail(
                local_part='राम',
                smtputf8=True,
                ascii_domain='xn--l2bl7a9d.xn--o1b8dj2ki',
                domain='मोहन.ईन्फो',
                normalized='राम@मोहन.ईन्फो',
            ),
        ),
        (
            'юзер@екзампл.ком',
            ValidatedEmail(
                local_part='юзер',
                smtputf8=True,
                ascii_domain='xn--80ajglhfv.xn--j1aef',
                domain='екзампл.ком',
                normalized='юзер@екзампл.ком',
            ),
        ),
        (
            'θσερ@εχαμπλε.ψομ',
            ValidatedEmail(
                local_part='θσερ',
                smtputf8=True,
                ascii_domain='xn--mxahbxey0c.xn--xxaf0a',
                domain='εχαμπλε.ψομ',
                normalized='θσερ@εχαμπλε.ψομ',
            ),
        ),
        (
            '葉士豪@臺網中心.tw',
            ValidatedEmail(
                local_part='葉士豪',
                smtputf8=True,
                ascii_domain='xn--fiqq24b10vi0d.tw',
                domain='臺網中心.tw',
                normalized='葉士豪@臺網中心.tw',
            ),
        ),
        (
            '葉士豪@臺網中心.台灣',
            ValidatedEmail(
                local_part='葉士豪',
                smtputf8=True,
                ascii_domain='xn--fiqq24b10vi0d.xn--kpry57d',
                domain='臺網中心.台灣',
                normalized='葉士豪@臺網中心.台灣',
            ),
        ),
        (
            'jeff葉@臺網中心.tw',
            ValidatedEmail(
                local_part='jeff葉',
                smtputf8=True,
                ascii_domain='xn--fiqq24b10vi0d.tw',
                domain='臺網中心.tw',
                normalized='jeff葉@臺網中心.tw',
            ),
        ),
        (
            'ñoñó@example.tld',
            ValidatedEmail(
                local_part='ñoñó',
                smtputf8=True,
                ascii_domain='example.tld',
                domain='example.tld',
                normalized='ñoñó@example.tld',
            ),
        ),
        (
            '我買@example.tld',
            ValidatedEmail(
                local_part='我買',
                smtputf8=True,
                ascii_domain='example.tld',
                domain='example.tld',
                normalized='我買@example.tld',
            ),
        ),
        (
            '甲斐黒川日本@example.tld',
            ValidatedEmail(
                local_part='甲斐黒川日本',
                smtputf8=True,
                ascii_domain='example.tld',
                domain='example.tld',
                normalized='甲斐黒川日本@example.tld',
            ),
        ),
        (
            'чебурашкаящик-с-апельсинами.рф@example.tld',
            ValidatedEmail(
                local_part='чебурашкаящик-с-апельсинами.рф',
                smtputf8=True,
                ascii_domain='example.tld',
                domain='example.tld',
                normalized='чебурашкаящик-с-апельсинами.рф@example.tld',
            ),
        ),
        (
            'उदाहरण.परीक्ष@domain.with.idn.tld',
            ValidatedEmail(
                local_part='उदाहरण.परीक्ष',
                smtputf8=True,
                ascii_domain='domain.with.idn.tld',
                domain='domain.with.idn.tld',
                normalized='उदाहरण.परीक्ष@domain.with.idn.tld',
            ),
        ),
        (
            'ιωάννης@εεττ.gr',
            ValidatedEmail(
                local_part='ιωάννης',
                smtputf8=True,
                ascii_domain='xn--qxaa9ba.gr',
                domain='εεττ.gr',
                normalized='ιωάννης@εεττ.gr',
            ),
        ),
    ],
)
def test_email_valid_intl_local_part(email_input, output):
    # Check that it passes when allow_smtputf8 is True.
    assert validate_email(email_input, check_deliverability=False) == output

    # Check that it fails when allow_smtputf8 is False.
    with pytest.raises(EmailSyntaxError) as exc_info:
        validate_email(email_input, allow_smtputf8=False, check_deliverability=False)
    assert "Internationalized characters before the @-sign are not supported: " in str(exc_info.value)


@pytest.mark.parametrize(
    'email_input,normalized_local_part',
    [
        ('"unnecessarily.quoted.local.part"@example.com', 'unnecessarily.quoted.local.part'),
        ('"quoted..local.part"@example.com', '"quoted..local.part"'),
        ('"quoted.with.at@"@example.com', '"quoted.with.at@"'),
        ('"quoted with space"@example.com', '"quoted with space"'),
        ('"quoted.with.dquote\\""@example.com', '"quoted.with.dquote\\""'),
        ('"unnecessarily.quoted.with.unicode.λ"@example.com', 'unnecessarily.quoted.with.unicode.λ'),
        ('"quoted.with..unicode.λ"@example.com', '"quoted.with..unicode.λ"'),
        ('"quoted.with.extraneous.\\escape"@example.com', 'quoted.with.extraneous.escape'),
    ])
def test_email_valid_only_if_quoted_local_part(email_input, normalized_local_part):
    # These addresses are invalid with the default allow_quoted_local=False option.
    with pytest.raises(EmailSyntaxError) as exc_info:
        validate_email(email_input)
    assert str(exc_info.value) == 'Quoting the part before the @-sign is not allowed here.'

    # But they are valid if quoting is allowed.
    validated = validate_email(email_input, allow_quoted_local=True, check_deliverability=False)

    # Check that the normalized form correctly removed unnecessary backslash escaping
    # and even the quoting if they weren't necessary.
    assert validated.local_part == normalized_local_part


def test_domain_literal():
    # Check parsing IPv4 addresses.
    validated = validate_email("me@[127.0.0.1]", allow_domain_literal=True)
    assert validated.domain == "[127.0.0.1]"
    assert repr(validated.domain_address) == "IPv4Address('127.0.0.1')"

    # Check parsing IPv6 addresses.
    validated = validate_email("me@[IPv6:::1]", allow_domain_literal=True)
    assert validated.domain == "[IPv6:::1]"
    assert repr(validated.domain_address) == "IPv6Address('::1')"

    # Check that IPv6 addresses are normalized.
    validated = validate_email("me@[IPv6:0000:0000:0000:0000:0000:0000:0000:0001]", allow_domain_literal=True)
    assert validated.domain == "[IPv6:::1]"
    assert repr(validated.domain_address) == "IPv6Address('::1')"


@pytest.mark.parametrize(
    'email_input,error_msg',
    [
        ('my@localhost', 'The part after the @-sign is not valid. It should have a period.'),
        ('my@.leadingdot.com', 'An email address cannot have a period immediately after the @-sign.'),
        ('my@．leadingfwdot.com', 'An email address cannot have a period immediately after the @-sign.'),
        ('my@twodots..com', 'An email address cannot have two periods in a row.'),
        ('my@twofwdots．．.com', 'An email address cannot have two periods in a row.'),
        ('my@trailingdot.com.', 'An email address cannot end with a period.'),
        ('my@trailingfwdot.com．', 'An email address cannot end with a period.'),
        ('me@-leadingdash', 'An email address cannot have a hyphen immediately after the @-sign.'),
        ('me@－leadingdashfw', 'An email address cannot have a hyphen immediately after the @-sign.'),
        ('me@trailingdash-', 'An email address cannot end with a hyphen.'),
        ('me@trailingdashfw－', 'An email address cannot end with a hyphen.'),
        ('my@baddash.-.com', 'An email address cannot have a period and a hyphen next to each other.'),
        ('my@baddash.-a.com', 'An email address cannot have a period and a hyphen next to each other.'),
        ('my@baddash.b-.com', 'An email address cannot have a period and a hyphen next to each other.'),
        ('my@baddashfw.－.com', 'An email address cannot have a period and a hyphen next to each other.'),
        ('my@baddashfw.－a.com', 'An email address cannot have a period and a hyphen next to each other.'),
        ('my@baddashfw.b－.com', 'An email address cannot have a period and a hyphen next to each other.'),
        ('my@example.com\n',
         'The part after the @-sign contains invalid characters: U+000A.'),
        ('my@example\n.com',
         'The part after the @-sign contains invalid characters: U+000A.'),
        ('me@x!', 'The part after the @-sign contains invalid characters: \'!\'.'),
        ('me@x ', 'The part after the @-sign contains invalid characters: SPACE.'),
        ('.leadingdot@domain.com', 'An email address cannot start with a period.'),
        ('twodots..here@domain.com', 'An email address cannot have two periods in a row.'),
        ('trailingdot.@domain.email', 'An email address cannot have a period immediately before the @-sign.'),
        ('me@⒈wouldbeinvalid.com',
         "The part after the @-sign contains invalid characters (Codepoint U+2488 not allowed "
         "at position 1 in '⒈wouldbeinvalid.com')."),
        ('@example.com', 'There must be something before the @-sign.'),
        ('white space@test', 'The email address contains invalid characters before the @-sign: SPACE.'),
        ('test@white space', 'The part after the @-sign contains invalid characters: SPACE.'),
        ('\nmy@example.com', 'The email address contains invalid characters before the @-sign: U+000A.'),
        ('m\ny@example.com', 'The email address contains invalid characters before the @-sign: U+000A.'),
        ('my\n@example.com', 'The email address contains invalid characters before the @-sign: U+000A.'),
        ('test@\n', 'The part after the @-sign contains invalid characters: U+000A.'),
        ('bad"quotes"@example.com', 'The email address contains invalid characters before the @-sign: \'"\'.'),
        ('obsolete."quoted".atom@example.com', 'The email address contains invalid characters before the @-sign: \'"\'.'),
        ('11111111112222222222333333333344444444445555555555666666666677777@example.com', 'The email address is too long before the @-sign (1 character too many).'),
        ('111111111122222222223333333333444444444455555555556666666666777777@example.com', 'The email address is too long before the @-sign (2 characters too many).'),
        ('me@1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.111111111122222222223333333333444444444455555555556.com', 'The email address is too long (4 characters too many).'),
        ('me@1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.1111111111222222222233333333334444444444555555555566.com', 'The email address is too long after the @-sign (1 character too many).'),
        ('me@中1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.1111111111222222222233333333334444444444555555555566.com', 'The email address is too long after the @-sign.'),
        ('my.long.address@1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.11111111112222222222333333333344444.info', 'The email address is too long (2 characters too many).'),
        ('my.long.address@λ111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.11111111112222222222333333.info', 'The email address is too long (when converted to IDNA ASCII).'),
        ('my.long.address@λ111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.1111111111222222222233333333334444.info', 'The email address is too long (at least 1 character too many).'),
        ('my.λong.address@1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.111111111122222222223333333333444.info', 'The email address is too long (when encoded in bytes).'),
        ('my.λong.address@1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.1111111111222222222233333333334444.info', 'The email address is too long (at least 1 character too many).'),
        ('me@bad-tld-1', 'The part after the @-sign is not valid. It should have a period.'),
        ('me@bad.tld-2', 'The part after the @-sign is not valid. It is not within a valid top-level domain.'),
        ('me@xn--0.tld', 'The part after the @-sign is not valid IDNA (Invalid A-label).'),
        ('me@yy--0.tld', 'An email address cannot have two letters followed by two dashes immediately after the @-sign or after a period, except Punycode.'),
        ('me@yy－－0.tld', 'An email address cannot have two letters followed by two dashes immediately after the @-sign or after a period, except Punycode.'),
        ('me@[127.0.0.1]', 'A bracketed IPv4 address after the @-sign is not allowed here.'),
        ('me@[127.0.0.999]', 'The address in brackets after the @-sign is not valid: It is not an IPv4 address (Octet 999 (> 255) not permitted in \'127.0.0.999\') or is missing an address literal tag.'),
        ('me@[IPv6:::1]', 'A bracketed IPv6 address after the @-sign is not allowed here.'),
        ('me@[IPv6:::G]', 'The IPv6 address in brackets after the @-sign is not valid (Only hex digits permitted in \'G\' in \'::G\').'),
        ('me@[tag:text]', 'The part after the @-sign contains an invalid address literal tag in brackets.'),
        ('me@[untaggedtext]', 'The part after the @-sign in brackets is not an IPv4 address and has no address literal tag.'),
        ('me@[tag:invalid space]', 'The part after the @-sign contains invalid characters in brackets: SPACE.'),
    ],
)
def test_email_invalid_syntax(email_input, error_msg):
    # Since these all have syntax errors, deliverability
    # checks do not arise.
    with pytest.raises(EmailSyntaxError) as exc_info:
        validate_email(email_input)
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
    assert "is a special-use or reserved name" in str(exc_info.value)


@pytest.mark.parametrize(
    ('s', 'expected_error'),
    [
        ('\u2005', 'FOUR-PER-EM SPACE'),  # four-per-em space (Zs)
        ('\u2028', 'LINE SEPARATOR'),  # line separator (Zl)
        ('\u2029', 'PARAGRAPH SEPARATOR'),  # paragraph separator (Zp)
        ('\u0300', 'COMBINING GRAVE ACCENT'),  # grave accent (M)
        ('\u009C', 'U+009C'),  # string terminator (Cc)
        ('\u200B', 'ZERO WIDTH SPACE'),  # zero-width space (Cf)
        ('\u202Dforward-\u202Ereversed', 'LEFT-TO-RIGHT OVERRIDE, RIGHT-TO-LEFT OVERRIDE'),  # BIDI (Cf)
        ('\uD800', 'U+D800'),  # surrogate (Cs)
        ('\uE000', 'U+E000'),  # private use (Co)
        ('\U0010FDEF', 'U+0010FDEF'),  # priate use (Co)
        ('\uFDEF', 'U+FDEF'),  # unassigned (Cn)
    ],
)
def test_email_unsafe_character(s, expected_error):
    # Check for various unsafe characters that are permitted by the email
    # specs but should be disallowed for being unsafe or not sensible Unicode.

    with pytest.raises(EmailSyntaxError) as exc_info:
        validate_email(s + "@test", test_environment=True)
    assert str(exc_info.value) == f"The email address contains unsafe characters: {expected_error}."

    with pytest.raises(EmailSyntaxError) as exc_info:
        validate_email("test@" + s, test_environment=True)
    assert "The email address contains unsafe characters" in str(exc_info.value)


@pytest.mark.parametrize(
    ('email_input', 'expected_error'),
    [
        ('λambdaツ@test', 'Internationalized characters before the @-sign are not supported: \'λ\', \'ツ\'.'),
        ('"quoted.with..unicode.λ"@example.com', 'Internationalized characters before the @-sign are not supported: \'λ\'.'),
    ],
)
def test_email_invalid_character_smtputf8_off(email_input, expected_error):
    # Check that internationalized characters are rejected if allow_smtputf8=False.
    with pytest.raises(EmailSyntaxError) as exc_info:
        validate_email(email_input, allow_smtputf8=False, test_environment=True)
    assert str(exc_info.value) == expected_error


def test_email_empty_local():
    validate_email("@test", allow_empty_local=True, test_environment=True)

    # This next one might not be desirable.
    validate_email("\"\"@test", allow_empty_local=True, allow_quoted_local=True, test_environment=True)


def test_email_test_domain_name_in_test_environment():
    validate_email("anything@test", test_environment=True)
    validate_email("anything@mycompany.test", test_environment=True)


def test_case_insensitive_mailbox_name():
    validate_email("POSTMASTER@test", test_environment=True).normalized = "postmaster@test"
    validate_email("NOT-POSTMASTER@test", test_environment=True).normalized = "NOT-POSTMASTER@test"


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
        # ['""@iana.org', 'ISEMAIL_RFC5321_QUOTEDSTRING'], # we think an empty quoted string should be invalid
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
        # All standard email address forms should not raise an exception
        # with any set of parsing options.
        validate_email(email_input, test_environment=True)
        validate_email(email_input, allow_quoted_local=True, allow_domain_literal=True, test_environment=True)

    elif status == "ISEMAIL_RFC5321_QUOTEDSTRING":
        # Quoted-literal local parts are only valid with an option.
        with pytest.raises(EmailSyntaxError):
            validate_email(email_input, test_environment=True)
        validate_email(email_input, allow_quoted_local=True, test_environment=True)

    elif "_ADDRESSLITERAL" in status or status == 'ISEMAIL_RFC5321_IPV6DEPRECATED':
        # Domain literals with IPv4 or IPv6 addresses are only valid with an option.
        # I am not sure if the ISEMAIL_RFC5321_IPV6DEPRECATED case should be rejected:
        # The Python ipaddress module accepts it.
        with pytest.raises(EmailSyntaxError):
            validate_email(email_input, test_environment=True)
        validate_email(email_input, allow_domain_literal=True, test_environment=True)

    elif "_DOMLIT_" in status or "DOMAINLITERAL" in status or "_IPV6" in status:
        # Invalid domain literals even when allow_domain_literal=True.
        # The _DOMLIT_ diagnoses appear to be invalid domain literals.
        # The DOMAINLITERAL diagnoses appear to be valid domain literals that can't
        # be parsed as an IPv4 or IPv6 address.
        # The _IPV6_ diagnoses appear to represent syntactically invalid domain literals.
        with pytest.raises(EmailSyntaxError):
            validate_email(email_input, allow_domain_literal=True, test_environment=True)

    elif "_ERR_" in status or "_TOOLONG" in status \
         or "_CFWS_FWS" in status or "_CFWS_COMMENT" in status \
         or status == "ISEMAIL_RFC5322_DOMAIN":
        # Invalid syntax, extraneous whitespace, and "(comments)" should be rejected.
        # The ISEMAIL_RFC5322_DOMAIN diagnosis appears to be a syntactically invalid domain.
        # These are invalid with any set of options.
        with pytest.raises(EmailSyntaxError):
            validate_email(email_input, test_environment=True)
            validate_email(email_input, allow_quoted_local=True, allow_domain_literal=True, test_environment=True)

    elif "_DEPREC_" in status:
        # Various deprecated syntax are valid email addresses and are accepted by pyIsEmail,
        # but we reject them even with extended options.
        with pytest.raises(EmailSyntaxError):
            validate_email(email_input, test_environment=True)
            validate_email(email_input, allow_quoted_local=True, allow_domain_literal=True, test_environment=True)

    else:
        raise ValueError(f"status {status} is not recognized")
