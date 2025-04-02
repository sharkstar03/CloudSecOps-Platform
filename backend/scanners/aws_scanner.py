import boto3
import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid

from ..api.models.vulnerability import Vulnerability, SeverityLevel, CloudProvider, VulnerabilityStatus

# Configure logging
logger = logging.getLogger(__name__)

class AWSScanner:
    """
    Scanner for AWS resources to identify security vulnerabilities and compliance issues.
    """
    
    def __init__(self, aws_access_key: Optional[str] = None, aws_secret_key: Optional[str] = None, 
                 aws_region: str = "us-east-1", session: Optional[boto3.Session] = None):
        """
        Initialize the AWS Scanner.
        
        Args:
            aws_access_key: AWS Access Key ID
            aws_secret_key: AWS Secret Access Key
            aws_region: AWS Region
            session: Existing boto3 Session (if provided, credentials and region are ignored)
        """
        self.aws_region = aws_region
        
        if session:
            self.session = session
        else:
            self.session = boto3.Session(
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=aws_region
            )
        
        logger.info(f"Initialized AWS Scanner for region {aws_region}")
        
        # Initialize service clients
        self.ec2 = self.session.client('ec2')
        self.s3 = self.session.client('s3')
        self.iam = self.session.client('iam')
        self.security_hub = self.session.client('securityhub')
        self.guardduty = self.session.client('guardduty')
        
    async def scan_all(self) -> List[Vulnerability]:
        """
        Run all scanners and return combined vulnerabilities.
        
        Returns:
            List of found vulnerabilities
        """
        logger.info("Starting full AWS security scan")
        
        vulnerabilities = []
        
        # Run all scan methods
        vulnerabilities.extend(await self.scan_security_groups())
        vulnerabilities.extend(await self.scan_s3_buckets())
        vulnerabilities.extend(await self.scan_iam_policies())
        vulnerabilities.extend(await self.fetch_security_hub_findings())
        vulnerabilities.extend(await self.fetch_guardduty_findings())
        
        logger.info(f"AWS scan completed. Found {len(vulnerabilities)} vulnerabilities.")
        return vulnerabilities
    
    async def scan_security_groups(self) -> List[Vulnerability]:
        """
        Scan EC2 security groups for vulnerabilities.
        
        Returns:
            List of found vulnerabilities
        """
        logger.info("Scanning AWS EC2 security groups")
        vulnerabilities = []
        
        try:
            response = self.ec2.describe_security_groups()
            
            for sg in response['SecurityGroups']:
                sg_id = sg['GroupId']
                sg_name = sg.get('GroupName', 'Unknown')
                
                # Check for overly permissive rules
                for permission in sg.get('IpPermissions', []):
                    # Check for 0.0.0.0/0 ingress
                    for ip_range in permission.get('IpRanges', []):
                        if ip_range.get('CidrIp') == '0.0.0.0/0':
                            port_range = f"{permission.get('FromPort', 'Any')}-{permission.get('ToPort', 'Any')}"
                            protocol = permission.get('IpProtocol', 'All')
                            
                            # Check if this is a critical port (SSH, RDP, etc.)
                            severity = SeverityLevel.MEDIUM
                            if permission.get('FromPort') in [22, 3389, 1433, 3306, 5432]:
                                severity = SeverityLevel.CRITICAL
                            
                            vuln = Vulnerability(
                                id=str(uuid.uuid4()),
                                title=f"Security Group {sg_name} has overly permissive ingress rule",
                                description=f"Security Group {sg_id} ({sg_name}) allows unrestricted access (0.0.0.0/0) "
                                           f"for ports {port_range} using protocol {protocol}.",
                                resource_id=sg_id,
                                resource_type="SecurityGroup",
                                cloud_provider=CloudProvider.AWS,
                                region=self.aws_region,
                                severity=severity,
                                status=VulnerabilityStatus.OPEN,
                                remediation_steps="Restrict the security group rule to only necessary IP ranges. "
                                                "Avoid using 0.0.0.0/0 especially for administrative ports.",
                                detected_at=datetime.utcnow()
                            )
                            
                            vulnerabilities.append(vuln)
            
            logger.info(f"Found {len(vulnerabilities)} security group vulnerabilities")
            return vulnerabilities
                            
        except Exception as e:
            logger.error(f"Error scanning EC2 security groups: {e}")
            return []

    async def scan_s3_buckets(self) -> List[Vulnerability]:
        """
        Scan S3 buckets for vulnerabilities.
        
        Returns:
            List of found vulnerabilities
        """
        logger.info("Scanning AWS S3 buckets")
        vulnerabilities = []
        
        try:
            response = self.s3.list_buckets()
            
            for bucket in response['Buckets']:
                bucket_name = bucket['Name']
                
                # Check bucket encryption
                try:
                    encryption = self.s3.get_bucket_encryption(Bucket=bucket_name)
                except self.s3.exceptions.ClientError as e:
                    if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                        vuln = Vulnerability(
                            id=str(uuid.uuid4()),
                            title=f"S3 Bucket {bucket_name} is not encrypted",
                            description=f"S3 Bucket {bucket_name} does not have default encryption enabled.",
                            resource_id=bucket_name,
                            resource_type="S3Bucket",
                            cloud_provider=CloudProvider.AWS,
                            region=self.aws_region,
                            severity=SeverityLevel.HIGH,
                            status=VulnerabilityStatus.OPEN,
                            remediation_steps="Enable default encryption on the S3 bucket using either SSE-S3 or SSE-KMS.",
                            detected_at=datetime.utcnow()
                        )
                        vulnerabilities.append(vuln)
                
                # Check public access
                try:
                    public_access = self.s3.get_public_access_block(Bucket=bucket_name)
                    block_config = public_access.get('PublicAccessBlockConfiguration', {})
                    
                    if not all([
                        block_config.get('BlockPublicAcls', False),
                        block_config.get('IgnorePublicAcls', False),
                        block_config.get('BlockPublicPolicy', False),
                        block_config.get('RestrictPublicBuckets', False)
                    ]):
                        vuln = Vulnerability(
                            id=str(uuid.uuid4()),
                            title=f"S3 Bucket {bucket_name} has public access enabled",
                            description=f"S3 Bucket {bucket_name} does not have all public access block settings enabled.",
                            resource_id=bucket_name,
                            resource_type="S3Bucket",
                            cloud_provider=CloudProvider.AWS,
                            region=self.aws_region,
                            severity=SeverityLevel.HIGH,
                            status=VulnerabilityStatus.OPEN,
                            remediation_steps="Enable all public access block settings for the S3 bucket.",
                            detected_at=datetime.utcnow()
                        )
                        vulnerabilities.append(vuln)
                        
                except Exception as e:
                    logger.warning(f"Could not check public access for bucket {bucket_name}: {e}")
            
            logger.info(f"Found {len(vulnerabilities)} S3 bucket vulnerabilities")
            return vulnerabilities
                    
        except Exception as e:
            logger.error(f"Error scanning S3 buckets: {e}")
            return []
    
    async def scan_iam_policies(self) -> List[Vulnerability]:
        """
        Scan IAM policies for vulnerabilities.
        
        Returns:
            List of found vulnerabilities
        """
        logger.info("Scanning AWS IAM policies")
        vulnerabilities = []
        
        try:
            # Get all policies
            response = self.iam.list_policies(Scope='Local')
            
            for policy in response['Policies']:
                policy_id = policy['PolicyId']
                policy_name = policy['PolicyName']
                
                # Get policy version details
                policy_version = self.iam.get_policy_version(
                    PolicyArn=policy['Arn'],
                    VersionId=policy['DefaultVersionId']
                )
                
                # Check for overly permissive policies
                document = policy_version['PolicyVersion']['Document']
                
                # Check for * actions with * resources
                for statement in document.get('Statement', []):
                    if isinstance(statement, dict):
                        effect = statement.get('Effect')
                        action = statement.get('Action')
                        resource = statement.get('Resource')
                        
                        if effect == 'Allow' and (action == '*' or (isinstance(action, list) and '*' in action)) and \
                           (resource == '*' or (isinstance(resource, list) and '*' in resource)):
                            
                            vuln = Vulnerability(
                                id=str(uuid.uuid4()),
                                title=f"IAM Policy {policy_name} has overly permissive permissions",
                                description=f"IAM Policy {policy_name} ({policy_id}) allows all actions (*) on all resources (*).",
                                resource_id=policy_id,
                                resource_type="IAMPolicy",
                                cloud_provider=CloudProvider.AWS,
                                region="global",
                                severity=SeverityLevel.CRITICAL,
                                status=VulnerabilityStatus.OPEN,
                                remediation_steps="Revise the IAM policy to follow the principle of least privilege. "
                                                "Specify only the actions and resources that are necessary.",
                                detected_at=datetime.utcnow()
                            )
                            vulnerabilities.append(vuln)
            
            logger.info(f"Found {len(vulnerabilities)} IAM policy vulnerabilities")
            return vulnerabilities
                            
        except Exception as e:
            logger.error(f"Error scanning IAM policies: {e}")
            return []
    
    async def fetch_security_hub_findings(self) -> List[Vulnerability]:
        """
        Fetch findings from AWS Security Hub.
        
        Returns:
            List of vulnerabilities from Security Hub
        """
        logger.info("Fetching AWS Security Hub findings")
        vulnerabilities = []
        
        try:
            # Check if Security Hub is enabled
            try:
                self.security_hub.get_findings(MaxResults=1)
            except Exception as e:
                logger.warning(f"Security Hub may not be enabled: {e}")
                return []
            
            # Get findings with HIGH or CRITICAL severity
            response = self.security_hub.get_findings(
                Filters={
                    'SeverityLabel': {
                        'Comparison': 'EQUALS',
                        'Value': 'HIGH'
                    }
                },
                MaxResults=100
            )
            
            for finding in response['Findings']:
                resources = finding.get('Resources', [])
                resource_id = resources[0].get('Id', 'Unknown') if resources else 'Unknown'
                resource_type = resources[0].get('Type', 'Unknown') if resources else 'Unknown'
                
                # Map Security Hub severity to our severity
                severity_map = {
                    'CRITICAL': SeverityLevel.CRITICAL,
                    'HIGH': SeverityLevel.HIGH,
                    'MEDIUM': SeverityLevel.MEDIUM,
                    'LOW': SeverityLevel.LOW,
                    'INFORMATIONAL': SeverityLevel.INFO
                }
                
                severity = severity_map.get(finding.get('Severity', {}).get('Label', 'LOW'), SeverityLevel.LOW)
                
                vuln = Vulnerability(
                    id=str(uuid.uuid4()),
                    title=finding.get('Title', 'Security Hub Finding'),
                    description=finding.get('Description', 'No description provided'),
                    resource_id=resource_id,
                    resource_type=resource_type,
                    cloud_provider=CloudProvider.AWS,
                    region=finding.get('Region', self.aws_region),
                    severity=severity,
                    status=VulnerabilityStatus.OPEN,
                    remediation_steps=finding.get('Remediation', {}).get('Recommendation', {}).get('Text', 'See AWS Security Hub for remediation steps.'),
                    detected_at=datetime.utcnow()
                )
                vulnerabilities.append(vuln)
            
            logger.info(f"Found {len(vulnerabilities)} Security Hub findings")
            return vulnerabilities
                
        except Exception as e:
            logger.error(f"Error fetching Security Hub findings: {e}")
            return []
    
    async def fetch_guardduty_findings(self) -> List[Vulnerability]:
        """
        Fetch findings from AWS GuardDuty.
        
        Returns:
            List of vulnerabilities from GuardDuty
        """
        logger.info("Fetching AWS GuardDuty findings")
        vulnerabilities = []
        
        try:
            # Check if GuardDuty is enabled
            detector_ids = []
            try:
                detector_response = self.guardduty.list_detectors()
                detector_ids = detector_response.get('DetectorIds', [])
                if not detector_ids:
                    logger.warning("GuardDuty is not enabled in this region")
                    return []
            except Exception as e:
                logger.warning(f"GuardDuty may not be enabled: {e}")
                return []
            
            # Get findings for each detector
            for detector_id in detector_ids:
                response = self.guardduty.list_findings(
                    DetectorId=detector_id,
                    FindingCriteria={
                        'Criterion': {
                            'severity': {
                                'Gt': 4.0  # Medium to High severity
                            }
                        }
                    },
                    MaxResults=100
                )
                
                finding_ids = response.get('FindingIds', [])
                
                if finding_ids:
                    findings_response = self.guardduty.get_findings(
                        DetectorId=detector_id,
                        FindingIds=finding_ids
                    )
                    
                    for finding in findings_response.get('Findings', []):
                        # Map GuardDuty severity to our severity
                        gd_severity = finding.get('Severity', 0)
                        
                        if gd_severity >= 7.0:
                            severity = SeverityLevel.CRITICAL
                        elif gd_severity >= 5.0:
                            severity = SeverityLevel.HIGH
                        elif gd_severity >= 3.0:
                            severity = SeverityLevel.MEDIUM
                        elif gd_severity >= 1.0:
                            severity = SeverityLevel.LOW
                        else:
                            severity = SeverityLevel.INFO
                        
                        # Extract resource details
                        resource = finding.get('Resource', {})
                        resource_type = resource.get('ResourceType', 'Unknown')
                        
                        # Get resource ID based on type
                        resource_id = 'Unknown'
                        if resource_type == 'Instance':
                            resource_id = resource.get('InstanceDetails', {}).get('InstanceId', 'Unknown')
                        elif resource_type == 'AccessKey':
                            resource_id = resource.get('AccessKeyDetails', {}).get('AccessKeyId', 'Unknown')
                        elif resource_type == 'S3Bucket':
                            resource_id = resource.get('S3BucketDetails', {}).get('Name', 'Unknown')
                        
                        vuln = Vulnerability(
                            id=str(uuid.uuid4()),
                            title=finding.get('Title', 'GuardDuty Finding'),
                            description=finding.get('Description', 'No description provided'),
                            resource_id=resource_id,
                            resource_type=resource_type,
                            cloud_provider=CloudProvider.AWS,
                            region=self.aws_region,
                            severity=severity,
                            status=VulnerabilityStatus.OPEN,
                            cvss_score=gd_severity,
                            remediation_steps="Review the GuardDuty finding details and follow AWS recommended steps.",
                            detected_at=datetime.utcnow()
                        )
                        vulnerabilities.append(vuln)
            
            logger.info(f"Found {len(vulnerabilities)} GuardDuty findings")
            return vulnerabilities
                
        except Exception as e:
            logger.error(f"Error fetching GuardDuty findings: {e}")
            return []