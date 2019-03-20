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
