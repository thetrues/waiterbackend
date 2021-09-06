from dateutil import parser


def get_date_objects(date1, date2):
    """Converts dates strings to dates objects"""

    return parser.parse(date1).date(), parser.parse(date2).date()


def validate_dates(date1, date2):
    """Validation: Check if the from_date is less than or equal to the to_date otherwise rise an error"""
    if date1 > date2:
        return True


def orders_number_generator(sender, field_name) -> int:
    """
        This is the generic function that generates the next number\
        from the previous object by incrementing the\
        last object's number by one: If there is no object it returns 100
    """

    try:
        object = sender.objects.first()
        if field_name == "customer_orders_number":
            number: int = int(object.customer_orders_number) + 1
        elif field_name == "order_number":
            number: int = int(object.order_number) + 1
        elif field_name == "dish_number":
            number: int = int(object.dish_number) + 1
    except:
        number: int = 100

    return number
