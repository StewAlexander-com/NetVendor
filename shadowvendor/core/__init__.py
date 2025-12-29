"""Core functionality for ShadowVendor package."""

from .netvendor import (
    check_dependencies,
    is_mac_address,
    is_mac_address_table,
    parse_port_info,
    main
)
from .oui_manager import OUIManager

__all__ = [
    'check_dependencies',
    'is_mac_address',
    'is_mac_address_table',
    'parse_port_info',
    'main',
    'OUIManager'
]
