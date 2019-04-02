# StandaloneCrawler

## Database preparation

### Installation

- [Download Postgres](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads)
- Use 'root' as password
- Complete installation
- Run pgAdmin4
- Select 'postgres' database > Tools > Query tools > Open file > Open 'database/database_init.sql'
- Execute query
- Check if schema exists: Databases > postgres > Schemas > crawldb

### Test

- Run 'test_database.py' in database folder
- Go to pgadmin4 and execute query
```
SELECT * FROM crawldb.site
```


## Required packages

- Selenium
```
pip install selenium
```
- BeautifulSoup
```
pip install bs4
```
- Psycopg2
```
pip install psycopg2
```
- lxml
```
pip install lxml
```

## How to run

- Implementation in /crawler
- Set up desired parameters in constants.py and crawler.py (and database.ini for custom database properties)
- For first time you should run the crawler with FRESH_START set to True
- You can start the crawler by running crawler.py

## Remarks
- [Other database backups](https://drive.google.com/open?id=1KnOVGFBAQ7l3gfGNgCxUExbxB_w-fSwc)