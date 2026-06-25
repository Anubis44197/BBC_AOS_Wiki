# tests/test_math.py
import pytest
from bbc_core.bbc_scalar import BBCScalar, STABLE, WEAK, UNSTABLE, NEG_ZERO, OmegaOperator

def test_bbc_scalar_init():
    s = BBCScalar(10.0, state=STABLE)
    assert s.value == 10.0
    assert s.state == STABLE

def test_bbc_scalar_multiplication():
    s1 = BBCScalar(5.0, state=STABLE)
    s2 = BBCScalar(3.0, state=WEAK)
    res = s1 * s2
    assert res.state == WEAK
    assert res.value == 15.0

def test_omega_operator_trigger():
    s = BBCScalar(-0.0, state=NEG_ZERO)
    triggered = OmegaOperator.trigger(s)
    assert triggered.state == WEAK
    assert triggered.value == 1e-6
    assert triggered.heal_count == 1
