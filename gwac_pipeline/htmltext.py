# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup

#url='http://www.astronomy.ohio-state.edu/~assassin/transients.html'
#session=requests.Session()
#r = session.get(url, timeout=20, verify=False)

content_file=open('aa.txt', 'r')
content = content_file.read()
content_file.close()
pageContent = BeautifulSoup(content, 'html.parser')
trs = pageContent.findAll('tr')
print(len(trs))

tstrs=""
for tr in trs:
    td = tr.findAll("td")
    if len(td)==12:
        name=td[0].contents[0]
        ra=td[3].contents[0]
        dec=td[4].contents[0]
        comm=td[11].contents[0]
        #print(comm)
        if comm.find('CV candidate')>-1:
            tstrs="%s%s\t@\t%s\t@\t%s\t@\t%s\n"%(tstrs,name,ra,dec,comm)

content_file=open('abc.txt', 'w')
content_file.write(tstrs)
content_file.close()