from email_validator import validate_email

email1 = 'ewferfwekuh@ekjfjeir1.com'
email2 = 'ewferfwekuh@ekjfjeir.ewrfref.mm71'
email3 = 'ewferfwekuh@ekjfjeir.local'

v1 = validate_email(email1,check_deliverability=False)
v2 = validate_email(email2,check_deliverability=False,allow_any_top_level_domain=False,allowed_top_level_domains=['mm72','mm74'])
v3 = validate_email(email3,check_deliverability=False,allow_special_domains=True)