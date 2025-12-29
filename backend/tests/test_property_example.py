"""
Example property-based test using Hypothesis
"""

from hypothesis import given, strategies as st
import pytest


@given(st.text())
def test_string_length_property(s):
    """
    Property test example: String length is always non-negative
    **Feature: health-insight-core, Property Example: String length non-negative**
    """
    assert len(s) >= 0


@given(st.integers(), st.integers())
def test_addition_commutative_property(a, b):
    """
    Property test example: Addition is commutative
    **Feature: health-insight-core, Property Example: Addition commutative**
    """
    assert a + b == b + a