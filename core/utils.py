from dateutil import parser


def get_date_objects(date1, date2):
    """Converts dates strings to dates objects"""

    return parser.parse(date1).date(), parser.parse(date2).date()


def validate_dates(date1, date2):
    """Validation: Check if the from_date is less than or equal to the to_date otherwise rise an error"""
    if date1 > date2:
        return True
