"""
Azure Integration Module

This module provides integration with Azure services for security scanning,
resource discovery, and compliance checks.
"""

from .auth import AzureAuthenticator
from .resources import AzureResourceDiscovery
from .security import AzureSecurity

__all__ = ['AzureAuthenticator', 'AzureResourceDiscovery', 'AzureSecurity']