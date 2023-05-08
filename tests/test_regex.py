import re

from src.json_parser import DUPLICATE_REGEX


def test_duplicate_id() -> None:
    assert re.fullmatch(DUPLICATE_REGEX, "ABCDE-1") is not None
    assert re.fullmatch(DUPLICATE_REGEX, "ABC-r") is not None
    assert re.fullmatch(DUPLICATE_REGEX, "ABCDE-") is None
    assert re.fullmatch(DUPLICATE_REGEX, "ABCDE-1-r") is not None
    assert re.fullmatch(DUPLICATE_REGEX, "ABC-1r") is None
    assert re.fullmatch(DUPLICATE_REGEX, "ABCDE") is None
    assert re.fullmatch(DUPLICATE_REGEX, "ABC-DEF-G") is None
    assert re.fullmatch(DUPLICATE_REGEX, "") is None
    assert re.fullmatch(DUPLICATE_REGEX, "-r") is not None