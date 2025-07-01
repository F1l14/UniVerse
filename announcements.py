from bs4 import BeautifulSoup
import requests
import urllib3
requests.packages.urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

announcements_html = requests.get("https://www.ceid.upatras.gr", verify=False).text
soup = BeautifulSoup(announcements_html, 'lxml')


links = soup.select("h3.gdlr-core-blog-title a")

# Print out the href and text of each relevant link
for a in links:
    print(a.text+"\n")