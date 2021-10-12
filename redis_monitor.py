from redis import Redis

redis_host = "localhost"
redis_port = 6380


if __name__ == "__main__":
    r = Redis(
        host=redis_host,
        port=redis_port,
    )
    with r.monitor() as m:
        for command in m.listen():
            print(command)
