from fastapi import FastAPI
from scanners.aws_scanner import check_aws_security
from integrations.aws_integration import AWSIntegration

app = FastAPI()

@app.get("/scan/aws")
async def scan_aws():
    aws = AWSIntegration()
    return check_aws_security(aws.get_resources())