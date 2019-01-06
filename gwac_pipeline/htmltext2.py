# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup


url='http://vizier.u-strasbg.fr/viz-bin/VizieR-4?-ref=VIZ5bd5371da602&-out.add=_r&-out.add=_RAJ%2C_DEJ&-sort=_r&-order=I&-oc.form=sexa&-meta.foot=1&-meta=1&-meta.ucd=2&-c.geom=r&-c.eq=J2000&-c.u=arcmin&-c.r=+0.5&-c=128.42223%2C36.46916'
session=requests.Session()
r = session.get(url, timeout=20, verify=False)
content=r.text

'''
content_file=open('abc.txt', 'r')
content = content_file.read()
content_file.close()
'''
'''
content_file=open('abc.txt', 'w')
content_file.write(content)
content_file.close()
'''
pageContent = BeautifulSoup(content, 'html.parser')
tables = pageContent.findAll(attrs={'id' : "!ext-tsv/catClient.py_11"})
print("\n******************tables")
print(tables)

trs=tables[0].findAll("tr",attrs={'class' : "tuple-2"})
print("\n******************trs")
print(trs)
tds = trs[0].findAll('td')
print("\n******************tds")
print(tds)
print("\n******************td4")
td4=tds[4]
print(td4)
raj2000=td4.contents[0]
print("\n******************raj2000")
print(raj2000)

