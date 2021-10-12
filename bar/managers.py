from django.db.models import Manager
from typing import List, Dict


class BarPayrolCustomManager(Manager):
    """Custom Manager for Bar Payrolls"""

    def get_monthly_payments(self, queryset) -> List[Dict]:
        response: List[Dict] = []

        for q in queryset:
            response.append(
                {
                    "id": q.id,
                    "payee": q.bar_payee.username,
                    "amount": q.amount_paid,
                }
            )

        return response
