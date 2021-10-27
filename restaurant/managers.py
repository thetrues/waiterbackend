from django.db.models import Manager
from typing import List, Dict


class RestaurantPayrolCustomManager(Manager):
    """Custom Manager for Restaurant Payrols"""

    def get_monthly_payments(self, queryset) -> List[Dict]:
        response: List[Dict] = []

        for q in queryset:
            response.append(
                {
                    "id": q.id,
                    "payee": q.name,
                    "amount": q.amount_paid,
                }
            )

        return response
