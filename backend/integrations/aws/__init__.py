"""
AWS Integration Module

This module provides integration with AWS services for security scanning,
resource discovery, and compliance checks.
"""

from .auth import AWSAuthenticator
from .resources import AWSResourceDiscovery
from .security import AWSSecurity

__all__ = ['AWSAuthenticator', 'AWSResourceDiscovery', 'AWSSecurity']