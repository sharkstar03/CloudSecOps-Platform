from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import os

from sqlalchemy.orm import Session
from ..models.database import get_db
from ...scanners.azure_scanner import AzureScanner
from ...scanners.vulnerability_db import VulnerabilityDatabase
from ..models.vulnerability import SeverityLevel, CloudProvider, VulnerabilityStatus

router = APIRouter()

# Pydantic models for request/response
class AzureCredentials(BaseModel):
    subscription_id: str
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    
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

# Background task to run Azure scan
async def run_azure_scan(credentials: AzureCredentials, db: Session):
    scanner = AzureScanner(
        subscription_id=credentials.subscription_id,
        tenant_id=credentials.tenant_id,
        client_id=credentials.client_id,
        client_secret=credentials.client_secret
    )
    
    # Run the scan
    vulnerabilities = await scanner.scan_all()
    
    # Store results in database
    db_interface = VulnerabilityDatabase(db_session=db)
    await db_interface.store_vulnerabilities(vulnerabilities)

@router.post("/scan", response_model=ScanResponse)
async def scan_azure_resources(
    credentials: AzureCredentials,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start a scan of Azure resources for security vulnerabilities
    """
    # Generate a scan ID
    import uuid
    scan_id = str(uuid.uuid4())
    
    try:
        # Add the scan task to background tasks
        background_tasks.add_task(run_azure_scan, credentials, db)
        
        return {
            "scan_id": scan_id,
            "status": "started",
            "message": "Azure scan started successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error starting Azure scan: {str(e)}"
        )

@router.get("/vulnerabilities", response_model=List[VulnerabilityResponse])
async def get_azure_vulnerabilities(
    severity: Optional[List[str]] = Query(None),
    status: Optional[List[str]] = Query(None),
    resource_type: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    limit: int = Query(100, gt=0, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get vulnerabilities from Azure resources
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
            cloud_provider=CloudProvider.AZURE.value,
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
            detail=f"Error retrieving Azure vulnerabilities: {str(e)}"
        )

@router.get("/statistics")
async def get_azure_statistics(db: Session = Depends(get_db)):
    """
    Get statistics for Azure vulnerabilities
    """
    try:
        db_interface = VulnerabilityDatabase(db_session=db)
        all_stats = await db_interface.get_statistics()
        
        # Filter for Azure only
        azure_stats = {
            "total": 0,
            "by_severity": {},
            "by_status": {},
            "by_resource_type": {},
            "recent_24h": 0
        }
        
        # If we have provider stats, extract Azure
        if "by_cloud_provider" in all_stats and CloudProvider.AZURE.value in all_stats["by_cloud_provider"]:
            azure_stats["total"] = all_stats["by_cloud_provider"][CloudProvider.AZURE.value]
        
        # TODO: Implement more detailed Azure-specific statistics
        
        return azure_stats
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving Azure statistics: {str(e)}"
        )

@router.get("/resources/{resource_id}/vulnerabilities")
async def get_resource_vulnerabilities(
    resource_id: str,
    db: Session = Depends(get_db)
):
    """
    Get vulnerabilities for a specific Azure resource
    """
    try:
        db_interface = VulnerabilityDatabase(db_session=db)
        
        # Custom query for resource vulnerabilities
        query = f"""
        SELECT * FROM vulnerabilities 
        WHERE resource_id = '{resource_id}'
        AND cloud_provider = '{CloudProvider.AZURE.value}'
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
    Update the status of an Azure vulnerability
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
async def get_azure_regions():
    """
    Get a list of Azure regions
    """
    # List of Azure regions
    regions = [
        "eastus", "eastus2", "westus", "westus2", "centralus", "northcentralus", "southcentralus",
        "westcentralus", "eastasia", "southeastasia", "japaneast", "japanwest", "australiaeast",
        "australiasoutheast", "australiacentral", "australiacentral2", "brazilsouth", "brazilsoutheast",
        "canadacentral", "canadaeast", "northeurope", "westeurope", "francecentral", "francesouth",
        "germanywestcentral", "germanynorth", "norwayeast", "norwaywest", "switzerlandnorth",
        "switzerlandwest", "uksouth", "ukwest", "uaenorth", "uaecentral", "southafricanorth",
        "southafricawest", "indiacentral", "indiasouth", "indiawest", "koreacentral", "koreasouth"
    ]
    
    return {"regions": regions}

@router.get("/resource-types")
async def get_azure_resource_types():
    """
    Get a list of Azure resource types
    """
    # List of common Azure resource types
    resource_types = [
        "VirtualMachine", "NetworkSecurityGroup", "StorageAccount", "VirtualNetwork",
        "WebApp", "FunctionApp", "SqlServer", "SqlDatabase", "CosmosDb",
        "KeyVault", "ManagedIdentity", "LoadBalancer", "ApplicationGateway",
        "AKSCluster", "ContainerRegistry", "LogicApp", "APIManagement"
    ]
    
    return {"resource_types": resource_types}