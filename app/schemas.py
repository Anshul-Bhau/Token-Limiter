from pydantic import BaseModel

from typing import Literal
from pydantic import BaseModel, Field

class CheckRequest(BaseModel):
    client_key: str

class CheckResponse(BaseModel):
    allowed: bool
    tokens_remaining: float
    client_key: str

class AdminRequest(BaseModel):
    client_key: str

    max_tokens: int = Field(
        default=10,
        ge=1
    )

    refill_rate: float = Field(
        default=2.0,
        gt=0
    )

    window_size: int = Field(
        default=60,
        ge=1
    )
    
    algorithm: Literal[
        "token_bucket",
        "sliding_window"
    ] = "token_bucket"

class AdminResponse(BaseModel):
    status: str
    client_key: str