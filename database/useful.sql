select count(*), page.site_id from crawldb.page where page_type_code='HTML' GROUP BY page.site_id

select count(*) from crawldb.page where page_type_code='HTML'

select * from crawldb.site

select count(*), page.site_id from crawldb.page where page_type_code='DUPLICATE' GROUP BY page.site_id

select count(*) from crawldb.page where page_type_code='DUPLICATE'

select count(*), p.site_id from crawldb.image i, crawldb.page p where p.id=i.page_id group by p.site_id

select count(*) from crawldb.image

select count(*), p.site_id from crawldb.page_data pd, crawldb.page p where p.id=pd.page_id group by p.site_id

select count(*) from crawldb.page_data

select count(*), s.domain from crawldb.page p, crawldb.site s where s.id=p.site_id and page_type_code='HTML' group by s.domain
select count(*) from crawldb.page where page_type_code='HTML'

select count(*), s.domain from crawldb.page p, crawldb.site s where s.id=p.site_id and page_type_code='DUPLICATE' group by s.domain
select count(*) from crawldb.page where page_type_code='DUPLICATE'