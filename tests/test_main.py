import pytest
from email_validator import EmailSyntaxError, EmailUndeliverableError, \
                            validate_email, validate_email_deliverability, \
                            ValidatedEmail


@pytest.mark.parametrize(
    'email_input,output',
    [
        (
            'Abc@example.com',
            ValidatedEmail(
                local_part='Abc',
                ascii_local_part='Abc',
                smtputf8=False,
                ascii_domain='example.com',
                domain='example.com',
                email='Abc@example.com',
                ascii_email='Abc@example.com',
            ),
        ),
        (
            'Abc.123@example.com',
            ValidatedEmail(
                local_part='Abc.123',
                ascii_local_part='Abc.123',
                smtputf8=False,
                ascii_domain='example.com',
                domain='example.com',
                email='Abc.123@example.com',
                ascii_email='Abc.123@example.com',
            ),
        ),
        (
            'user+mailbox/department=shipping@example.com',
            ValidatedEmail(
                local_part='user+mailbox/department=shipping',
                ascii_local_part='user+mailbox/department=shipping',
                smtputf8=False,
                ascii_domain='example.com',
                domain='example.com',
                email='user+mailbox/department=shipping@example.com',
                ascii_email='user+mailbox/department=shipping@example.com',
            ),
        ),
        (
            "!#$%&'*+-/=?^_`.{|}~@example.com",
            ValidatedEmail(
                local_part="!#$%&'*+-/=?^_`.{|}~",
                ascii_local_part="!#$%&'*+-/=?^_`.{|}~",
                smtputf8=False,
                ascii_domain='example.com',
                domain='example.com',
                email="!#$%&'*+-/=?^_`.{|}~@example.com",
                ascii_email="!#$%&'*+-/=?^_`.{|}~@example.com",
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
            'ñoñó@example.com',
            ValidatedEmail(
                local_part='ñoñó',
                smtputf8=True,
                ascii_domain='example.com',
                domain='example.com',
                email='ñoñó@example.com',
            ),
        ),
        (
            '我買@example.com',
            ValidatedEmail(
                local_part='我買',
                smtputf8=True,
                ascii_domain='example.com',
                domain='example.com',
                email='我買@example.com',
            ),
        ),
        (
            '甲斐黒川日本@example.com',
            ValidatedEmail(
                local_part='甲斐黒川日本',
                smtputf8=True,
                ascii_domain='example.com',
                domain='example.com',
                email='甲斐黒川日本@example.com',
            ),
        ),
        (
            'чебурашкаящик-с-апельсинами.рф@example.com',
            ValidatedEmail(
                local_part='чебурашкаящик-с-апельсинами.рф',
                smtputf8=True,
                ascii_domain='example.com',
                domain='example.com',
                email='чебурашкаящик-с-апельсинами.рф@example.com',
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
        ('.leadingdot@domain.com', 'The email address contains invalid characters before the @-sign: ..'),
        ('..twodots@domain.com', 'The email address contains invalid characters before the @-sign: ..'),
        ('twodots..here@domain.com', 'The email address contains invalid characters before the @-sign: ..'),
        ('me@⒈wouldbeinvalid.com',
         "The domain name ⒈wouldbeinvalid.com contains invalid characters (Codepoint U+2488 not allowed "
         "at position 1 in '⒈wouldbeinvalid.com')."),
        ('@example.com', 'There must be something before the @-sign.'),
        ('\nmy@example.com', 'The email address contains invalid characters before the @-sign: \n.'),
        ('m\ny@example.com', 'The email address contains invalid characters before the @-sign: \n.'),
        ('my\n@example.com', 'The email address contains invalid characters before the @-sign: \n.'),
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
def test_email_invalid(email_input, error_msg):
    with pytest.raises(EmailSyntaxError) as exc_info:
        validate_email(email_input)
    # print(f'({email_input!r}, {str(exc_info.value)!r}),')
    assert str(exc_info.value) == error_msg


def test_deliverability_no_records():
    assert validate_email_deliverability('example.com', 'example.com') == {'mx': [(0, '')], 'mx-fallback': None}


def test_deliverability_found():
    response = validate_email_deliverability('gmail.com', 'gmail.com')
    assert response.keys() == {'mx', 'mx-fallback'}
    assert response['mx-fallback'] is None
    assert len(response['mx']) > 1
    assert len(response['mx'][0]) == 2
    assert isinstance(response['mx'][0][0], int)
    assert response['mx'][0][1].endswith('.com')


def test_deliverability_fails():
    domain = 'xkxufoekjvjfjeodlfmdfjcu.com'
    with pytest.raises(EmailUndeliverableError, match='The domain name {} does not exist'.format(domain)):
        validate_email_deliverability(domain, domain)
