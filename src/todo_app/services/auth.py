from fastapi import Depends, HTTPException, status, APIRouter

from todo_app import auth
from todo_app.services.utils import Creditential, Token, rate_limiter

REQUESTS_LIMIT = 10
REQUESTS_LIMIT_TIME = 60 * 5
router = APIRouter()


def is_len_right(cred: Creditential) -> bool:
    if not (len(cred.username) <= 16 and len(cred.username) >= 2):
        raise HTTPException(
            status_code=status.HTTP_411_LENGTH_REQUIRED,
            detail="A username must be longer than 2 characters and shorter than 16 characters.",
        )

    if not (len(cred.password) <= 36 and len(cred.password) >= 8):
        raise HTTPException(
            status_code=status.HTTP_411_LENGTH_REQUIRED,
            detail="A password must be longer than 8 characters and shorter than 36 characters.",
        )

    return True


@router.post(
    "/auth/sign_up",
    dependencies=[Depends(rate_limiter(REQUESTS_LIMIT, REQUESTS_LIMIT_TIME))],
)
async def sign_up(cred: Creditential):
    is_len_right(cred)

    return await auth.sign_up(cred.username, cred.password)


@router.post(
    "/auth/login",
    dependencies=[Depends(rate_limiter(REQUESTS_LIMIT, REQUESTS_LIMIT_TIME))],
)
async def login(cred: Creditential):
    is_len_right(cred)

    return await auth.login(cred.username, cred.password)


@router.post(
    "/auth/log_out",
    dependencies=[Depends(rate_limiter(REQUESTS_LIMIT, REQUESTS_LIMIT_TIME))],
)
async def log_out(token: Token):
    if len(token.access_token) != 36:  # uuid4 is 36 chars long
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Access token doens't exist.",
        )

    return await auth.log_out(token.access_token)


@router.delete(
    "/auth/delete_account",
    dependencies=[Depends(rate_limiter(REQUESTS_LIMIT, REQUESTS_LIMIT_TIME))],
)
async def delete_account(cred: Creditential):
    is_len_right(cred)

    return await auth.delete_account(cred.username, cred.password)
