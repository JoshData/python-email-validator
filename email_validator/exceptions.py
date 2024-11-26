from dataclasses import dataclass
import unicodedata


class EmailNotValidError(ValueError):
    """Parent class of all exceptions raised by this module."""
    pass


class EmailSyntaxError(EmailNotValidError):
    """Exception raised when an email address fails validation because of its form."""
    pass


class EmailSyntaxNoAtSignError(EmailSyntaxError):
    """Exception raised when an email address is missing an @-sign."""
    def __str__(self):
        return "An email address must have an @-sign."


@dataclass
class EmailSyntaxAtSignConfusedError(EmailSyntaxNoAtSignError):
    """Exception raised when an email address is missing an @-sign but a confusable character is present."""
    character: str
    def __str__(self):
        return f"The email address has the {self.character} character instead of a regular at-sign."


def safe_character_display(c: str) -> str:
    # Return safely displayable characters in quotes.
    if c == '\\':
        return f"\"{c}\""  # can't use repr because it escapes it
    if unicodedata.category(c)[0] in ("L", "N", "P", "S"):
        return repr(c)

    # Construct a hex string in case the unicode name doesn't exist.
    if ord(c) < 0xFFFF:
        h = f"U+{ord(c):04x}".upper()
    else:
        h = f"U+{ord(c):08x}".upper()

    # Return the character name or, if it has no name, the hex string.
    return unicodedata.name(c, h)


@dataclass
class EmailInvalidCharactersError(EmailSyntaxError):
    """Exception raised when an email address fails validation because it contains invalid characters."""
    characters: list[str]
    def __str__(self):
        return ", ".join(safe_character_display(c) for c in self.characters)


class EmailInvalidCharactersAfterQuotedString(EmailInvalidCharactersError):
    """Exception raised when an email address fails validation because it contains invalid characters after a quoted string."""
    def __str__(self):
        return "Extra character(s) found after close quote: " + EmailInvalidCharactersError.__str__(self) + "."


class EmailInvalidCharactersInUnquotedDisplayName(EmailInvalidCharactersError):
    """Exception raised when an email address fails validation because it contains invalid characters after a quoted string."""
    def __str__(self):
        return "The display name contains invalid characters when not quoted: " + EmailInvalidCharactersError.__str__(self) + "."


class EmailIntlCharactersInLocalPart(EmailInvalidCharactersError):
    """Exception raised when an email address fails validation because it contains invalid characters after a quoted string."""
    def __str__(self):
        return "Internationalized characters before the @-sign are not supported: " + EmailInvalidCharactersError.__str__(self) + "."


class EmailInvalidCharactersInLocalPart(EmailInvalidCharactersError):
    """Exception raised when an email address fails validation because it contains invalid characters in the local part."""
    def __str__(self):
        return "The email address contains invalid characters before the @-sign: " + EmailInvalidCharactersError.__str__(self) + "."


class EmailUnsafeCharactersError(EmailInvalidCharactersError):
    """Exception raised when an email address fails validation because it contains invalid characters in the local part."""
    def __str__(self):
        return "The email address contains unsafe characters: " + EmailInvalidCharactersError.__str__(self) + "."


class EmailInvalidCharactersInDomainPart(EmailInvalidCharactersError):
    """Exception raised when an email address fails validation because it contains invalid characters after a quoted string."""
    def __str__(self):
        return f"The part after the @-sign contains invalid characters: " + EmailInvalidCharactersError.__str__(self) + "."


class EmailInvalidCharactersInDomainPartAfterUnicodeNormalization(EmailInvalidCharactersError):
    """Exception raised when an email address fails validation because it contains invalid characters after a quoted string."""
    def __str__(self):
        return f"The part after the @-sign contains invalid characters after Unicode normalization: " + EmailInvalidCharactersError.__str__(self) + "."


class EmailInvalidCharactersInDomainAddressLiteral(EmailInvalidCharactersError):
    """Exception raised when an email address fails validation because it contains invalid characters after a quoted string."""
    def __str__(self):
        return f"The part after the @-sign contains invalid characters in brackets: " + EmailInvalidCharactersError.__str__(self) + "."


class EmailBracketedAddressMissingCloseBracket(EmailSyntaxError):
    """Exception raised when an email address begins with an angle bracket but does not end with an angle bracket."""
    def __str__(self):
        return "An open angle bracket at the start of the email address has to be followed by a close angle bracket at the end."


class EmailBracketedAddressExtraneousText(EmailSyntaxError):
    """Exception raised when an email address in angle brackets has text after the angle brackets."""
    def __str__(self):
        return "There can't be anything after the email address."


class EmailNoLocalPartError(EmailSyntaxError):
    """Exception raised when an email address in angle brackets has text after the angle brackets."""
    def __str__(self):
        return "There must be something before the @-sign."


@dataclass
class EmailUnhandledSyntaxError(EmailSyntaxError):
    """Exception raised when an email address has an unhandled error."""
    message: str
    def __str__(self):
        return self.message


@dataclass
class EmailUndeliverableError(EmailNotValidError):
    """Exception raised when an email address fails validation because its domain name does not appear deliverable."""
    domain: str


@dataclass
class EmailUndeliverableNullMxError(EmailUndeliverableError):
    """Exception raised when an email address fails validation because its domain name has a Null MX record indicating that it cannot receive mail."""
    # See https://www.rfc-editor.org/rfc/rfc7505.
    def __str__(self):
        return f"The domain name {self.domain} does not accept email."

@dataclass
class EmailUndeliverableNoMxError(EmailUndeliverableError):
    """Exception raised when an email address fails validation because its domain name has no MX, A, or AAAA record indicating how to deliver mail."""
    def __str__(self):
        return f"The domain name {self.domain} does not accept email."

@dataclass
class EmailUndeliverableFallbackDeniesSendingMailError(EmailUndeliverableError):
    """Exception raised when an email address fails validation because its domain name has no MX record and it has a SPF record indicating it does not send mail."""
    def __str__(self):
        return f"The domain name {self.domain} does not send email."

@dataclass
class EmailUndeliverableNoDomainError(EmailUndeliverableError):
    """Exception raised when an email address fails validation because its domain name does not exist in DNS."""
    def __str__(self):
        return f"The domain name {self.domain} does not exist."


@dataclass
class EmailUndeliverableOtherError(EmailNotValidError):
    """Exception raised when an email address fails validation because of an unhandled exception."""
    def __str__(self):
        return "There was an error while checking if the domain name in the email address is deliverable."
