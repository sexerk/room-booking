from fastapi import HTTPException, status

class BookingConflictError(HTTPException):
    def __init__(self, detail: str = "Booking conflict"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)

class RoomNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

class UserNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

class BookingNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

class InvalidBookingDatesError(HTTPException):
    def __init__(self, detail: str = "Invalid booking dates"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

class BookingCancellationError(HTTPException):
    def __init__(self, detail: str = "Cannot cancel booking"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

class AuthenticationError(HTTPException):
    def __init__(self, detail: str = "Could not authenticate"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

class PermissionDeniedError(HTTPException):
    def __init__(self, detail: str = "Not enough permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )