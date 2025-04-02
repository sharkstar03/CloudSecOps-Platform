import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

# Azure SDK imports
from azure.identity import DefaultAzureCredential
from azure.mgmt.security import SecurityCenter
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.monitor import MonitorManagementClient

from ..api.models.vulnerability import Vulnerability, SeverityLevel, CloudProvider, VulnerabilityStatus

# Configure logging
logger = logging.getLogger(__name__)

class AzureScanner:
    """
    Scanner for Azure resources to identify security vulnerabilities and compliance issues.
    """
    
    def __init__(self, subscription_id: str, tenant_id: Optional[str] = None, 
                 client_id: Optional[str] = None, client_secret: Optional[str] = None):
        """
        Initialize the Azure Scanner.
        
        Args:
            subscription_id: Azure Subscription ID
            tenant_id: Azure Tenant ID (optional if using DefaultAzureCredential)
            client_id: Azure Client ID (optional if using DefaultAzureCredential)
            client_secret: Azure Client Secret (optional if using DefaultAzureCredential)
        """
        self.subscription_id = subscription_id
        
        # Use DefaultAzureCredential which tries multiple authentication methods
        self.credential = DefaultAzureCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        
        logger.info(f"Initialized Azure Scanner for subscription {subscription_id}")
        
        # Initialize service clients
        self.security_client = SecurityCenter(self.credential, self.subscription_id)
        self.resource_client = ResourceManagementClient(self.credential, self.subscription_id)
        self.network_client = NetworkManagementClient(self.credential, self.subscription_id)
        self.storage_client = StorageManagementClient(self.credential, self.subscription_id)
        self.monitor_client = MonitorManagementClient(self.credential, self.subscription_id)
        
    async def scan_all(self) -> List[Vulnerability]:
        """
        Run all scanners and return combined vulnerabilities.
        
        Returns:
            List of found vulnerabilities
        """
        logger.info("Starting full Azure security scan")
        
        vulnerabilities = []
        
        # Run all scan methods
        vulnerabilities.extend(await self.scan_network_security_groups())
        vulnerabilities.extend(await self.scan_storage_accounts())
        vulnerabilities.extend(await self.fetch_security_center_recommendations())
        vulnerabilities.extend(await self.scan_role_assignments())
        
        logger.info(f"Azure scan completed. Found {len(vulnerabilities)} vulnerabilities.")
        return vulnerabilities
    
    async def scan_network_security_groups(self) -> List[Vulnerability]:
        """
        Scan Network Security Groups for vulnerabilities.
        
        Returns:
            List of found vulnerabilities
        """
        logger.info("Scanning Azure Network Security Groups")
        vulnerabilities = []
        
        try:
            # Get all Network Security Groups
            nsgs = list(self.network_client.network_security_groups.list_all())
            
            for nsg in nsgs:
                nsg_id = nsg.id
                nsg_name = nsg.name
                resource_group = nsg_id.split('/')[4]  # Extract resource group from ID
                location = nsg.location
                
                # Check for overly permissive rules
                for rule in nsg.security_rules:
                    # Check for rules that allow Any from Internet
                    if (rule.access == 'Allow' and 
                        rule.direction == 'Inbound' and 
                        (rule.source_address_prefix == '*' or rule.source_address_prefix == 'Internet')):
                        
                        # Check critical ports (22, 3389, etc.)
                        is_critical = False
                        port_range = rule.destination_port_range
                        
                        if port_range in ['22', '3389', '1433', '3306', '5432', '*']:
                            is_critical = True
                        elif '-' in port_range:
                            # Check port ranges
                            try:
                                start_port, end_port = map(int, port_range.split('-'))
                                if (22 >= start_port and 22 <= end_port) or \
                                   (3389 >= start_port and 3389 <= end_port):
                                    is_critical = True
                            except ValueError:
                                pass
                        
                        severity = SeverityLevel.CRITICAL if is_critical else SeverityLevel.HIGH
                        
                        vuln = Vulnerability(
                            id=str(uuid.uuid4()),
                            title=f"NSG {nsg_name} has overly permissive inbound rule",
                            description=f"Network Security Group {nsg_name} has an inbound rule {rule.name} "
                                      f"that allows access from {rule.source_address_prefix} "
                                      f"to port(s) {port_range}",
                            resource_id=nsg_id,
                            resource_type="NetworkSecurityGroup",
                            cloud_provider=CloudProvider.AZURE,
                            region=location,
                            severity=severity,
                            status=VulnerabilityStatus.OPEN,
                            remediation_steps="Restrict the NSG rule to only necessary IP ranges. "
                                            "Avoid using '*' or 'Internet' especially for administrative ports.",
                            detected_at=datetime.utcnow()
                        )
                        
                        vulnerabilities.append(vuln)
            
            logger.info(f"Found {len(vulnerabilities)} NSG vulnerabilities")
            return vulnerabilities
                        
        except Exception as e:
            logger.error(f"Error scanning Network Security Groups: {e}")
            return []
    
    async def scan_storage_accounts(self) -> List[Vulnerability]:
        """
        Scan Storage Accounts for vulnerabilities.
        
        Returns:
            List of found vulnerabilities
        """
        logger.info("Scanning Azure Storage Accounts")
        vulnerabilities = []
        
        try:
            # Get all Storage Accounts
            storage_accounts = list(self.storage_client.storage_accounts.list())
            
            for account in storage_accounts:
                account_id = account.id
                account_name = account.name
                resource_group = account_id.split('/')[4]  # Extract resource group from ID
                location = account.location
                
                # Check for public access
                if account.allow_blob_public_access:
                    vuln = Vulnerability(
                        id=str(uuid.uuid4()),
                        title=f"Storage Account {account_name} allows public blob access",
                        description=f"Storage Account {account_name} has public blob access enabled, "
                                  f"which may expose data if containers are configured with public access.",
                        resource_id=account_id,
                        resource_type="StorageAccount",
                        cloud_provider=CloudProvider.AZURE,
                        region=location,
                        severity=SeverityLevel.HIGH,
                        status=VulnerabilityStatus.OPEN,
                        remediation_steps="Disable public blob access for the storage account unless absolutely necessary.",
                        detected_at=datetime.utcnow()
                    )
                    vulnerabilities.append(vuln)
                
                # Check for secure transfer
                if not account.enable_https_traffic_only:
                    vuln = Vulnerability(
                        id=str(uuid.uuid4()),
                        title=f"Storage Account {account_name} allows non-HTTPS traffic",
                        description=f"Storage Account {account_name} does not enforce secure transfer (HTTPS only), "
                                  f"which may expose data in transit.",
                        resource_id=account_id,
                        resource_type="StorageAccount",
                        cloud_provider=CloudProvider.AZURE,
                        region=location,
                        severity=SeverityLevel.HIGH,
                        status=VulnerabilityStatus.OPEN,
                        remediation_steps="Enable 'Secure transfer required' for the storage account.",
                        detected_at=datetime.utcnow()
                    )
                    vulnerabilities.append(vuln)
                
                # Check for encryption
                if not account.encryption.services.blob.enabled or not account.encryption.services.file.enabled:
                    vuln = Vulnerability(
                        id=str(uuid.uuid4()),
                        title=f"Storage Account {account_name} has incomplete encryption",
                        description=f"Storage Account {account_name} does not have encryption enabled for all services.",
                        resource_id=account_id,
                        resource_type="StorageAccount",
                        cloud_provider=CloudProvider.AZURE,
                        region=location,
                        severity=SeverityLevel.MEDIUM,
                        status=VulnerabilityStatus.OPEN,
                        remediation_steps="Enable encryption for all services in the storage account.",
                        detected_at=datetime.utcnow()
                    )
                    vulnerabilities.append(vuln)
            
            logger.info(f"Found {len(vulnerabilities)} Storage Account vulnerabilities")
            return vulnerabilities
                    
        except Exception as e:
            logger.error(f"Error scanning Storage Accounts: {e}")
            return []
    
    async def fetch_security_center_recommendations(self) -> List[Vulnerability]:
        """
        Fetch recommendations from Azure Security Center.
        
        Returns:
            List of vulnerabilities from Security Center
        """
        logger.info("Fetching Azure Security Center recommendations")
        vulnerabilities = []
        
        try:
            # Get recommendations from Security Center
            assessments = list(self.security_client.assessments.list())
            
            for assessment in assessments:
                # Skip if assessment is compliant
                if assessment.status.code == "Healthy":
                    continue
                
                # Map Security Center severity to our severity
                severity_map = {
                    "High": SeverityLevel.HIGH,
                    "Medium": SeverityLevel.MEDIUM,
                    "Low": SeverityLevel.LOW
                }
                
                severity = severity_map.get(assessment.status.severity, SeverityLevel.MEDIUM)
                
                # Extract resource information
                resource_id = assessment.resource_details.id if hasattr(assessment.resource_details, 'id') else "Unknown"
                resource_type = resource_id.split('/')[-2] if '/' in resource_id else "Unknown"
                
                # Extract location from resource ID
                location = "unknown"
                try:
                    resource = self.resource_client.resources.get_by_id(resource_id, "2021-04-01")
                    location = resource.location
                except Exception:
                    pass
                
                vuln = Vulnerability(
                    id=str(uuid.uuid4()),
                    title=assessment.display_name,
                    description=assessment.metadata.description if hasattr(assessment.metadata, 'description') else "No description provided",
                    resource_id=resource_id,
                    resource_type=resource_type,
                    cloud_provider=CloudProvider.AZURE,
                    region=location,
                    severity=severity,
                    status=VulnerabilityStatus.OPEN,
                    remediation_steps=assessment.metadata.remediation_description if hasattr(assessment.metadata, 'remediation_description') else "See Azure Security Center for remediation steps.",
                    detected_at=datetime.utcnow()
                )
                vulnerabilities.append(vuln)
            
            logger.info(f"Found {len(vulnerabilities)} Security Center recommendations")
            return vulnerabilities
                
        except Exception as e:
            logger.error(f"Error fetching Security Center recommendations: {e}")
            return []
    
    async def scan_role_assignments(self) -> List[Vulnerability]:
        """
        Scan Role Assignments for potential excessive permissions.
        
        Returns:
            List of vulnerabilities from role assignments
        """
        logger.info("Scanning Azure Role Assignments")
        vulnerabilities = []
        
        try:
            from azure.mgmt.authorization import AuthorizationManagementClient
            
            # Initialize authorization client
            auth_client = AuthorizationManagementClient(self.credential, self.subscription_id)
            
            # Get role definitions to check for Owner and Contributor roles
            role_definitions = list(auth_client.role_definitions.list(scope=f"/subscriptions/{self.subscription_id}"))
            
            # Find Owner and Contributor role IDs
            owner_id = None
            contributor_id = None
            
            for role_def in role_definitions:
                if role_def.role_name == "Owner":
                    owner_id = role_def.id
                elif role_def.role_name == "Contributor":
                    contributor_id = role_def.id
            
            if not owner_id or not contributor_id:
                logger.warning("Could not identify Owner or Contributor role IDs")
                return []
            
            # Get role assignments
            role_assignments = list(auth_client.role_assignments.list_for_subscription())
            
            # Track users/principals with Owner/Contributor roles
            owner_assignments = []
            contributor_assignments = []
            
            for assignment in role_assignments:
                role_def_id = assignment.role_definition_id
                principal_id = assignment.principal_id
                
                if role_def_id == owner_id:
                    owner_assignments.append((assignment.id, principal_id))
                elif role_def_id == contributor_id:
                    contributor_assignments.append((assignment.id, principal_id))
            
            # Create vulnerabilities for excessive Owner roles
            if len(owner_assignments) > 3:  # Arbitrary threshold
                vuln = Vulnerability(
                    id=str(uuid.uuid4()),
                    title=f"Excessive number of Owner role assignments",
                    description=f"There are {len(owner_assignments)} Owner role assignments in the subscription. "
                              f"Having too many owners increases the risk surface area.",
                    resource_id=f"/subscriptions/{self.subscription_id}",
                    resource_type="Subscription",
                    cloud_provider=CloudProvider.AZURE,
                    region="global",
                    severity=SeverityLevel.HIGH,
                    status=VulnerabilityStatus.OPEN,
                    remediation_steps="Review Owner role assignments and reduce to minimum necessary. "
                                    "Consider using more granular RBAC roles instead.",
                    detected_at=datetime.utcnow()
                )
                vulnerabilities.append(vuln)
            
            # Check for service principals with Owner roles
            for assignment_id, principal_id in owner_assignments:
                try:
                    # Try to determine if this is a service principal
                    # This is a simplified approach - in real implementation would need Microsoft Graph API
                    if len(principal_id) == 36:  # UUID format
                        vuln = Vulnerability(
                            id=str(uuid.uuid4()),
                            title=f"Service Principal with Owner role",
                            description=f"A service principal (ID: {principal_id}) has Owner role, "
                                      f"which grants full access to manage all resources.",
                            resource_id=assignment_id,
                            resource_type="RoleAssignment",
                            cloud_provider=CloudProvider.AZURE,
                            region="global",
                            severity=SeverityLevel.HIGH,
                            status=VulnerabilityStatus.OPEN,
                            remediation_steps="Review if the service principal truly needs Owner permissions. "
                                            "Consider using a more restrictive role.",
                            detected_at=datetime.utcnow()
                        )
                        vulnerabilities.append(vuln)
                except Exception as e:
                    logger.warning(f"Error checking role assignment {assignment_id}: {e}")
            
            logger.info(f"Found {len(vulnerabilities)} Role Assignment vulnerabilities")
            return vulnerabilities
                
        except Exception as e:
            logger.error(f"Error scanning Role Assignments: {e}")
            return []