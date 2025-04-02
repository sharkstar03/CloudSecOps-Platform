"""
AWS Authentication Module

Handles authentication and session management for AWS services.
"""

import boto3
import logging
from botocore.exceptions import ClientError
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class AWSAuthenticator:
    """
    Handles AWS authentication using various methods including:
    - AWS Access Keys
    - IAM Role assumption
    - STS temporary credentials
    """
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize the AWS authenticator
        
        Args:
            region: Default AWS region to use
        """
        self.region = region
        self.session = None
        self.sts_client = None
        self.account_id = None
    
    def authenticate_with_keys(self, 
                              access_key: str, 
                              secret_key: str, 
                              region: Optional[str] = None) -> boto3.Session:
        """
        Authenticate using AWS access and secret keys
        
        Args:
            access_key: AWS access key ID
            secret_key: AWS secret access key
            region: AWS region (optional, uses default if not provided)
            
        Returns:
            boto3.Session: Authenticated session
        """
        try:
            self.session = boto3.Session(
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region or self.region
            )
            
            # Verify the credentials work by getting the account ID
            self.sts_client = self.session.client('sts')
            response = self.sts_client.get_caller_identity()
            self.account_id = response['Account']
            
            logger.info(f"Successfully authenticated with AWS (Account: {self.account_id})")
            return self.session
            
        except ClientError as e:
            logger.error(f"AWS authentication failed: {str(e)}")
            raise
    
    def assume_role(self, 
                   role_arn: str, 
                   session_name: str = "CloudSecOpsSession",
                   duration_seconds: int = 3600) -> Dict[str, Any]:
        """
        Assume an IAM role using STS
        
        Args:
            role_arn: ARN of the role to assume
            session_name: Name for the session
            duration_seconds: Duration for the temporary credentials
            
        Returns:
            Dict containing temporary credentials
        """
        if not self.sts_client:
            if not self.session:
                # Create default session
                self.session = boto3.Session(region_name=self.region)
            self.sts_client = self.session.client('sts')
            
        try:
            response = self.sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName=session_name,
                DurationSeconds=duration_seconds
            )
            
            credentials = response['Credentials']
            logger.info(f"Successfully assumed role: {role_arn}")
            
            # Create a new session with the temporary credentials
            self.session = boto3.Session(
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken'],
                region_name=self.region
            )
            
            return credentials
            
        except ClientError as e:
            logger.error(f"Failed to assume role {role_arn}: {str(e)}")
            raise
    
    def get_account_id(self) -> Optional[str]:
        """Get the current AWS account ID"""
        return self.account_id
    
    def get_session(self) -> Optional[boto3.Session]:
        """Get the current boto3 session"""
        return self.session
    
    def create_client(self, service_name: str) -> Any:
        """
        Create a boto3 client for the specified service
        
        Args:
            service_name: AWS service name (e.g., 's3', 'ec2', 'guardduty')
            
        Returns:
            boto3 client for the specified service
        """
        if not self.session:
            raise ValueError("No active AWS session. Call authenticate_with_keys() first.")
        
        return self.session.client(service_name)
    
    def create_resource(self, service_name: str) -> Any:
        """
        Create a boto3 resource for the specified service
        
        Args:
            service_name: AWS service name (e.g., 's3', 'ec2')
            
        Returns:
            boto3 resource for the specified service
        """
        if not self.session:
            raise ValueError("No active AWS session. Call authenticate_with_keys() first.")
        
        return self.session.resource(service_name)