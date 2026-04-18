"""Citadel internal package.

Contains modules that wire the Vortex market scanner to external Citadel
infrastructure (e.g. the mapping-and-inventory Hub).
"""

from .hub_publisher import HubPublisher, ping_hub

__all__ = ["HubPublisher", "ping_hub"]
