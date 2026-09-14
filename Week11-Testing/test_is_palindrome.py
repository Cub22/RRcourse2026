"""Test suite for `is_palindrome`.

Bonus assignment, Week 11 (Testing) — Reproducible Research.
Jakub Ryłow

Run with:  pytest test_is_palindrome.py -v

The function under test, as given:

    # Returns True if s reads the same forwards and backwards,
    # ignoring case and ignoring spaces. Empty string is a palindrome.
    def is_palindrome(s):
        cleaned = s.lower().replace(" ", "")
        return cleaned == cleaned[::-1]

The partitions tested below are: the empty string, single characters, even and
odd length palindromes, non-palindromes, case differences, spaces in various
positions, digits, and inputs the docstring does not cover at all. The last
group is where the specification and the implementation come apart, and it is
marked `xfail` rather than deleted — a known limitation that is written down is
worth more than a suite that only exercises what already works.
"""

import pytest


def is_palindrome(s):
    cleaned = s.lower().replace(" ", "")
    return cleaned == cleaned[::-1]


# --- the specification, clause by clause ---------------------------------


def test_empty_string_is_a_palindrome():
    """The docstring says so explicitly, so it gets its own test."""
    assert is_palindrome("") is True


def test_single_character_is_a_palindrome():
    assert is_palindrome("a") is True


def test_simple_odd_length_palindrome():
    assert is_palindrome("racecar") is True


def test_simple_even_length_palindrome():
    assert is_palindrome("abba") is True


def test_obvious_non_palindrome_is_rejected():
    assert is_palindrome("python") is False


def test_almost_palindrome_differing_in_one_letter_is_rejected():
    """A near miss, to check the comparison is not accidentally too lenient."""
    assert is_palindrome("racecat") is False


def test_case_is_ignored():
    assert is_palindrome("RaceCar") is True


def test_spaces_between_words_are_ignored():
    assert is_palindrome("never odd or even") is True


@pytest.mark.parametrize(
    "text,expected",
    [
        ("", True),
        ("a", True),
        ("aa", True),
        ("ab", False),
        ("abba", True),
        ("racecar", True),
        ("RaceCar", True),
        ("never odd or even", True),
        ("  race  car  ", True),
        ("python", False),
        ("12321", True),
        ("12345", False),
    ],
    ids=[
        "empty",
        "single-char",
        "doubled-char",
        "two-different-chars",
        "even-length",
        "odd-length",
        "mixed-case",
        "multi-word",
        "irregular-spacing",
        "not-a-palindrome",
        "digits-palindrome",
        "digits-not-palindrome",
    ],
)
def test_partitions(text, expected):
    """One table covering the partitions above, so a new case is one line."""
    assert is_palindrome(text) is expected


def test_leading_and_trailing_spaces_do_not_matter():
    """Spaces are stripped everywhere, not just between words."""
    assert is_palindrome("   abba   ") is True


# --- where the specification and the implementation disagree -------------


@pytest.mark.xfail(
    strict=True,
    reason="punctuation is not removed; the classic palindrome fails. The "
    "docstring only promises to ignore case and spaces, so this is arguably "
    "correct behaviour and a wrong specification rather than a wrong "
    "implementation - but either way a caller will be surprised.",
)
def test_punctuation_should_probably_be_ignored():
    assert is_palindrome("A man, a plan, a canal: Panama") is True


@pytest.mark.xfail(
    strict=True,
    reason="only the literal space character is stripped, so a leading tab "
    "breaks an otherwise valid palindrome. Writing this test also corrected my "
    "first attempt, 'ab\\tba', which passes for the wrong reason: the tab sits "
    "in the middle and is therefore symmetric.",
)
def test_whitespace_other_than_a_space_should_probably_be_ignored():
    assert is_palindrome("\tabba") is True


def test_non_string_input_raises_rather_than_returning_false():
    """Documented so that a later 'fix' returning False is a visible change.

    The specification says nothing about non-strings. The implementation calls
    `.lower()`, so an integer raises AttributeError. Asserting the current
    behaviour turns an accident into a decision.
    """
    with pytest.raises(AttributeError):
        is_palindrome(12321)
