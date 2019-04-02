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

delete from crawldb.link l where
l.from_page IN (select p1.id
				from crawldb.page p1, crawldb.site s1
				where s1.id=p1.site_id and not (s1.domain like '%e-prostor%' or s1.domain like '%evem%'))
OR l.to_page IN (select p2.id
				from crawldb.page p2, crawldb.site s2
				where s2.id=p2.site_id and not (s2.domain like '%e-prostor%' or s2.domain like '%evem%'))

delete from crawldb.page p where
p.id in (select p1.id
	   from crawldb.page p1, crawldb.site s1
		 where p1.site_id=s1.id and not (s1.domain like '%e-prostor%' or s1.domain like '%evem%'))

delete from crawldb.site where not (domain like '%e-prostor%' or domain like '%evem%')

										 select * from crawldb.site

						select * from crawldb.page
