from asyncio import Future
from typing import Optional, Union, TYPE_CHECKING

from .exceptions_types import EmailSyntaxError, ValidatedEmail
from .syntax import split_email, validate_email_local_part, validate_email_domain_name, validate_email_domain_literal, validate_email_length
from .rfc_constants import CASE_INSENSITIVE_MAILBOX_NAMES

if TYPE_CHECKING:
    import dns.resolver
    _Resolver = dns.resolver.Resolver
else:
    _Resolver = object


# This is the main function of the package. Through some magic,
# it can be called both non-asynchronously and, if async_loop
# is not None, also asynchronously with 'await'. If called
# asynchronously, dns_resolver may be an instance of
# dns.asyncresolver.Resolver.
def validate_email_sync_or_async(
    # NOTE: Arguments other than async_loop must match
    # validate_email_sync/async defined below.
    email: Union[str, bytes],
    /,  # prior arguments are positional-only
    *,  # subsequent arguments are keyword-only
    allow_smtputf8: Optional[bool] = None,
    allow_empty_local: bool = False,
    allow_quoted_local: Optional[bool] = None,
    allow_domain_literal: Optional[bool] = None,
    allow_display_name: Optional[bool] = None,
    check_deliverability: Optional[bool] = None,
    test_environment: Optional[bool] = None,
    globally_deliverable: Optional[bool] = None,
    timeout: Optional[int] = None,
    dns_resolver: Optional[_Resolver] = None,
    async_loop: Optional[object] = None
) -> Union[ValidatedEmail, Future]:  # Future[ValidatedEmail] works in Python 3.10+
    """
    Given an email address, and some options, returns a ValidatedEmail instance
    with information about the address if it is valid or, if the address is not
    valid, raises an EmailNotValidError. This is the main function of the module.
    """

    # Fill in default values of arguments.
    from . import ALLOW_SMTPUTF8, ALLOW_QUOTED_LOCAL, ALLOW_DOMAIN_LITERAL, ALLOW_DISPLAY_NAME, \
        GLOBALLY_DELIVERABLE, CHECK_DELIVERABILITY, TEST_ENVIRONMENT, DEFAULT_TIMEOUT
    if allow_smtputf8 is None:
        allow_smtputf8 = ALLOW_SMTPUTF8
    if allow_quoted_local is None:
        allow_quoted_local = ALLOW_QUOTED_LOCAL
    if allow_domain_literal is None:
        allow_domain_literal = ALLOW_DOMAIN_LITERAL
    if allow_display_name is None:
        allow_display_name = ALLOW_DISPLAY_NAME
    if check_deliverability is None:
        check_deliverability = CHECK_DELIVERABILITY
    if test_environment is None:
        test_environment = TEST_ENVIRONMENT
    if globally_deliverable is None:
        globally_deliverable = GLOBALLY_DELIVERABLE
    if timeout is None and dns_resolver is None:
        timeout = DEFAULT_TIMEOUT

    # Allow email to be a str or bytes instance. If bytes,
    # it must be ASCII because that's how the bytes work
    # on the wire with SMTP.
    if not isinstance(email, str):
        try:
            email = email.decode("ascii")
        except ValueError as e:
            raise EmailSyntaxError("The email address is not valid ASCII.") from e

    # Split the address into the display name (or None), the local part
    # (before the @-sign), and the domain part (after the @-sign).
    # Normally, there is only one @-sign. But the awkward "quoted string"
    # local part form (RFC 5321 4.1.2) allows @-signs in the local
    # part if the local part is quoted.
    display_name, local_part, domain_part, is_quoted_local_part \
        = split_email(email)
    if display_name is not None and not allow_display_name:
        raise EmailSyntaxError("A display name and angle brackets around the email address are not permitted here.")

    # Collect return values in this instance.
    ret = ValidatedEmail()
    ret.original = email
    ret.display_name = display_name

    # Validate the email address's local part syntax and get a normalized form.
    # If the original address was quoted and the decoded local part is a valid
    # unquoted local part, then we'll get back a normalized (unescaped) local
    # part.
    local_part_info = validate_email_local_part(local_part,
                                                allow_smtputf8=allow_smtputf8,
                                                allow_empty_local=allow_empty_local,
                                                quoted_local_part=is_quoted_local_part)
    ret.local_part = local_part_info["local_part"]
    ret.ascii_local_part = local_part_info["ascii_local_part"]
    ret.smtputf8 = local_part_info["smtputf8"]

    # If a quoted local part isn't allowed but is present, now raise an exception.
    # This is done after any exceptions raised by validate_email_local_part so
    # that mandatory checks have highest precedence.
    if is_quoted_local_part and not allow_quoted_local:
        raise EmailSyntaxError("Quoting the part before the @-sign is not allowed here.")

    # Some local parts are required to be case-insensitive, so we should normalize
    # to lowercase.
    # RFC 2142
    if ret.ascii_local_part is not None \
       and ret.ascii_local_part.lower() in CASE_INSENSITIVE_MAILBOX_NAMES \
       and ret.local_part is not None:
        ret.ascii_local_part = ret.ascii_local_part.lower()
        ret.local_part = ret.local_part.lower()

    # Validate the email address's domain part syntax and get a normalized form.
    is_domain_literal = False
    if len(domain_part) == 0:
        raise EmailSyntaxError("There must be something after the @-sign.")

    elif domain_part.startswith("[") and domain_part.endswith("]"):
        # Parse the address in the domain literal and get back a normalized domain.
        domain_literal_info = validate_email_domain_literal(domain_part[1:-1])
        if not allow_domain_literal:
            raise EmailSyntaxError("A bracketed IP address after the @-sign is not allowed here.")
        ret.domain = domain_literal_info["domain"]
        ret.ascii_domain = domain_literal_info["domain"]  # Domain literals are always ASCII.
        ret.domain_address = domain_literal_info["domain_address"]
        is_domain_literal = True  # Prevent deliverability checks.

    else:
        # Check the syntax of the domain and get back a normalized
        # internationalized and ASCII form.
        domain_name_info = validate_email_domain_name(domain_part, test_environment=test_environment, globally_deliverable=globally_deliverable)
        ret.domain = domain_name_info["domain"]
        ret.ascii_domain = domain_name_info["ascii_domain"]

    # Construct the complete normalized form.
    ret.normalized = ret.local_part + "@" + ret.domain

    # If the email address has an ASCII form, add it.
    if not ret.smtputf8:
        if not ret.ascii_domain:
            raise Exception("Missing ASCII domain.")
        ret.ascii_email = (ret.ascii_local_part or "") + "@" + ret.ascii_domain
    else:
        ret.ascii_email = None

    # Check the length of the address.
    validate_email_length(ret)

    # If no deliverability checks will be performed, return the validation
    # information immediately.
    if not check_deliverability or is_domain_literal or test_environment:
        # When called non-asynchronously, just return --- that's easy.
        if not async_loop:
            return ret

        # When this method is called asynchronously, we must return an awaitable,
        # not the regular return value. Normally 'async def' handles that for you,
        # but to not duplicate this entire function in an asynchronous version, we
        # have a single function that works both both ways, depending on if
        # async_loop is set.
        #
        # Wrap the ValidatedEmail object in a Future that is immediately
        # done. If async_loop holds a loop object, use it to create the Future.
        # Otherwise create a default Future instance.
        fut: Future
        if async_loop is True:
            fut = Future()
        elif not hasattr(async_loop, 'create_future'):  # suppress typing warning
            raise RuntimeError("async_loop parameter must have a create_future method.")
        else:
            fut = async_loop.create_future()
        fut.set_result(ret)
        return fut

    # Validate the email address's deliverability using DNS
    # and update the returned ValidatedEmail object with metadata.
    #
    # Domain literals are not DNS names so deliverability checks are
    # skipped (above) if is_domain_literal is set.

    # Lazy load `deliverability` as it is slow to import (due to dns.resolver)
    from .deliverability import validate_email_deliverability

    # Wrap validate_email_deliverability, which is an async function, in another
    # async function that merges the resulting information with the ValidatedEmail
    # instance. Since this method may be used in a non-asynchronous call, it
    # must not await on anything that might yield execution.
    async def run_deliverability_checks():
        # Run the DNS-based deliverabiltiy checks.
        #
        # Although validate_email_deliverability (and this local function)
        # are async functions, when async_loop is None it must not yield
        # execution. See below.
        info = await validate_email_deliverability(
            ret.ascii_domain, ret.domain, timeout, dns_resolver,
            async_loop
        )

        # Merge deliverability info with the syntax info (if there was no exception).
        for key, value in info.items():
            setattr(ret, key, value)

        return ret

    if not async_loop:
        # When this function is called non-asynchronously, we will manually
        # drive the coroutine returned by the async run_deliverability_checks
        # function. Since we know that it does not yield execution, it will
        # finish by raising StopIteration after the first 'send()' call. (If
        # it doesn't, something serious went wrong.)
        try:
            # This call will either raise StopIteration on success or it will
            # raise an EmailUndeliverableError on failure.
            run_deliverability_checks().send(None)

            # If we come here, the coroutine yielded execution. We can't recover
            # from this.
            raise RuntimeError("Asynchronous resolver used in non-asychronous call or validate_email_deliverability mistakenly yielded.")

        except StopIteration as e:
            # This is how a successful return occurs when driving a coroutine.
            # The 'value' attribute on the exception holds the return value.
            # Since we're in a non-asynchronous call, we can return it directly.
            return e.value

    else:
        # When this method is called asynchronously, return
        # a coroutine.
        return run_deliverability_checks()


