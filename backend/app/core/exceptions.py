"""Custom HTTP exceptions for ClassPulse.

FastAPI converts HTTPException into a JSON response automatically:
  { "detail": "<message>" }  with the appropriate HTTP status code.
"""

from fastapi import HTTPException, status


class NotFoundError(HTTPException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND,
                         detail=f"{resource} not found.")


class ForbiddenError(HTTPException):
    def __init__(self, msg: str = "You do not have permission to perform this action."):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=msg)


class UnauthorizedError(HTTPException):
    def __init__(self, msg: str = "Authentication required."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ConflictError(HTTPException):
    def __init__(self, msg: str = "Resource already exists."):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=msg)


class BadRequestError(HTTPException):
    def __init__(self, msg: str = "Bad request."):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
