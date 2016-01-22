class EmailNotValidError(ValueError):
    """Had to copy paste to avoid circular import."""
    pass



class Validator(object):

    @staticmethod
    def validate_username_length(username=''):
        if username:
            if ((len(username)>6) and (len(username)<30)):
                return True
        raise EmailNotValidError('Error at username checker')

    @staticmethod
    def  validate_special_char(username=''):
    """
    Usernames can't contain an equal sign (=), brackets (<,>), plus sign (+), a comma (,), or more than one period (.) in a row.
    """
    import re
    if re.match()