# Validates an email address with DNS queries issued synchronously.
# This is exposed as the package's main validate_email method.
def validate_email_sync(
    email: Union[str, bytes],
    /,  # prior arguments are positional-only
    *,  # subsequent arguments are keyword-only
    allow_smtputf8: Optional[bool] = None,
    allow_empty_local: bool = False,
    allow_quoted_local: Optional[bool] = None,
    allow_domain_literal: Optional[bool] = None,
    allow_display_name: Optional[bool] = None,
    check_deliverability: Optional[bool] = None,
    test_environment: Optional[bool] = None,
    globally_deliverable: Optional[bool] = None,
    timeout: Optional[int] = None,
    dns_resolver: Optional[object] = None
) -> ValidatedEmail:
    ret = validate_email_sync_or_async(
        email,
        allow_smtputf8=allow_smtputf8,
        allow_empty_local=allow_empty_local,
        allow_quoted_local=allow_quoted_local,
        allow_domain_literal=allow_domain_literal,
        allow_display_name=allow_display_name,
        check_deliverability=check_deliverability,
        test_environment=test_environment,
        globally_deliverable=globally_deliverable,
        timeout=timeout,
        dns_resolver=dns_resolver,
        async_loop=None)
    if not isinstance(ret, ValidatedEmail):  # suppress typing warning
        raise RuntimeError(type(ret))
    return ret


