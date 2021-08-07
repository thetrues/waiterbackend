from user.models import User
from typing import List


def get_recipients():
    response: List[str] = []
    qs = User.objects.filter(user_type="manager")
    [response.append(user.mobile_phone) for user in qs]

    return response
