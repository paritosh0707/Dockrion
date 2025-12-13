"""
Invoice Processing Service - Handler Mode Example

This module demonstrates the handler pattern where a direct callable function
processes requests instead of going through a framework-specific agent.

Handler functions are useful when you need:
- Custom preprocessing/postprocessing logic
- Business logic wrappers around agents
- Simpler use cases that don't need full agent workflows
- Integration with existing service patterns

Handler Contract:
    def handler(payload: dict) -> dict
"""

from typing import Dict, Any, Optional
from .graph import build_graph

# Cache the agent instance
_agent = None


def get_agent():
    """Get or create the agent instance (cached)."""
    global _agent
    if _agent is None:
        _agent = build_graph()
    return _agent


def process_invoice(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process an invoice document and extract structured data.
    
    This is a handler function that can be used directly with Dockrion's
    handler mode. It wraps the underlying agent with additional logic.
    
    Args:
        payload: Dict containing:
            - document_text (required): The invoice text to process
            - currency_hint (optional): Expected currency (INR, USD, EUR)
            - vendor_hint (optional): Known vendor name
            - user_id (optional): User ID for tracking
            
    Returns:
        Dict containing:
            - vendor: Extracted vendor name
            - invoice_number: Extracted invoice number
            - invoice_date: Extracted date
            - total_amount: Extracted total
            - currency: Detected/provided currency
            - line_items: List of line items
            - processing_metadata: Additional info about processing
            
    Example:
        >>> result = process_invoice({
        ...     "document_text": "INVOICE #123\\nVendor: Acme Corp\\nTotal: $500",
        ...     "currency_hint": "USD"
        ... })
        >>> print(result["vendor"])
        "Acme Corp"
    """
    # =========================================================================
    # Pre-processing
    # =========================================================================
    
    # Validate required fields
    if "document_text" not in payload:
        return {
            "error": "Missing required field: document_text",
            "success": False
        }
    
    document_text = payload.get("document_text", "")
    
    # Clean up the document text
    cleaned_text = document_text.strip()
    if not cleaned_text:
        return {
            "error": "document_text cannot be empty",
            "success": False
        }
    
    # Extract optional hints
    currency_hint = payload.get("currency_hint")
    vendor_hint = payload.get("vendor_hint")
    user_id = payload.get("user_id")
    
    # =========================================================================
    # Agent Invocation
    # =========================================================================
    
    # Build the agent input
    agent_input = {
        "document_text": cleaned_text,
    }
    if currency_hint:
        agent_input["currency_hint"] = currency_hint
    if vendor_hint:
        agent_input["vendor_hint"] = vendor_hint
    
    # Get the cached agent and invoke
    agent = get_agent()
    result = agent.invoke(agent_input)
    
    # =========================================================================
    # Post-processing
    # =========================================================================
    
    # Add processing metadata
    result["processing_metadata"] = {
        "user_id": user_id,
        "document_length": len(cleaned_text),
        "hints_provided": {
            "currency": currency_hint is not None,
            "vendor": vendor_hint is not None
        }
    }
    
    # Mark as successful
    result["success"] = True
    
    return result


async def process_invoice_async(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Async version of process_invoice.
    
    Demonstrates that handlers can be async functions.
    Dockrion's HandlerAdapter automatically handles async functions.
    
    Args:
        payload: Same as process_invoice
        
    Returns:
        Same as process_invoice
    """
    # For this example, we just call the sync version
    # In a real async handler, you might do async I/O here
    return process_invoice(payload)

