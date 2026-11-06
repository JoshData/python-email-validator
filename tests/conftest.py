
from typing import Any

from email_validator import ValidatedEmail


def pytest_assertrepr_compare(config: Any, op: str, left: Any, right: Any) -> list[str] | None:
    if isinstance(left, ValidatedEmail) and isinstance(right, ValidatedEmail) and op == "==":
        leftDict = left.as_dict()
        rightDict = right.as_dict()
        keys = set(leftDict) | set(rightDict)
        table = [[key, leftDict.get(key), rightDict.get(key)]
                 for key in keys]
        maxLen = [max(len(repr(row[col])) for row in table) for col in (0, 1, 2)]
        return ([repr(left) + " != " + repr(right)]
                + [(str(t[0]).rjust(maxLen[0])
                   + " " + repr(t[1]).ljust(maxLen[1])
                   + (" ==" if t[1] == t[2] else " !=")
                   + " " + repr(t[2]).ljust(maxLen[2]))
                   for t in table])
    return None
