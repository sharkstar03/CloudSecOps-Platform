"""
CloudSecOps Platform - Cloud Service Integrations Package

This package provides integration interfaces for various cloud providers
including AWS and Azure. It handles authentication, resource discovery,
and security assessment for cloud resources.
"""

from . import aws
from . import azure

__version__ = "0.1.0"