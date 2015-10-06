import requests, re, string
from csv import writer
from lxml import html
from lxml.cssselect import CSSSelector
from time import ctime, sleep

app_id = 1
genres = list()
subgenres = list()
letters = list(string.ascii_uppercase) + ["*"]

class Genre(object):
	"""Container for genre object"""


	def __init__(self, genre_id, genre_name, genre_url, num_subgenres):
		"""Construct genre object using genre details"""
		
		self.genre_id = genre_id
		self.genre_name = genre_name
		self.genre_url = genre_url
		self.num_subgenres = num_subgenres


	def get_genre(self):
		"""Return genre attributes in list format for saving in CSV"""

		return [self.genre_id, self.genre_name, self.genre_url, self.num_subgenres]




class Subgenre(object):
	"""Container for subgenre object"""


	def __init__(self, subgenre_id, subgenre_name, subgenre_url, genre_id):
		"""Construct subgenre object using subgenre details"""
		
		self.subgenre_id = subgenre_id
		self.subgenre_name = subgenre_name
		self.subgenre_url = subgenre_url
		self.genre_id = genre_id


	def get_subgenre(self):
		"""Return subgenre attributes in list format for saving in CSV"""

		return [self.subgenre_id, self.subgenre_name, self.subgenre_url, self.genre_id]




class App(object):
	"""Container for app details"""


	def __init__(self, app_id, app_itunes_id, app_name, app_genre_id, app_subgenre_id, app_url):
		"""Construct app object using app details"""

		self.app_id = app_id
		self.app_itunes_id = app_itunes_id
		self.app_name = app_name
		self.app_genre_id = app_genre_id
		self.app_subgenre_id = app_subgenre_id
		self.app_url = app_url


	def get_app(self):
		"""Return app attributes in list format for saving in CSV"""

		return [self.app_id, self.app_itunes_id, self.app_name, self.app_genre_id, self.app_subgenre_id, self.app_url]




class Page(object):
	"""Container for page details"""


	def __init__(self, url):
		"""Construct object using _url_ of page"""

		self.url = url
		connected = False
		while not connected:
			try:
				self.text = requests.get(self.url).text
				connected = True
			except:
				sleep(30)
				pass
		self.dom = html.fromstring(self.text, parser=html.HTMLParser(encoding='utf-8'))




def extract_genres(seed_url):
	"""Extract genres and subgenres from iTunes main page"""

	global genres
	global subgenres

	g_id = 1
	s_id = 1
	
	store = Page(seed_url)
	a_tags = CSSSelector("a")
	store_atags = [e for e in a_tags(store.dom) if e.get("class")=="top-level-genre"]
	
	for a in store_atags:
		g_name, g_url, num_subgenres = a.text, a.get("href"), 0
		if a.getnext()!=None:
			subgenre_atags = [li.getchildren()[0] for li in a.getnext().getchildren()]
			for s in subgenre_atags:
				s_name = s.text
				s_url = s.get("href")
				subgenres.append(Subgenre(s_id, s_name, s_url, g_id))
				s_id += 1
				num_subgenres += 1
		genres.append(Genre(g_id, g_name, g_url, num_subgenres))
		g_id += 1

	with open("Genres.csv", 'w') as g:
		gWrite =writer(g)
		gWrite.writerow(["genre_id", "genre_name", "genre_url", "num_subgenres"])
		gWrite.writerows([i.get_genre() for i in genres])

	with open("Subgenres.csv", 'w') as s:
		sWrite =writer(s)
		sWrite.writerow(["subgenre_id", "subgenre_name", "subgenre_url", "genre_id"])
		sWrite.writerows([i.get_subgenre() for i in subgenres])




def extract_apps(genre_id, url, appwriter, logfile, subgenre_id=0):
	"""Extract app details by going genre, subgenre, letter, and page number"""

	global letters
	global app_id

	divs = CSSSelector("div")

	#Logging
	print app_id, ctime(), genre_id, subgenre_id
	logfile.write(str(ctime()) + ", app_id: " + str(app_id) + ", genre_id: " + str(genre_id) + ", subgenre_id: " + str(subgenre_id) + "\n")
	
	for l in letters:

		current_page = 1
		prev_page_app = None

		while True:
			pagenum_url = url + "&letter=" + l + "&page=" + str(current_page) + "#page"
			pagenum_page = Page(pagenum_url)

			appdivs = [e for e in divs(pagenum_page.dom) if e.getparent().get("id")=="selectedcontent"]

			try:
				first_app = appdivs[0].getchildren()[0].getchildren()[0].getchildren()[0].text
				if prev_page_app == first_app:
					break
				prev_page_app = first_app
			except:
				break

			for d in appdivs:
				for ul in d.getchildren():
					for li in ul.getchildren():
						for a in li.getchildren():
							#There is only one element in d, ul, li, thus these are effectively 2 for loops
							app_name = a.text.encode("utf-8")
							app_url = a.get("href")
							app_itunes_id = re.findall(r"/id.*\?mt", app_url)[0][3:-3]
							app_details = App(app_id, app_itunes_id, app_name, genre_id, subgenre_id, app_url)
							appwriter.writerow(app_details.get_app())
							app_id += 1

			current_page += 1



def main():

	global genres
	global subgenres
	
	itunes_seed_url = "https://itunes.apple.com/us/genre/ios/id36"
	extract_genres(itunes_seed_url)

	appfile = open("Apps.csv", 'w')
	appwriter = writer(appfile)
	appwriter.writerow(["app_id", "app_itunes_id", "app_name", "app_genre_id", "app_subgenre_id", "app_url"])
	

	logfile = open("Log.txt", 'w') 

	for g in genres:
		if g.num_subgenres==0:
			extract_apps(g.genre_id, g.genre_url, appwriter, logfile)

	for s in subgenres:
		extract_apps(s.genre_id, s.subgenre_url, appwriter, logfile, s.subgenre_id)

	appfile.close()
	logfile.close()

if __name__=="__main__":
	main()