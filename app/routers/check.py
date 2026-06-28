import time
from fastapi import APIRouter, Response
from app.schemas import CheckRequest, CheckResponse
from app.limiter import check_rate_limit, get_client_config
from fastapi.responses import JSONResponse
from app.config import settings

router = APIRouter()

@router.post("/check", response_model=CheckResponse)
async def check(request: CheckRequest, response: Response):

    try:
        allowed, remaining = await check_rate_limit(request.client_key)
        config = await get_client_config(request.client_key)

        reset_time = int(time.time() + (1.0/config["refill_rate"]))

        response.headers["X-RateLimit-Limit"] = str(config["max_tokens"])
        response.headers["X-RateLimit-Remaining"] = str(int(remaining))
        response.headers["X-RateLimit-Reset"] = str(reset_time)

        return CheckResponse(
            allowed= allowed,
            tokens_remaining=remaining,
            client_key=request.client_key,
        )

    except Exception as e:
        return JSONResponse(status_code=503, content={"erorr" : "service unavailable", 
                                                    "detail" : str(e)})