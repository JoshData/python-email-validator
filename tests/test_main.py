import pytest
from email_validator import EmailSyntaxError, EmailUndeliverableError, validate_email, validate_email_deliverability


@pytest.mark.parametrize(
    'email_input,output',
    [
        (
            'Abc@example.com',
            {
                'local': 'Abc',
                'smtputf8': False,
                'domain': 'example.com',
                'domain_i18n': 'example.com',
                'email': 'Abc@example.com',
                'email_ascii': 'Abc@example.com',
            },
        ),
        (
            'Abc.123@example.com',
            {
                'local': 'Abc.123',
                'smtputf8': False,
                'domain': 'example.com',
                'domain_i18n': 'example.com',
                'email': 'Abc.123@example.com',
                'email_ascii': 'Abc.123@example.com',
            },
        ),
        (
            'user+mailbox/department=shipping@example.com',
            {
                'local': 'user+mailbox/department=shipping',
                'smtputf8': False,
                'domain': 'example.com',
                'domain_i18n': 'example.com',
                'email': 'user+mailbox/department=shipping@example.com',
                'email_ascii': 'user+mailbox/department=shipping@example.com',
            },
        ),
        (
            "!#$%&'*+-/=?^_`.{|}~@example.com",
            {
                'local': "!#$%&'*+-/=?^_`.{|}~",
                'smtputf8': False,
                'domain': 'example.com',
                'domain_i18n': 'example.com',
                'email': "!#$%&'*+-/=?^_`.{|}~@example.com",
                'email_ascii': "!#$%&'*+-/=?^_`.{|}~@example.com",
            },
        ),
        (
            '伊昭傑@郵件.商務',
            {
                'local': '伊昭傑',
                'smtputf8': True,
                'domain': 'xn--5nqv22n.xn--lhr59c',
                'domain_i18n': '郵件.商務',
                'email': '伊昭傑@郵件.商務',
            },
        ),
        (
            'राम@मोहन.ईन्फो',
            {
                'local': 'राम',
                'smtputf8': True,
                'domain': 'xn--l2bl7a9d.xn--o1b8dj2ki',
                'domain_i18n': 'मोहन.ईन्फो',
                'email': 'राम@मोहन.ईन्फो',
            },
        ),
        (
            'юзер@екзампл.ком',
            {
                'local': 'юзер',
                'smtputf8': True,
                'domain': 'xn--80ajglhfv.xn--j1aef',
                'domain_i18n': 'екзампл.ком',
                'email': 'юзер@екзампл.ком',
            },
        ),
        (
            'θσερ@εχαμπλε.ψομ',
            {
                'local': 'θσερ',
                'smtputf8': True,
                'domain': 'xn--mxahbxey0c.xn--xxaf0a',
                'domain_i18n': 'εχαμπλε.ψομ',
                'email': 'θσερ@εχαμπλε.ψομ',
            },
        ),
        (
            '葉士豪@臺網中心.tw',
            {
                'local': '葉士豪',
                'smtputf8': True,
                'domain': 'xn--fiqq24b10vi0d.tw',
                'domain_i18n': '臺網中心.tw',
                'email': '葉士豪@臺網中心.tw',
            },
        ),
        (
            'jeff@臺網中心.tw',
            {
                'local': 'jeff',
                'smtputf8': False,
                'domain': 'xn--fiqq24b10vi0d.tw',
                'domain_i18n': '臺網中心.tw',
                'email': 'jeff@臺網中心.tw',
                'email_ascii': 'jeff@xn--fiqq24b10vi0d.tw',
            },
        ),
        (
            '葉士豪@臺網中心.台灣',
            {
                'local': '葉士豪',
                'smtputf8': True,
                'domain': 'xn--fiqq24b10vi0d.xn--kpry57d',
                'domain_i18n': '臺網中心.台灣',
                'email': '葉士豪@臺網中心.台灣',
            },
        ),
        (
            'jeff葉@臺網中心.tw',
            {
                'local': 'jeff葉',
                'smtputf8': True,
                'domain': 'xn--fiqq24b10vi0d.tw',
                'domain_i18n': '臺網中心.tw',
                'email': 'jeff葉@臺網中心.tw',
            },
        ),
        (
            'ñoñó@example.com',
            {
                'local': 'ñoñó',
                'smtputf8': True,
                'domain': 'example.com',
                'domain_i18n': 'example.com',
                'email': 'ñoñó@example.com',
            },
        ),
        (
            '我買@example.com',
            {
                'local': '我買',
                'smtputf8': True,
                'domain': 'example.com',
                'domain_i18n': 'example.com',
                'email': '我買@example.com',
            },
        ),
        (
            '甲斐黒川日本@example.com',
            {
                'local': '甲斐黒川日本',
                'smtputf8': True,
                'domain': 'example.com',
                'domain_i18n': 'example.com',
                'email': '甲斐黒川日本@example.com',
            },
        ),
        (
            'чебурашкаящик-с-апельсинами.рф@example.com',
            {
                'local': 'чебурашкаящик-с-апельсинами.рф',
                'smtputf8': True,
                'domain': 'example.com',
                'domain_i18n': 'example.com',
                'email': 'чебурашкаящик-с-апельсинами.рф@example.com',
            },
        ),
        (
            'उदाहरण.परीक्ष@domain.with.idn.tld',
            {
                'local': 'उदाहरण.परीक्ष',
                'smtputf8': True,
                'domain': 'domain.with.idn.tld',
                'domain_i18n': 'domain.with.idn.tld',
                'email': 'उदाहरण.परीक्ष@domain.with.idn.tld',
            },
        ),
        (
            'ιωάννης@εεττ.gr',
            {
                'local': 'ιωάννης',
                'smtputf8': True,
                'domain': 'xn--qxaa9ba.gr',
                'domain_i18n': 'εεττ.gr',
                'email': 'ιωάννης@εεττ.gr',
            },
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
        ('.leadingdot@domain.com', 'The email address contains invalid characters before the @-sign: ..'),
        ('..twodots@domain.com', 'The email address contains invalid characters before the @-sign: ..'),
        ('twodots..here@domain.com', 'The email address contains invalid characters before the @-sign: ..'),
        ('me@⒈wouldbeinvalid.com',
         "The domain name ⒈wouldbeinvalid.com contains invalid characters (Codepoint U+2488 not allowed "
         "at position 1 in '⒈wouldbeinvalid.com')."),
        ('@example.com', 'There must be something before the @-sign.'),
        ('{}@{}.com'.format(32 * 'x', '.'.join([60 * 'y' for _ in range(4)])), 'The email address is too long.'),
    ],
)
def test_email_invalid(email_input, error_msg):
    with pytest.raises(EmailSyntaxError) as exc_info:
        validate_email(email_input)
    # print(f'({email_input!r}, {str(exc_info.value)!r}),')
    assert str(exc_info.value) == error_msg


def test_deliverability_no_records():
    assert validate_email_deliverability('example.com', 'example.com') == {'mx': [(0, '')], 'mx-fallback': False}


def test_deliverability_found():
    response = validate_email_deliverability('gmail.com', 'gmail.com')
    assert response.keys() == {'mx', 'mx-fallback'}
    assert response['mx-fallback'] is False
    assert len(response['mx']) > 1
    assert len(response['mx'][0]) == 2
    assert isinstance(response['mx'][0][0], int)
    assert response['mx'][0][1].endswith('.com')


def test_deliverability_fails():
    domain = 'xkxufoekjvjfjeodlfmdfjcu.com'
    with pytest.raises(EmailUndeliverableError, match='The domain name {} does not exist'.format(domain)):
        validate_email_deliverability(domain, domain)
