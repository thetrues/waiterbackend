# from restaurant.models import RestaurantPayrol
import restaurant
from django.db.models.aggregates import Sum
from django.db.models import Manager
from django.conf import settings
from typing import List, Dict


RestaurantPayrol = settings.RESTAURANT_PAYROL

RestaurantPayrol = getattr(restaurant.models, RestaurantPayrol)


class RestaurantPayrolCustomManager(Manager):
    """Custom Manager for Restaurant Payrols"""

    def get_monthly_payments(self, queryset) -> List[Dict]:
        response: List[Dict] = []

        for q in queryset:
            response.append(
                {
                    "id": q.id,
                    "payee": q.restaurant_payee.username,
                    "amount": q.amount_paid,
                }
            )

        return response

    def get_total(self, this_month) -> float:
        return RestaurantPayrol.objects.filter(
            date_paid__month=this_month.month, date_paid__year=this_month.year
        ).aggregate(total=Sum("amount_paid"))["total"]
