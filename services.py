import os
import httpx
from fastapi import HTTPException
from schemas import InvoicePayload
from extractor import extract_invoice_data

ACCOUNTING_API_URL = "http://localhost:8080"
API_KEY = "demo-key-1234"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}


async def process_invoices():
    
    async with httpx.AsyncClient() as client :
        try:
            partner_resp=await  client.get(f"{ACCOUNTING_API_URL}/partners", headers=HEADERS)
            partner_resp.raise_for_status()
            partners = partner_resp.json()["data"]["partners"]
            
        except Exception as e :
            raise HTTPException(status_code=500, detail=f"Unable to fetch ")
    
    invoice_dir = "invoices"
    if not os.path.exists(invoice_dir):
        raise HTTPException(status_code=400, detail="'invoices' folder not found !")
    
    files = [f for f in os.listdir(invoice_dir) if f.lower().endswith(('.pdf','.jpg'))]
    
    results=[]
    success_count=0
    fail_count=0
    
    async with httpx.AsyncClient(timeout=60) as client:
        for filename in files:
            file_path= os.path.join(invoice_dir, filename)
            try:
                extracted_data = await extract_invoice_data(file_path, partners)
                validated_data= InvoicePayload(**extracted_data)
                post_resp= await client.post(f"{ACCOUNTING_API_URL}/invoices", headers=HEADERS, json=validated_data.model_dump())
                if post_resp.status_code == 201:
                    success_count +=1
                    results.append({"file":filename, "status":"success"})
                else:
                    fail_count += 1
                    results.append({"file":filename , "status":"api_rejected" , "error":post_resp.json()})
            except Exception as e :
                fail_count += 1
                results.append({"file":filename, "status":"extraction_failed", "error":str(e)})
                
                        
    
    return {
        "status": "completed",
        "message": f"Processed {len(files)} files.",
        "succeed": success_count,
        "failed": fail_count,
        "details": results
    }
