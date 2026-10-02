"""Strict rational input conversion; never accept a binary floating-point value."""
from fractions import Fraction

def rational(value):
    if type(value) is int or isinstance(value, Fraction):
        return Fraction(value)
    if type(value) is str and len(value) <= 4096:
        try:
            return Fraction(value)
        except (ValueError, ZeroDivisionError) as exc:
            raise ValueError('invalid exact rational') from exc
    raise ValueError('exact integer or rational string required; no floats or bools')