# Validates an email address with DNS queries issued asynchronously.
async def validate_email_async(
    email: Union[str, bytes],
    /,  # prior arguments are positional-only
    *,  # subsequent arguments are keyword-only
    allow_smtputf8: Optional[bool] = None,
    allow_empty_local: bool = False,
    allow_quoted_local: Optional[bool] = None,
    allow_domain_literal: Optional[bool] = None,
    allow_display_name: Optional[bool] = None,
    check_deliverability: Optional[bool] = None,
    test_environment: Optional[bool] = None,
    globally_deliverable: Optional[bool] = None,
    timeout: Optional[int] = None,
    dns_resolver: Optional[object] = None,
    loop: Optional[object] = None
) -> ValidatedEmail:
    coro = validate_email_sync_or_async(
        email,
        allow_smtputf8=allow_smtputf8,
        allow_empty_local=allow_empty_local,
        allow_quoted_local=allow_quoted_local,
        allow_domain_literal=allow_domain_literal,
        allow_display_name=allow_display_name,
        check_deliverability=check_deliverability,
        test_environment=test_environment,
        globally_deliverable=globally_deliverable,
        timeout=timeout,
        dns_resolver=dns_resolver,
        async_loop=loop or True)
    import inspect
    if not inspect.isawaitable(coro):  # suppress typing warning
        raise RuntimeError(type(coro))
    return await coro
