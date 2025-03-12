"""Test to verify our Colors mock is working properly."""

from tests.mocks.terminal_utils import Colors
import pytest


def test_colors_mock():
    """Test that our Colors mock has all necessary attributes."""
    # Basic color attributes
    assert hasattr(Colors, "RED")
    assert hasattr(Colors, "GREEN")
    assert hasattr(Colors, "BLUE")
    assert hasattr(Colors, "YELLOW")
    assert hasattr(Colors, "CYAN")
    assert hasattr(Colors, "MAGENTA")
    
    # Text style attributes
    assert hasattr(Colors, "BOLD")
    assert hasattr(Colors, "UNDERLINE")
    assert hasattr(Colors, "ENDC")
    
    # Background color attributes
    assert hasattr(Colors, "BG_RED")
    assert hasattr(Colors, "BG_GREEN")
    assert hasattr(Colors, "BG_BLUE")
    assert hasattr(Colors, "BG_YELLOW")
    assert hasattr(Colors, "BG_CYAN")
    assert hasattr(Colors, "BG_MAGENTA")