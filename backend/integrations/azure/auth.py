"""
Azure Authentication Module

Handles authentication and session management for Azure services.
"""

import logging
from typing import Optional, Dict, Any
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.subscription import SubscriptionClient
from azure.core.exceptions import ClientAuthenticationError

logger = logging.getLogger(__name__)

class AzureAuthenticator:
    """
    Handles Azure authentication using various methods including:
    - Service Principal (client ID + secret)
    - Managed Identity
    - Default Azure credentials
    """
    
    def __init__(self):
        """Initialize the Azure authenticator"""
        self.credential = None
        self.subscription_id = None
        self.tenant_id = None
        
    def authenticate_with_service_principal(self, 
                                          client_id: str, 
                                          client_secret: str, 
                                          tenant_id: str) -> ClientSecretCredential:
        """
        Authenticate using Azure Service Principal credentials
        
        Args:
            client_id: Azure client (application) ID
            client_secret: Azure client secret
            tenant_id: Azure tenant ID
            
        Returns:
            ClientSecretCredential: Azure credential object
        """
        try:
            self.tenant_id = tenant_id
            self.credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
            
            # Test the credentials by accessing subscription info
            subscription_client = SubscriptionClient(self.credential)
            subscriptions = list(subscription_client.subscriptions.list())
            
            if subscriptions:
                self.subscription_id = subscriptions[0].subscription_id
                logger.info(f"Successfully authenticated with Azure (Tenant: {tenant_id})")
            else:
                logger.warning("Authenticated but no subscriptions found")
                
            return self.credential
            
        except ClientAuthenticationError as e:
            logger.error(f"Azure authentication failed: {str(e)}")
            raise
    
    def authenticate_with_default_credentials(self) -> DefaultAzureCredential:
        """
        Authenticate using DefaultAzureCredential, which tries multiple methods
        
        Returns:
            DefaultAzureCredential: Azure credential object
        """
        try:
            self.credential = DefaultAzureCredential()
            
            # Test the credentials
            subscription_client = SubscriptionClient(self.credential)
            subscriptions = list(subscription_client.subscriptions.list())
            
            if subscriptions:
                self.subscription_id = subscriptions[0].subscription_id
                self.tenant_id = subscriptions[0].tenant_id
                logger.info("Successfully authenticated with Azure using default credentials")
            else:
                logger.warning("Authenticated but no subscriptions found")
                
            return self.credential
            
        except ClientAuthenticationError as e:
            logger.error(f"Azure default authentication failed: {str(e)}")
            raise
    
    def set_subscription(self, subscription_id: str):
        """
        Set the active subscription ID
        
        Args:
            subscription_id: Azure subscription ID to use
        """
        self.subscription_id = subscription_id
        logger.info(f"Set active subscription to: {subscription_id}")
    
    def get_credential(self) -> Any:
        """Get the current Azure credential object"""
        if not self.credential:
            raise ValueError("No active Azure credentials. Call authenticate_* method first.")
        return self.credential
    
    def get_subscription_id(self) -> Optional[str]:
        """Get the current Azure subscription ID"""
        return self.subscription_id
    
    def get_tenant_id(self) -> Optional[str]:
        """Get the current Azure tenant ID"""
        return self.tenant_id
    
    def create_client(self, client_class: Any, **kwargs) -> Any:
        """
        Create an Azure SDK client using the active credentials
        
        Args:
            client_class: Azure SDK client class to instantiate
            **kwargs: Additional arguments to pass to the client constructor
            
        Returns:
            Instance of the specified Azure SDK client
        """
        if not self.credential:
            raise ValueError("No active Azure credentials. Call authenticate_* method first.")
        
        if 'subscription_id' not in kwargs and self.subscription_id:
            kwargs['subscription_id'] = self.subscription_id
            
        return client_class(credential=self.credential, **kwargs)
    
    def list_subscriptions(self) -> list:
        """
        List all accessible Azure subscriptions
        
        Returns:
            List of subscription objects
        """
        if not self.credential:
            raise ValueError("No active Azure credentials. Call authenticate_* method first.")
            
        subscription_client = SubscriptionClient(self.credential)
        return list(subscription_client.subscriptions.list())
    
    def list_resource_groups(self) -> list:
        """
        List all resource groups in the current subscription
        
        Returns:
            List of resource group objects
        """
        if not self.credential or not self.subscription_id:
            raise ValueError("No active Azure credentials or subscription ID.")
            
        resource_client = ResourceManagementClient(self.credential, self.subscription_id)
        return list(resource_client.resource_groups.list())