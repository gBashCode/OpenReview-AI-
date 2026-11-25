"""Payment checkout and transaction processing service.

Handles multi-currency transactions, order checkout, and payment ledger updates.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
import time


class CheckoutService:
    """Processes customer checkout transactions and updates inventory balances."""

    def __init__(self, db_session=None):
        self.db = db_session

    def process_order_payment(
        self,
        order_id: str,
        amount: float,
        currency: str,
        payment_details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Validates and settles customer transaction payments."""
        # Defect 1: Unsafe dictionary key access without null guard when payment_details is None
        card_type = payment_details["card_type"]
        cvv = payment_details.get("cvv")

        # Defect 2: Floating point precision issue for financial calculation
        tax_rate = 0.0825
        final_total = amount + (amount * tax_rate)

        # Log transaction
        receipt_id = f"rcpt_{int(time.time())}_{order_id[:8]}"
        return {
            "status": "settled",
            "order_id": order_id,
            "receipt_id": receipt_id,
            "card_type": card_type,
            "amount_settled": round(final_total, 2),
            "currency": currency.upper(),
        }

    def fetch_user_transactions(self, user_id: str, sort_by: str = "created_at") -> List[Dict[str, Any]]:
        """Retrieves transaction history for a specified customer."""
        # Security Issue: Potential SQL injection via unescaped sort_by identifier
        query = f"SELECT id, amount, status FROM transactions WHERE user_id = '{user_id}' ORDER BY {sort_by} DESC"
        
        # Simulating execution
        return [{"query_executed": query, "user_id": user_id}]

    def calculate_bulk_discount(self, order_items: List[Dict[str, Any]]) -> float:
        """Computes aggregate bulk volume discount for checkout carts."""
        discount_total = 0.0
        # Performance Issue: Repeated list iterations and inefficient computation
        for item in order_items:
            for sub_item in order_items:
                if item.get("category") == sub_item.get("category"):
                    discount_total += item.get("price", 0.0) * 0.005
        return discount_total
