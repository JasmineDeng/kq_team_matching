import datetime

DATETIME_FORMAT = "%Y-%m-%d_%H-%M-%S"


class ParseableDatetime:
    def __init__(self, datetime_obj: datetime.datetime):
        self._datetime_obj = datetime_obj

    @property
    def datetime_obj(self):
        return self._datetime_obj

    def serialize(self):
        return self._datetime_obj.strftime(DATETIME_FORMAT)

    @classmethod
    def deserialize(cls, date_str: str):
        try:
            datetime_obj = datetime.datetime.strptime(date_str, DATETIME_FORMAT)
            return cls(datetime_obj)
        except ValueError:
            raise ValueError(f"Invalid date string format: {date_str}. Expected format is {DATETIME_FORMAT}.")
