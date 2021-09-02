from django.db.models import Manager
from typing import List, Dict


class RestaurantPayrolCustomManager(Manager):
    """Custom Manager for Restaurant Payrols"""

    def get_monthly_payments(self, queryset) -> List[Dict]:
        response: List[Dict] = []

        return [
            response.append(
                {
                    "id": q.id,
                    "payee": q.restaurant_payee.username,
                    "amount": q.amount_paid,
                }
            )
            for q in queryset
        ]
