"""AWS Lambda entry point via Mangum ASGI adapter."""
from mangum import Mangum

from app.main import app

# lifespan="off" avoids Lambda lifecycle issues with the DynamoDB table-creation
# lifespan event. The table must be pre-created by IaC before first invocation.
handler = Mangum(app, lifespan="off")
