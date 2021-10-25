from user.models import User
from typing import List


def get_recipients():
    response: List[str] = []
    qs = User.objects.filter(user_type="manager")
    [response.append(user.mobile_phone) for user in qs]

    return response


def send_notification(message: str, recipients: List[str]):
    from BeemAfrica import Authorize, SMS
    import requests
    import json

    api_key = "945c064a2f78eaea"
    secret_key = "YmU3ZDJlNzVhMGE3MTE3NDQ3NTJhNTQwN2ZkNWFkMDFiNWQ0ZmRjYjk4ZWU3YjE4MTBmYjdmYjlhYjE0NDdiYw=="

    Authorize(api_key, secret_key)

    try:
        SMS.send_sms(message, recipients)
    except Exception as e:
        error_name: str = str(e)
        return requests.models.Response(
            json.dumps(error_name),
            status=500,
        )
