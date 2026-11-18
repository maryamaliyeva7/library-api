class LibraryError(Exception):
    def __init__(self, message, status):
        self.message = message
        self.status = status


def bad_request(message):
    return LibraryError(message, 400)


def not_found(message):
    return LibraryError(message, 404)


def conflict(message):
    return LibraryError(message, 409)