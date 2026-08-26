import base64
import pymupdf as pmp
import httpx
import json
import os
from dotenv import load_dotenv
from schemas import InvoicePayload

load_dotenv()


def encode_file_to_base64(file_path: str):
    if file_path.lower().endswith(".pdf"):
        doc = pmp.open(file_path)
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=150)
        return base64.b64encode(pix.tobytes("png")).decode("utf-8"), "image/png"
    else:
        with open(file_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8"), "image/jpeg"


async def extract_invoice_data(file_path: str, partner_master: list) -> dict:
    or_api_key = os.getenv("OR_API_KEY")
    if not or_api_key:
        raise ValueError("Cannot find the api key !")

    partner_info = json.dumps(partner_master, ensure_ascii=False, indent=2)
    schema_definition = json.dumps(InvoicePayload.model_json_schema(), indent=2)

    system_prompt = f"""
    You are an expert Japanese accounting AI. 
    Extract the invoice details from the image and return ONLY a valid JSON object matching this schema:
    {schema_definition}
    
    CRITICAL RULES:
    1. Read the supplier name on the invoice (e.g., "ヤマダ製作所") and map it to the correct 'partner_code' using this master list:
    {partner_info}
    2. Date formats MUST be strictly YYYY-MM-DD.
    3. Currency MUST be "JPY".
    4. Tax codes MUST be "T10" for 10% and "T08" for 8%. 
    5. Return ONLY raw JSON. Do not include markdown blocks like ```json.
    """

    base64_image, mime_type = encode_file_to_base64(file_path)

    headers = {
        "Authorization": f"Bearer {or_api_key}",
        "Content-type": "application/json",
    }

    payload = {
        "model": "google/gemini-3.5-flash-lite",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": system_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{base64_image}"},
                    },
                ],
            }
        ],
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
        )

        # If it's a 400 Bad Request, this will expose exactly what OpenRouter is complaining about!
        if response.status_code != 200:
            raise ValueError(f"OpenRouter Error: {response.text}")

        response.raise_for_status()

        result = response.json()

        raw_content = result["choices"][0]["message"]["content"]
        raw_content = raw_content.replace("```json", "").replace("```", "").strip()

        return json.loads(raw_content)
