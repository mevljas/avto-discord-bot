"""Module that contains util functions."""

from common.constants import (
    excluded_resource_types,
)


async def block_aggressively(route):
    """
    Prevent loading some resources for better performance.
    """
    if route.request.resource_type in excluded_resource_types:
        await route.abort()
    else:
        await route.continue_()
