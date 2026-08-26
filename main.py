from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from services import process_invoices

app = FastAPI(title="Invoice Intake Automation")

class InvoiceProcessResponse(BaseModel):
    status: str
    message: str
    succeed: int
    failed: int
    details: list

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Invoice Extractor"}

@app.post("/process-invoices", response_model=InvoiceProcessResponse)
async def trigger_processing():
    return await process_invoices()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)