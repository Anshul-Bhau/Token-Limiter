local tokens_key      = KEYS[1]
local last_refill_key = KEYS[2]
local now             = tonumber(ARGV[1])
local max_tokens      = tonumber(ARGV[2])
local refill_rate     = tonumber(ARGV[3])

local tokens      = tonumber(redis.call("GET", tokens_key))
local last_refill = tonumber(redis.call("GET", last_refill_key))

if not tokens then
    tokens = max_tokens
end
if not last_refill then
    last_refill = now
end

local elapsed = now - last_refill
tokens = math.min(max_tokens, tokens + (elapsed * refill_rate))

local allowed = 0
if tokens >= 1.0 then
    tokens  = tokens - 1.0
    allowed = 1
end

redis.call("SET", tokens_key,      tostring(tokens))
redis.call("SET", last_refill_key, tostring(now))

return { allowed, tostring(tokens) }