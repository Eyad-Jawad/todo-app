from fastapi import APIRouter, Depends, HTTPException, status

from todo_app import auth
from todo_app.services.utils import Creditential, Token, rate_limiter

REQUESTS_LIMIT = 10
REQUESTS_LIMIT_TIME = 60 * 5
router = APIRouter()


@router.post(
    "/auth/sign_up",
    dependencies=[Depends(rate_limiter(REQUESTS_LIMIT, REQUESTS_LIMIT_TIME))],
)
async def sign_up(cred: Creditential):
    return await auth.sign_up(cred.username, cred.password)


@router.post(
    "/auth/log_in",
    dependencies=[Depends(rate_limiter(REQUESTS_LIMIT, REQUESTS_LIMIT_TIME))],
)
async def log_in(cred: Creditential):
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
    return await auth.delete_account(cred.username, cred.password)
