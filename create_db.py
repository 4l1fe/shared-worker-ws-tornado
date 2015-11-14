import psycopg2


db_settings = {'dbname': 'postgres', 'host': '127.0.0.1', 'user': 'postgres', 'password': 'postgres'}
dsn = 'dbname={dbname} host={host} user={user} password={password}'.format(**db_settings)


def main(dsn):
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    cur.execute("""DROP TABLE IF EXISTS pool_test;
                   CREATE TABLE pool_test (
                          id serial primary key,
                          name varchar);""")
    conn.commit()


if __name__ == '__main__':
    main(dsn)