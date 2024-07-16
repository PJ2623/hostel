from redis.asyncio import Redis


"""
    ## Initialize Redis connection
    
    Redis is used as the in-memory cache for the application.
    It is used to store the data that is frequently accessed by the users and the application.
"""
redis = Redis(host='localhost', port=6379, db=0, decode_responses=True)
