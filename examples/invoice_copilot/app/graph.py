from typing import Dict, Any

def build_graph():
    class SimpleInvoiceAgent:
        def invoke(self, payload: Dict[str, Any]) -> Dict[str, Any]:
            text = payload.get("document_text","")
            return {
                "vendor": payload.get("vendor_hint","Unknown Vendor"),
                "invoice_number": "INV-1023",
                "invoice_date": "2025-10-20",
                "total_amount": 1299.0,
                "currency": payload.get("currency_hint","INR"),
                "line_items": [
                    {"description": "GPU Hosting", "qty": 1, "unit_price": 1299.0, "amount": 1299.0}
                ],
                "notes": "Demo agent response from SimpleInvoiceAgent"
            }
    return SimpleInvoiceAgent()
