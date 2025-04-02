from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
from sqlalchemy import func

from sqlalchemy.orm import Session
from ..models.database import get_db
from ..models.vulnerability import ComplianceFinding, Vulnerability, CloudProvider

router = APIRouter()

# Pydantic models for request/response
class ComplianceFindingResponse(BaseModel):
    id: str
    vulnerability_id: str
    standard: str
    control_id: str
    description: str
    is_compliant: bool
    evidence: Optional[str] = None
    
    class Config:
        orm_mode = True

class StandardSummary(BaseModel):
    standard: str
    total_controls: int
    compliant_controls: int
    compliance_percentage: float
    
class ComplianceStandard(BaseModel):
    name: str
    description: str
    
class ComplianceControl(BaseModel):
    id: str
    standard: str
    title: str
    description: str

@router.get("/findings", response_model=List[ComplianceFindingResponse])
async def get_compliance_findings(
    standard: Optional[str] = Query(None),
    is_compliant: Optional[bool] = Query(None),
    cloud_provider: Optional[str] = Query(None),
    limit: int = Query(100, gt=0, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get compliance findings with optional filters
    """
    try:
        query = db.query(ComplianceFinding)
        
        if standard:
            query = query.filter(ComplianceFinding.standard == standard)
            
        if is_compliant is not None:
            query = query.filter(ComplianceFinding.is_compliant == is_compliant)
            
        if cloud_provider:
            # Need to join with vulnerabilities to filter by cloud provider
            try:
                provider_enum = CloudProvider(cloud_provider.lower())
                query = query.join(Vulnerability).filter(Vulnerability.cloud_provider == provider_enum)
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid cloud provider value. Must be one of: {[p.value for p in CloudProvider]}"
                )
        
        # Apply pagination
        findings = query.limit(limit).offset(offset).all()
        
        return findings
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving compliance findings: {str(e)}"
        )

@router.get("/standards")
async def get_compliance_standards(db: Session = Depends(get_db)):
    """
    Get list of supported compliance standards
    """
    # Define common compliance standards
    standards = [
        {
            "name": "CIS",
            "description": "Center for Internet Security Benchmarks"
        },
        {
            "name": "NIST_800-53",
            "description": "NIST Special Publication 800-53 Security Controls"
        },
        {
            "name": "PCI_DSS",
            "description": "Payment Card Industry Data Security Standard"
        },
        {
            "name": "ISO_27001",
            "description": "ISO/IEC 27001 Information Security Standard"
        },
        {
            "name": "HIPAA",
            "description": "Health Insurance Portability and Accountability Act"
        },
        {
            "name": "GDPR",
            "description": "General Data Protection Regulation"
        },
        {
            "name": "SOC2",
            "description": "Service Organization Control 2"
        }
    ]
    
    # Get standards that are actually in the database
    try:
        db_standards = db.query(ComplianceFinding.standard).distinct().all()
        db_standard_names = [s[0] for s in db_standards]
        
        # Add any standards from the database that aren't in our predefined list
        standard_names = [s["name"] for s in standards]
        for db_standard in db_standard_names:
            if db_standard not in standard_names:
                standards.append({
                    "name": db_standard,
                    "description": f"{db_standard} Compliance Standard"
                })
    except Exception as e:
        pass  # Ignore database errors and return the predefined list
    
    return {"standards": standards}

@router.get("/standards/{standard}/controls")
async def get_standard_controls(
    standard: str,
    db: Session = Depends(get_db)
):
    """
    Get controls for a specific compliance standard
    """
    try:
        # Query distinct control IDs for the standard
        controls = db.query(
            ComplianceFinding.control_id,
            ComplianceFinding.description
        ).filter(
            ComplianceFinding.standard == standard
        ).distinct().all()
        
        if not controls:
            # Return some sample controls if none found in database
            if standard == "CIS":
                return {
                    "controls": [
                        {"id": "1.1", "title": "Maintain current inventory of assets", "description": "Maintain an accurate and up-to-date inventory of all technology assets."},
                        {"id": "2.1", "title": "Establish and maintain a software inventory", "description": "Establish and maintain a detailed inventory of all licensed software."},
                        {"id": "4.1", "title": "Secure configuration practices", "description": "Establish secure configuration practices for hardware and software."},
                        {"id": "5.1", "title": "Account management process", "description": "Establish and maintain an account management process."}
                    ]
                }
            elif standard == "NIST_800-53":
                return {
                    "controls": [
                        {"id": "AC-1", "title": "Access Control Policy and Procedures", "description": "The organization develops, documents, and disseminates an access control policy."},
                        {"id": "AC-2", "title": "Account Management", "description": "The organization manages information system accounts."},
                        {"id": "RA-5", "title": "Vulnerability Scanning", "description": "The organization scans for vulnerabilities in the information system."},
                        {"id": "SC-7", "title": "Boundary Protection", "description": "The information system monitors and controls communications at external boundaries."}
                    ]
                }
            else:
                return {"controls": []}
        
        # Format controls from database
        result = []
        for control_id, description in controls:
            result.append({
                "id": control_id,
                "title": f"{standard} {control_id}",
                "description": description or f"Control {control_id} for {standard}"
            })
        
        return {"controls": result}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving controls for standard {standard}: {str(e)}"
        )

@router.get("/summary")
async def get_compliance_summary(
    cloud_provider: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get compliance summary across all standards
    """
    try:
        # Build base query
        base_query = db.query(ComplianceFinding)
        
        # Apply cloud provider filter if specified
        if cloud_provider:
            try:
                provider_enum = CloudProvider(cloud_provider.lower())
                base_query = base_query.join(Vulnerability).filter(Vulnerability.cloud_provider == provider_enum)
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid cloud provider value. Must be one of: {[p.value for p in CloudProvider]}"
                )
        
        # Query for summary by standard
        standards_query = db.query(
            ComplianceFinding.standard.label('standard'),
            func.count(ComplianceFinding.id).label('total_controls'),
            func.sum(func.cast(ComplianceFinding.is_compliant, db.Integer)).label('compliant_controls')
        ).group_by(
            ComplianceFinding.standard
        )
        
        # Apply the same cloud provider filter
        if cloud_provider:
            try:
                provider_enum = CloudProvider(cloud_provider.lower())
                standards_query = standards_query.join(Vulnerability).filter(Vulnerability.cloud_provider == provider_enum)
            except ValueError:
                pass
        
        summary = []
        for standard, total, compliant in standards_query.all():
            compliance_percentage = (compliant / total * 100) if total > 0 else 0
            summary.append({
                "standard": standard,
                "total_controls": total,
                "compliant_controls": compliant,
                "compliance_percentage": round(compliance_percentage, 2)
            })
        
        # Calculate overall compliance
        overall_total = sum(item["total_controls"] for item in summary)
        overall_compliant = sum(item["compliant_controls"] for item in summary)
        overall_percentage = (overall_compliant / overall_total * 100) if overall_total > 0 else 0
        
        return {
            "summary": summary,
            "overall": {
                "total_controls": overall_total,
                "compliant_controls": overall_compliant,
                "compliance_percentage": round(overall_percentage, 2)
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving compliance summary: {str(e)}"
        )

@router.get("/standards/{standard}/summary")
async def get_standard_summary(
    standard: str,
    cloud_provider: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get detailed compliance summary for a specific standard
    """
    try:
        # Build base query for controls
        controls_query = db.query(
            ComplianceFinding.control_id.label('control_id'),
            func.count(ComplianceFinding.id).label('total_resources'),
            func.sum(func.cast(ComplianceFinding.is_compliant, db.Integer)).label('compliant_resources')
        ).filter(
            ComplianceFinding.standard == standard
        ).group_by(
            ComplianceFinding.control_id
        )
        
        # Apply cloud provider filter if specified
        if cloud_provider:
            try:
                provider_enum = CloudProvider(cloud_provider.lower())
                controls_query = controls_query.join(Vulnerability).filter(Vulnerability.cloud_provider == provider_enum)
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid cloud provider value. Must be one of: {[p.value for p in CloudProvider]}"
                )
        
        # Get control details
        controls = []
        for control_id, total, compliant in controls_query.all():
            compliance_percentage = (compliant / total * 100) if total > 0 else 0
            controls.append({
                "control_id": control_id,
                "total_resources": total,
                "compliant_resources": compliant,
                "compliance_percentage": round(compliance_percentage, 2)
            })
        
        # Calculate overall compliance for this standard
        overall_total = sum(item["total_resources"] for item in controls)
        overall_compliant = sum(item["compliant_resources"] for item in controls)
        overall_percentage = (overall_compliant / overall_total * 100) if overall_total > 0 else 0
        
        return {
            "standard": standard,
            "controls": controls,
            "overall": {
                "total_resources": overall_total,
                "compliant_resources": overall_compliant,
                "compliance_percentage": round(overall_percentage, 2)
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving summary for standard {standard}: {str(e)}"
        )