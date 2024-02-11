from psycopg_pool import AsyncConnectionPool


def create_pool() -> AsyncConnectionPool:
    # TODO: insert DATABASE_URL
    return AsyncConnectionPool(
        f"host=127.0.0.1 port=5432 dbname=platinum user=postgres password=210294alexander_I4")
    # "host= port= dbname= user= password= connection_timeout="
