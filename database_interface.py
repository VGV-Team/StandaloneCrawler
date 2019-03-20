from configparser import ConfigParser
import psycopg2
import threading

import constants


class DatabaseInterface:

    config = None
    database_lock = None

    def __init__(self, database_lock, config_path='database/database.ini'):
        self.config = self.read_config(filename=config_path)
        self.database_lock = database_lock

    def read_config(self, filename='database/database.ini', section='postgresql'):
        # create a parser
        parser = ConfigParser()
        # read config file
        parser.read(filename)
        # get section, default to postgresql
        config = {}
        if parser.has_section(section):
            params = parser.items(section)
            for param in params:
                config[param[0]] = param[1]
        else:
            raise Exception('Section {0} not found in the {1} file'.format(section, filename))
        return config

    def execute_select_sql(self, sql, values):
        conn = None
        rows = list()
        try:
            # connect to the PostgreSQL database
            conn = psycopg2.connect(**self.config)
            # create a new cursor
            cur = conn.cursor()
            # execute the SELECT statement
            cur.execute(sql, values)
            # fetch results
            rows = cur.fetchall()
            # close communication with the database
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()
        return rows

    def execute_update_sql(self, sql, values):
        conn = None
        updated_rows = 0
        try:
            # connect to the PostgreSQL database
            conn = psycopg2.connect(**self.config)
            # create a new cursor
            cur = conn.cursor()
            # execute the UPDATE statement
            cur.execute(sql, values)
            # get the number of updated rows
            updated_rows = cur.rowcount
            # commit the changes to the database
            conn.commit()
            # close communication with the database
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()
        return updated_rows

    def execute_insert_sql(self, sql, values, fetch_id=True):
        conn = None
        id = None
        try:
            # connect to the PostgreSQL database
            conn = psycopg2.connect(**self.config)
            # create a new cursor
            cur = conn.cursor()
            # execute the INSERT statement
            cur.execute(sql, values)
            if fetch_id:
                # get the generated id back
                id = cur.fetchone()[0]
            # commit the changes to the database
            conn.commit()
            # close communication with the database
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()
        return id

    def delete_all_data(self):
        with self.database_lock:
            sql = """TRUNCATE crawldb.site, crawldb.page, crawldb.link, crawldb.image, crawldb.page_data"""
            conn = None
            try:
                # connect to the PostgreSQL database
                conn = psycopg2.connect(**self.config)
                # create a new cursor
                cur = conn.cursor()
                # execute the TRUNCATE statement
                cur.execute(sql, ())
                # commit the changes to the database
                conn.commit()
                # close communication with the database
                cur.close()
            except (Exception, psycopg2.DatabaseError) as error:
                print(error)
            finally:
                if conn is not None:
                    conn.close()

    def find_site(self, domain):
        with self.database_lock:
            sql = """select id, domain, robots_content from crawldb.site WHERE domain = %s;"""
            result = self.execute_select_sql(sql, [domain])
            return result

    def get_all_sites(self):
        with self.database_lock:
            sql = """select id, domain from crawldb.site;"""
            return self.execute_select_sql(sql, ())

    def get_all_pages(self):
        with self.database_lock:
            sql = """select id, site_id, url from crawldb.page;"""
            return self.execute_select_sql(sql, ())

    def get_all_page_hashes(self):
        with self.database_lock:
            sql = """select id, site_id, hash from crawldb.page where hash is not null;"""
            return self.execute_select_sql(sql, ())

    def get_next_N_frontier(self, N):
        with self.database_lock:
            sql = """select id, site_id, url from crawldb.page WHERE page_type_code=%s AND processing is null ORDER BY accessed_time LIMIT %s;"""
            results = self.execute_select_sql(sql, (constants.PAGE_TYPE_CODE_FRONTIER, N))
            for res in results:
                sql = """UPDATE crawldb.page SET processing = TRUE WHERE id = %s;"""
                self.execute_update_sql(sql, [res[0]])
            return results

    def get_duplicated_pages(self, url1, url2):
        with self.database_lock:
            sql = """select id from crawldb.page WHERE url=%s OR url=%s;"""
            return self.execute_select_sql(sql, (url1, url2))
    
    def add_site(self, domain, robots_content, sitemap_content):
        with self.database_lock:
            sql = """INSERT INTO crawldb.site(domain, robots_content, sitemap_content) VALUES(%s, %s, %s) RETURNING id;"""
            return self.execute_insert_sql(sql, (domain, robots_content, sitemap_content))

    def add_page(self, site_id, url, accessed_time, from_id):
        with self.database_lock:
            sql = """select id from crawldb.page WHERE url=%s;"""
            id = self.execute_select_sql(sql, [url])

            if len(id) == 0:
                sql = """INSERT INTO crawldb.page(site_id, page_type_code, url, accessed_time) 
                            VALUES(%s, %s, %s, to_timestamp(%s)) RETURNING id;"""
                id = self.execute_insert_sql(sql, (site_id, constants.PAGE_TYPE_CODE_FRONTIER, url, accessed_time))
            else:
                id = id[0][0]

            if from_id is None:
                self.add_link(id, id, True)
            else:
                self.add_link(from_id, id, True)
            return id

    def update_page(self, id, page_type_code, html_content, http_status_code, hash):
        with self.database_lock:
            sql = """UPDATE crawldb.page SET page_type_code = %s, html_content = %s, 
                        http_status_code = %s, hash = %s WHERE id = %s;"""
            self.execute_update_sql(sql, (page_type_code, html_content, http_status_code, hash, id))

    def update_page_to_binary(self, id, http_status_code):
        self.update_page(id, constants.PAGE_TYPE_CODE_BINARY, constants.DATABASE_NULL, http_status_code, None)

    def update_page_to_html(self, id, html_content, http_status_code, hash):
        self.update_page(id, constants.PAGE_TYPE_CODE_HTML, html_content, http_status_code, hash)

    def update_page_to_duplicate(self, id, http_status_code, hash):
        self.update_page(id, constants.PAGE_TYPE_CODE_DUPLICATE, constants.DATABASE_NULL, http_status_code, hash)

    def add_image(self, page_id, filename, content_type, data, accessed_time):
        with self.database_lock:
            sql = """INSERT INTO crawldb.image(page_id, filename, content_type, data, accessed_time) 
                    VALUES(%s, %s, %s, %s, to_timestamp(%s)) RETURNING id;"""
            return self.execute_insert_sql(sql, (page_id, filename, content_type, data, accessed_time))

    def add_page_data(self, page_id, data_type_code, data):
        with self.database_lock:
            sql = """INSERT INTO crawldb.page_data(page_id, data_type_code, data) VALUES(%s, %s, %s) RETURNING id;"""
            return self.execute_insert_sql(sql, (page_id, data_type_code, data))

    def add_link(self, site_id_from, site_id_to, ignore_db_lock=False):
        if ignore_db_lock:
            sql = """INSERT INTO crawldb.link(from_page, to_page) VALUES(%s, %s);"""
            self.execute_insert_sql(sql, (site_id_from, site_id_to), False)
        else:
            with self.database_lock:
                sql = """INSERT INTO crawldb.link(from_page, to_page) VALUES(%s, %s);"""
                self.execute_insert_sql(sql, (site_id_from, site_id_to), False)
