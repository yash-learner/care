class BaseFHIRException(Exception):
    pass


class MoreThanOneFHIRResourceFound(BaseFHIRException):
    pass
