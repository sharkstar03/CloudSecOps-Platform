from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import os

from sqlalchemy.orm import Session
from ..models.database import get_db
from ...scanners.aws_scanner import AWSScanner
from ...scanners.vulnerability_db import VulnerabilityDatabase
from ..models.vulnerability import SeverityLevel, CloudProvider, VulnerabilityStatus

router = APIRouter()

# Pydantic models for request/response
class AWSCredentials(BaseModel):
    access_key: str
    secret_key: str
    region: str = "us-east-1"
    
class ScanResponse(BaseModel):
    scan_id: str
    status: str
    message: str
    
class VulnerabilityResponse(BaseModel):
    id: str
    title: str
    description: str
    resource_id: str
    resource_type: str
    severity: str
    status: str
    detected_at: datetime
    
    class Config:
        orm_mode = True

# Background task to run AWS scan
async def run_aws_scan(credentials: AWSCredentials, db: Session):
    scanner = AWSScanner(
        aws_access_key=credentials.access_key,
        aws_secret_key=credentials.secret_key,
        aws_region=credentials.region
    )
    
    # Run the scan
    vulnerabilities = await scanner.scan_all()
    
    # Store results in database
    db_interface = VulnerabilityDatabase(db_session=db)
    await db_interface.store_vulnerabilities(vulnerabilities)

@router.post("/scan", response_model=ScanResponse)
async def scan_aws_resources(
    credentials: AWSCredentials,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start a scan of AWS resources for security vulnerabilities
    """
    # Generate a scan ID
    import uuid
    scan_id = str(uuid.uuid4())
    
    try:
        # Add the scan task to background tasks
        background_tasks.add_task(run_aws_scan, credentials, db)
        
        return {
            "scan_id": scan_id,
            "status": "started",
            "message": "AWS scan started successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error starting AWS scan: {str(e)}"
        )

@router.get("/vulnerabilities", response_model=List[VulnerabilityResponse])
async def get_aws_vulnerabilities(
    severity: Optional[List[str]] = Query(None),
    status: Optional[List[str]] = Query(None),
    resource_type: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    limit: int = Query(100, gt=0, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get vulnerabilities from AWS resources
    """
    try:
        db_interface = VulnerabilityDatabase(db_session=db)
        
        # Convert string severity to enum if provided
        severity_enums = None
        if severity:
            try:
                severity_enums = [SeverityLevel(s.lower()) for s in severity]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid severity value. Must be one of: {[s.value for s in SeverityLevel]}"
                )
        
        # Convert string status to enum if provided
        status_enums = None
        if status:
            try:
                status_enums = [VulnerabilityStatus(s.lower()) for s in status]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status value. Must be one of: {[s.value for s in VulnerabilityStatus]}"
                )
        
        vulnerabilities = await db_interface.get_vulnerabilities(
            cloud_provider=CloudProvider.AWS.value,
            severity=severity_enums,
            status=status_enums,
            resource_type=resource_type,
            region=region,
            limit=limit,
            offset=offset
        )
        
        return vulnerabilities
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving AWS vulnerabilities: {str(e)}"
        )

@router.get("/statistics")
async def get_aws_statistics(db: Session = Depends(get_db)):
    """
    Get statistics for AWS vulnerabilities
    """
    try:
        db_interface = VulnerabilityDatabase(db_session=db)
        all_stats = await db_interface.get_statistics()
        
        # Filter for AWS only
        aws_stats = {
            "total": 0,
            "by_severity": {},
            "by_status": {},
            "by_resource_type": {},
            "recent_24h": 0
        }
        
        # If we have provider stats, extract AWS
        if "by_cloud_provider" in all_stats and CloudProvider.AWS.value in all_stats["by_cloud_provider"]:
            aws_stats["total"] = all_stats["by_cloud_provider"][CloudProvider.AWS.value]
        
        # TODO: Implement more detailed AWS-specific statistics
        
        return aws_stats
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving AWS statistics: {str(e)}"
        )

@router.get("/resources/{resource_id}/vulnerabilities")
async def get_resource_vulnerabilities(
    resource_id: str,
    db: Session = Depends(get_db)
):
    """
    Get vulnerabilities for a specific AWS resource
    """
    try:
        db_interface = VulnerabilityDatabase(db_session=db)
        
        # Custom query for resource vulnerabilities
        query = f"""
        SELECT * FROM vulnerabilities 
        WHERE resource_id = '{resource_id}'
        AND cloud_provider = '{CloudProvider.AWS.value}'
        ORDER BY severity, detected_at DESC
        """
        
        # Execute raw query
        result = db.execute(query).fetchall()
        
        # Convert to Vulnerability objects
        vulnerabilities = [dict(row) for row in result]
        
        return vulnerabilities
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving vulnerabilities for resource {resource_id}: {str(e)}"
        )

@router.post("/vulnerabilities/{vulnerability_id}/status")
async def update_vulnerability_status(
    vulnerability_id: str,
    status: str,
    db: Session = Depends(get_db)
):
    """
    Update the status of an AWS vulnerability
    """
    try:
        # Validate status
        try:
            status_enum = VulnerabilityStatus(status.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status value. Must be one of: {[s.value for s in VulnerabilityStatus]}"
            )
        
        db_interface = VulnerabilityDatabase(db_session=db)
        success = await db_interface.update_vulnerability_status(
            vulnerability_id=vulnerability_id,
            new_status=status_enum
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Vulnerability with ID {vulnerability_id} not found"
            )
        
        return {"status": "success", "message": f"Status updated to {status}"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating vulnerability status: {str(e)}"
        )

@router.get("/regions")
async def get_aws_regions():
    """
    Get a list of AWS regions
    """
    # List of AWS regions
    regions = [
        "us-east-1", "us-east-2", "us-west-1", "us-west-2",
        "af-south-1", "ap-east-1", "ap-south-1", "ap-northeast-3",
        "ap-northeast-2", "ap-southeast-1", "ap-southeast-2", "ap-northeast-1",
        "ca-central-1", "eu-central-1", "eu-west-1", "eu-west-2",
        "eu-south-1", "eu-west-3", "eu-north-1", "me-south-1",
        "sa-east-1"
    ]
    
    return {"regions": regions}

@router.get("/resource-types")
async def get_aws_resource_types():
    """
    Get a list of AWS resource types
    """
    # List of common AWS resource types
    resource_types = [
        "EC2Instance", "SecurityGroup", "S3Bucket", "IAMUser",
        "IAMRole", "IAMPolicy", "RDSInstance", "DynamoDBTable",
        "LambdaFunction", "ELBLoadBalancer", "VPC", "Subnet",
        "RouteTable", "InternetGateway", "NATGateway", "ElasticIP"
    ]
    
    return {"resource_types": resource_types}