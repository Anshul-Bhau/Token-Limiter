local key        = KEYS[1]
local now        = tonumber(ARGV[1])
local window     = tonumber(ARGV[2])
local max_req    = tonumber(ARGV[3])
local request_id = ARGV[4]

-- Delete everything older than now - window size 
redis.call("ZREMRANGEBYSCORE", key, 0, now - window)

-- Count how may requests remians in the active window
local count = redis.call("ZCARD", key)

if count < max_req then
    -- record current request
    redis.call("ZADD", key, now, request_id)
    -- garbage collection
    redis.call("EXPIRE", key, window * 2)
    return { 1, tostring(max_req - count - 1) }
else
    return { 0, "0" }
end