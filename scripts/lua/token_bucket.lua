local tokens_key      = KEYS[1]
local last_refill_key = KEYS[2]
local now             = tonumber(ARGV[1])
local max_tokens      = tonumber(ARGV[2])
local refill_rate     = tonumber(ARGV[3])

local tokens      = tonumber(redis.call("GET", tokens_key))
local last_refill = tonumber(redis.call("GET", last_refill_key))

if tokens == nil then
    tokens = max_tokens
end
if last_refill == nil then
    last_refill = now
end

local elapsed = now - last_refill
tokens = math.min(max_tokens, tokens + (elapsed * refill_rate))

local allowed = 0
if tokens >= 1.0 then
    tokens  = tokens - 1.0
    allowed = 1
end

redis.call("SET", tokens_key,      tokens)
redis.call("SET", last_refill_key, now)

-- Time required to completely refill the bucket
local ttl = math.call(max_tokens/refill_rate) * 3

redis.call("EXPIRE", tokens_key, ttl)
redis.call("EXPIRE", last_refill_key, ttl)

return { allowed, tostring(tokens) }