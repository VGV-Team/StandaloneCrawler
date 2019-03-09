from configparser import ConfigParser
import psycopg2

import constants as constants


class DatabaseInterface:

    config = None

    def __init__(self, config_path='database/database.ini'):
        self.config = self.read_config(filename=config_path)

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

    def execute_insert_sql(self, sql, values):
        conn = None
        id = None
        try:
            # connect to the PostgreSQL database
            conn = psycopg2.connect(**self.config)
            # create a new cursor
            cur = conn.cursor()
            # execute the INSERT statement
            cur.execute(sql, values)
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

    def get_all_domains(self):
        sql = """select id, domain from crawldb.site;"""
        return self.execute_select_sql(sql, ())

    def get_all_pages(self):
        sql = """select id, site_id, url from crawldb.page;"""
        return self.execute_select_sql(sql, ())

    def add_domain(self, domain, robots_content, sitemap_content):
        sql = """INSERT INTO crawldb.site(domain, robots_content, sitemap_content) VALUES(%s, %s, %s) RETURNING id;"""
        return self.execute_insert_sql(sql, (domain, robots_content, sitemap_content))

    def add_page(self, site_id, url, accessed_time):
        sql = """INSERT INTO crawldb.page(site_id, page_type_code, url, accessed_time) 
                    VALUES(%s, %s, %s, to_timestamp(%s)) RETURNING id;"""
        return self.execute_insert_sql(sql, (site_id, constants.PAGE_TYPE_CODE_FRONTIER, url, accessed_time))

    def update_page(self, id, page_type_code, html_content, http_status_code):
        sql = """UPDATE crawldb.page SET page_type_code = %s, html_content = %s, http_status_code = %s WHERE id = %s;"""
        self.execute_update_sql(sql, (page_type_code, html_content, http_status_code, id))

    def update_page_to_binary(self, id, http_status_code):
        self.update_page(id, constants.PAGE_TYPE_CODE_BINARY, constants.DATABASE_NULL, http_status_code)

    def update_page_to_html(self, id, http_status_code):
        self.update_page(id, constants.PAGE_TYPE_CODE_HTML, constants.DATABASE_NULL, http_status_code)

    def update_page_to_duplicate(self, id, http_status_code, duplicate_id):
        self.update_page(id, constants.PAGE_TYPE_CODE_DUPLICATE, constants.DATABASE_NULL, http_status_code)
        self.add_link(id, duplicate_id)

    def add_image(self, page_id, filename, content_type, data, accessed_time):
        sql = """INSERT INTO crawldb.image(page_id, filename, content_type, data, accessed_time) 
                    VALUES(%s, %s, %s, %s, %s) RETURNING id;"""
        return self.execute_insert_sql(sql, (page_id, filename, content_type, data, accessed_time))

    def add_page_data(self, page_id, data_type_code, data):
        sql = """INSERT INTO crawldb.page_data(page_id, data_type_code, data) VALUES(%s, %s, %s) RETURNING id;"""
        return self.execute_insert_sql(sql, (page_id, data_type_code, data))

    def add_link(self, site_id_from, site_id_to):
        sql = """INSERT INTO crawldb.link(from_page, to_page) VALUES(%s, %s) RETURNING id;"""
        return self.execute_insert_sql(sql, (site_id_from, site_id_to))

# todo: add additional attribute hash to page table
