
class EmailNotValidError(ValueError):
    """Parent class of all exceptions raised by this module."""
    pass

'''
The comments have bee copied from gmail website and support link
'''
class Validator(object):

    @staticmethod
    def validate_username_length(username=''):
        if username:
            if ((len(username)>6) and (len(username)<30)):
                return True
        raise EmailNotValidError('Invalid username length')

    @staticmethod
    def  validate_username_special_char(username=''):
        """
        Usernames can't contain an equal sign (=), brackets (<,>), plus sign (+), a comma (,), or more than one period (.) in a row.
        The last character of your username should be a letter (a-z) or number.
        """
        import re
        pattern = re.compile('[=><+,#!]*..+.$')
        response = pattern.match(username)
        if response:
           raise EmailNotValidError('Failed special character test')
        return response

    @staticmethod
    def validate_username_strictly(username=''):
        '''
        Usernames can contain letters (a-z), numbers (0-9), dashes (-), underscores (_), apostrophes ('}, and periods (.).
        '''
        import re
        pattern = re.compile("^[a-zA-Z0-9_-.']*$")
        response = pattern.match(username)
        if response:
            raise EmailNotValidError('Strict validation failed')
        """
        Usernames can't contain more than one period (.) in a row.
        The last character of your username should be a letter (a-z) or number.
        """
        pattern = re.compile("..+")
        response = pattern.match(username)
        if response:
           raise EmailNotValidError('Consecutive dots')
        last_char = username[len(username)-1]
        if not (last_char.isalpha() or last_char.isdigit()):
            raise EmailNotValidError("The last character of your username should be a letter (a-z) or number.`")
        return True

    @staticmethod
    def validate_domain_part(domain=''):
        if ((not domain == 'gmail.com') and (
                not domain == 'googlemail.com')):
            raise EmailNotValidError('domain name does not match gmail.com or googlemail.com')
        return True

    @staticmethod
    def normalize_username(username=''):
        #remove caps
        username = username.lower()
        #remove  dots, + 
        pattern = re.compile['.*']
        username = re.sub(pattern, '', username)
        return username

    @staticmethod
    def normalize_domain_part(domain=''):
        if domain == 'googlemail.com'
           return 'gmail.com'    
 