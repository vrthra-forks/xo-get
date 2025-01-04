#! /usr/bin/env python

# script started by chris hager, olpc-austria
# project page: http://wiki.laptop.org/go/Xo-get
# license: gpl

import os
import sys
import urllib2
import sqlite3
import xml.dom.minidom

VERSION_NEWS = "  1. Repository: http://xo-get.olpc.at/repository\n  2. Database structure updated. :)"
	
class Activity:
	wiki_name = u""
	system_name = u""
	version = u""
	xo_url = u""
	category = u""
	description = u""
	tags = u""
	filesize = u""
	flag = u""
	image = u""
	mime = u""
	repo = 0
	
class Database:
	db_filename = "activities.db"	
	new_install = False
	new_update = False
	
	def __init__(self, db_path, version):
		self.db_path = db_path
		self.version = version

		self.db_fullfn = "%s/%s" % (self.db_path, self.db_filename)
		
		# Create .xo-get (db_path) Directory
		if os.path.isdir(self.db_path) == False: os.mkdir(self.db_path)
				
		# Check if Database Exits
		create_dbfile = True
		if os.path.isfile(self.db_fullfn): create_dbfile = False

		# Connect Database
		self.con = sqlite3.connect(self.db_fullfn)
		self.cur = self.con.cursor()
		self.cur.execute("-- types unicode")

		# Create Tables (if not exists)
		self.create_db()
		
		# Display Message on Creation if Database File
		if create_dbfile: print "  [%s]: created\n" % (self.db_fullfn),
		
		# Did we just have a version update?
		q = "SELECT count(*) FROM versions WHERE version='%s'" % version
		res = self.query(q)
		
		if res[0][0] == 0:
			# Version 0.5.0 Info & Display News
			self.commit("INSERT INTO versions (version, notes) VALUES ('%s', '%s')" % (version, VERSION_NEWS.replace("'", '"')))
			if create_dbfile == False: 
				# We had an Update
				self.new_update = True
			else:
				# We had a new Installation
				self.new_install = True
	
	def create_db(self):
		self.cur.execute("CREATE TABLE IF NOT EXISTS 'activities'    ('id' INTEGER PRIMARY KEY AUTOINCREMENT, 'wiki_name' VARCHAR( 200 ), 'system_name' VARCHAR( 100 ),'version' VARCHAR( 30 ), 'xo_url' VARCHAR( 1023 ), 'category' VARCHAR( 255 ), 'description' TEXT, 'tags' VARCHAR( 255 ), 'filesize' VARCHAR( 20 ), 'flag' VARCHAR( 10 ), 'image' VARCHAR( 255 ), 'mime' VARCHAR( 255 ), 'repo' INT);")
		self.cur.execute("CREATE TABLE IF NOT EXISTS 'history'       ('id' INTEGER PRIMARY KEY AUTOINCREMENT, 'date' date, 'time' time, 'text' VARCHAR( 200 ));")
		self.cur.execute("CREATE TABLE IF NOT EXISTS 'versions'      ('id' INTEGER PRIMARY KEY AUTOINCREMENT, 'version' VARCHAR( 10 ) NOT NULL, 'notes' VARCHAR( 355 ) NOT NULL);")
		self.con.commit()

		try: 
			r = self.query("SELECT count(*) FROM activities	WHERE wiki_name='pw'");
			if r[0][0] == 0: 
				self.cur.execute("INSERT INTO activities (wiki_name, system_name, description, xo_url, category, tags) VALUES ('pw', 'pw', 'a single process monitoring tool', '', 'Tools', 'pw.py, process, monitoring');")
		except: pass
				
	def execute(self, q):
		self.cur.execute(q)
		self.con.commit()
		return True

	def query(self, q):
		dataList = []
		self.cur.execute(q)
		data = self.cur.fetchall()
		if data: dataList = [list(row) for row in data]
		return dataList

	def commit(self, q):
		self.cur.execute(q)
		self.con.commit()

	def add_history(self, text):
		self.cur.execute("INSERT INTO history (date, time, text) VALUES (current_date, current_time, '%s')" % text.replace("'", '"'))
		self.con.commit()
	
class XOGet:
	version = "1.2.3"
	update_url = "http://xo-get.olpc.at/xo-get.py"

	repositories = []
	repositories.append(["http://xo-get.olpc.at", "/repository/xoget.xml"]);
	repositories.append(["http://xo-get.linuxuser.at", "/xoget.xml"]);
		
	localpath = "%s/%s" % (os.path.expanduser( '~' ), ".xo_get")

	def __init__(self, runaslib=False):
		# Loading DB
		self.db = Database(self.localpath, self.version)
		new_install = self.db.new_install
		new_update = self.db.new_update

		print "\n  xo-get %s\n  %s" % (self.version, ("~" * (len(self.version)+7)))		
		print 

		if new_update:
			# This update requires a db update
			self.db.execute("DROP TABLE IF EXISTS activities;")
			self.db.execute("CREATE TABLE 'activities'  ('id' INTEGER PRIMARY KEY AUTOINCREMENT, 'wiki_name' VARCHAR( 200 ), 'system_name' VARCHAR( 100 ),'version' VARCHAR( 30 ), 'xo_url' VARCHAR( 1023 ), 'category' VARCHAR( 255 ), 'description' TEXT, 'tags' VARCHAR( 255 ), 'filesize' VARCHAR( 20 ), 'flag' VARCHAR( 10 ), 'image' VARCHAR( 255 ), 'mime' VARCHAR( 255 ), 'repo' INT);")
			self.db.create_db()

		if runaslib: 
			self.get_activity_registry()
			return 
				
		if len(sys.argv) == 1:
			print "  http://wiki.laptop.org/go/Xo-get\n\n  Usage:\n    %s update\n    %s list    ['categories' / category_name ] \n    %s search  keyword\n    %s install activity_name / activity_file.xo \n    %s remove  activity_name / activity_file.xo / activity_directory\n    %s start   activity_name\n    %s status  ['log']" % (sys.argv[0], sys.argv[0], sys.argv[0], sys.argv[0], sys.argv[0], sys.argv[0], sys.argv[0])
			print
				

			if new_install:
				print "  New installation detected"

			elif new_update:
				print "  New Update detected. News:"
				print VERSION_NEWS

			if new_install or new_update:
				i = self.force_input("\n- Update the database now?", ["y", "n"])
				if i == "y":
					print
					self.update()			
					print

			sys.exit(0)
		
		self.get_activity_registry()

		if sys.argv[1] == "update":  self.update()
		if sys.argv[1] == "list":    self.list()
		if sys.argv[1] == "search":  self.search()
		if sys.argv[1] == "install": self.install()
		if sys.argv[1] == "remove":  self.remove()
		if sys.argv[1] == "status":  self.status()
		if sys.argv[1] == "start":   self.start_activity()

		print

	def activity_is_preinstalled(self, activity_name):
		activity_name = activity_name.lower().replace(" ", "")
		for a in self.activities:
			if a[0].lower().replace(" ", "") == activity_name:
				return a[3]
		return False
	
	def get_activity_filesize(self, activity_name):
		q = "SELECT filesize FROM activities WHERE wiki_name='%s' OR system_name='%s'" % (activity_name, activity_name)
		res = self.db.query(q)
		if len(res[0][0]) > 0 and res[0][0] != None:
			fs = int(res[0][0])
			rest = fs % 1000
			fs /= 1000
			if fs > 1000:
				rest = fs % 1000
				fs /= 1000
				ext = "mb"
			else:	ext = "kb"
			if rest > 99:
				rest /= 100
			
			return "%i.%i %s" % (fs, rest, ext)

		else:
			return "-"
		
		
	def get_activity_registry(self):
		self.activities = []

		try:
			from sugar import activity
			from dbus.mainloop.glib import DBusGMainLoop
			DBusGMainLoop(set_as_default=True)
		except: return False

		# Get Registry
		a_arr = activity.get_registry().get_activities()

		for a in a_arr:
			if "/usr/share" in a.path:
				is_system=True
			else: is_system = False
			self.activities.append(["%s" % a.name, "%s" % a.bundle_id, "%s" % a.path, is_system])

	def force_input(self, question, possibilities):
		i = ""
		while i not in possibilities:
			print "%s [%s]" % (question, "/".join(possibilities)),
			i = raw_input()
		return i

	def start_activity(self):
		if len(sys.argv) > 2:
			# Get Directory
			directory = None
			for a in self.activities:
				if sys.argv[2].replace("gcompris-", "").replace(" ", "") in a[0].lower().replace(" ", ""):
					directory = "%s" % a[2]

			if directory == None:
				print "  Activity not found. Please use './xo-get.py status'"
				return False
				
			os.chdir(directory)
			os.system("sugar-launch %s" % sys.argv[2])
			return True
		else:
			print "  Please add a activity-name: './xo-get.py start simcity'"
			return False
		
	def status(self):
		if len(sys.argv) > 2 and sys.argv[2] == 'log':
			# Display last history entries
			if len(sys.argv) > 3: l = int(sys.argv[3])
			else: l = 10
				
			print "  Last Actions:\n"
			res = self.db.query("SELECT * FROM history WHERE 1 ORDER BY id DESC LIMIT %i" % l)
			for h in res: print "  %s: [%s %s] %s" % (h[0], h[1], h[2][:h[2].rindex(":")], h[3])
			
		else:
			# Display Installed Activities
			print "  Installed Activities\n"
			i = 1
			for a in self.activities:
				if a[3]: label = "(Preinstalled)"
				else: label = ""
				print "  %i.  %s %s" % (i, a[0], label)
				i += 1
			return True

	def list(self):
		# Lists available Activities / Categories
		i = 1
		spaces = 18

		print "  Listing",
		q = "SELECT wiki_name, description, category, tags FROM activities WHERE 1"
		if len(sys.argv) > 2:
			
			if sys.argv[2] == "installed":
				print "  Installed Activities\n"
				i = 1
				for a in self.activities:
					if a[3]: label = "(Preinstalled)"
					else: label = ""
					print "  %i.  %s %s" % (i, a[0], label)
					i += 1
				return True
				
			elif sys.argv[2] == "categories":
				print "Categories\n"
				q = "SELECT DISTINCT category FROM activities WHERE 1 ORDER BY category ASC"
				res = self.db.query(q)
				i = 1
				for r in res:
					print "  %i. %s" % (i, r[0])
					i += 1

				if len(res) == 0: print " - 0 found"
				return True
				
			elif sys.argv[2] == "gcompris":
				q = "%s%s" % (q, " AND category = 'GCompris' ")
			
			else:
				print "Category '%s'" % sys.argv[2]
				spaces2 = 0
				q = "%s AND category LIKE '%s%s'" % (q, sys.argv[2], "%")
		else:
			print "All Activities"

		
		if "GCompris" not in q:	q = "%s%s" % (q, " AND category != 'GCompris' ")
			
		q = "%s%s" % (q, " ORDER BY category ASC, wiki_name ASC")
		res = self.db.query(q)

		cur_category = ''
		for r in res:
			if cur_category != r[2]:
				print "\n  %s" % r[2]
				cur_category = r[2]
			
			if len(r[1]) > 50: r[1]="%s..." % r[1][:50]

			if len(r[1]) > 0:
				print "    %i.%s%s .%s. %s" % (i, " " * (4 - len(str(i))), r[0], "." * (spaces - len(r[0])), r[1])
			else:
				print "    %i.%s%s" % (i, " " * (4 - len(str(i))), r[0])

			i += 1

		if len(sys.argv) < 3:
			print
			print "  GCompris"
			print "    %i.  GCompris: Please type '%s list gcompris' for a list of activities" % (i, sys.argv[0])
			
	def search(self):
		# Search for tags and name
		if len(sys.argv) > 2:
			s = sys.argv[2]
			print "- Results for '%s':" % s

			res = self.db.query(q = "SELECT wiki_name, description, category FROM activities WHERE tags LIKE '%s%s%s' OR wiki_name LIKE '%s%s%s' OR description LIKE '%s%s%s' ORDER BY category ASC, wiki_name ASC" % ('%', s, '%', '%', s, '%', '%', s, '%'))

			i = 1
			spaces = 18
			spaces2 = 14
			for r in res:
				print "  %i.  %s" % (i, r[0]), "." * (spaces - len(r[0]) + (2 - len(str(i)))), r[1]
				i += 1
		else:
			print "  Please supply search-string (eg: '%s search quiz')" % sys.argv[0]

	def update_xoget(self, to_version):
		# Set local script filename (/.../xo-get.py)
		fn = sys.argv[0]
		if fn.count('/') > 0: fn = fn[fn.rindex('/'):]		
		if fn[:1] == "/": fn = fn[1:]
		
		fn = "%s/%s" % (sys.path[0], fn)
		
		print "- Updating", fn

		# Download new Script		
		content = urllib2.urlopen(self.update_url).read()
		
		# Writing Self
		f = open(fn, "w")
		f.write(content)
		f.close()

		print "- Update to version %s successful. Please re-run xo-get." % to_version
		self.db.add_history("xo-get updated to version %s" % to_version)

	def get_content(self, repository_domain, repository_path):
 		print "- Contacting server: [ %s ]" % (repository_domain)
 		url = "%s%s" % (repository_domain, repository_path)
 
 		try: content = urllib2.urlopen(url).read()
 		except: 
 			print "- Not ok... do you have connection to the internet?"
 			return False
 		
 		if len(content) == 0: return False
 		return content

	def update(self, silent=False):
		i = 0
		while i < len(self.repositories):
			content = self.get_content(self.repositories[i][0], self.repositories[i][1])
			if content != False and "<repository" in content:
				break
			else: content = False
			
			i += 1

		if content == False:
			print "  Could not read any repository. Please try again later."
			return False

		# We have the xml in content
		# Parse XML => activities
		doc = xml.dom.minidom.parseString(content)
		activities = []
		for a in doc.childNodes[0].childNodes:
			act = []			
			for e in a.childNodes:
				try: 	act.append(e.lastChild.nodeValue.strip())
				except: pass
			if len(act) > 0: activities.append(act)
		
		xoget = activities[0]
		xoget_cur_ver = xoget[2]		
		activities.pop(0)
		
		print "- Local version: %s (current: %s)" % (self.version, xoget_cur_ver)
 			
 		# Check Version for possible update
		if not silent and self.version != xoget_cur_ver:
			# Up or Downgrade?
			if self.version < xoget_cur_ver: grade = "Upgrade"
			else: grade = "Downgrade"

			i = self.force_input("\n- %s xo-get to version: %s?" % (grade, xoget_cur_ver), ["y", "n"])
			if i == "y":
				print
				self.update_xoget(xoget_cur_ver)
				return True

		print		 		

		# Clear DB 
		self.db.commit("DELETE FROM activities WHERE 1")
		print "- Clearing database: ok\n"

		# Add Activities
		print "- Adding activities..."
		count = 0
		for a in activities:
			q = "INSERT INTO activities (wiki_name, system_name, version, xo_url, category, description, tags, filesize, flag, image, mime, repo) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (a[0], a[1], a[2], a[3], a[4], a[5].replace("'", ""), a[6], a[7], a[8], a[9], a[10], a[11])
			self.db.commit(q)
			count += 1
							
		print "- %i Activities Added" % count
		print		
		print "- Database is up-to-date"
		self.db.add_history("Database updated")
		
		return True
	
	def save_url(self, url, fn):
		print "  Download => %s" % fn
		try: 
			data = urllib2.urlopen(url).read()
		except:
			print "- Could not contact server."
			return False

		f = open(fn, "w")
		f.write(data)
		f.close()
		
	
	def install_pw(self):
		print "- installing pw.py"

		if self.save_url("http://www.linuxuser.at/process-watch/src/pw.txt", "%s/pw.py" % self.localpath) == False: return False
		if self.save_url("http://www.linuxuser.at/process-watch/src/pw-plugin-console.txt", "%s/pw-plugin-console.py" % self.localpath) == False: return False
		if self.save_url("http://www.linuxuser.at/process-watch/src/pw-plugin-gtk_graph.txt", "%s/pw-plugin-gtk_graph.py" % self.localpath) == False: return False

		os.system("chmod 755 %s/pw.py" % self.localpath)
		
		print "- done :)"
		print

		res = os.popen("grep 'alias pw' %s/.bashrc" % self.localpath[:-8]).read().strip()
		if len(res) == 0:	
			os.system("echo \"alias pw='%s/pw.py'\" >> %s/.bashrc" % (self.localpath, self.localpath[:-8]))
			os.system("source %s/.bashrc" % self.localpath[:-8])

			print "  to run pw.py with the command 'pw', either"
			print "  restart the console or type 'source ~/.bashrc"

		
	def install(self, activity_name=None, silent=False):
		fn = None	
		
		if activity_name != None:
			s = activity_name
		else:
			s = None
			if len(sys.argv) > 2:
				s = sys.argv[2]
		
		# Check Parameters
		if s != None:
			if s == "procwatch" or s == "pw" or s == "pw.py":
				self.install_pw()
				return True
				
			if s == "gcompris":
				self.install_gcompris_all()
				return True
				
			# NEW: Install via Supplied .xo filename
			if os.path.isfile(s):
				print "- Installing Activity via File '%s'" % s
				return self.install_xofile(s, None, True)
				
		else:
			print "- Plase supply an activity_name (eg: '%s install imagequiz')" %  sys.argv[0]
			return False

		# Normal Install with an Activity's Name
		# Search for xo_url
		q = "SELECT xo_url, id FROM activities WHERE wiki_name='%s' OR system_name='%s'" % (s, s)
		res = self.db.query(q)

		# If no xo_url, then Search for similar Name!
		if len(res) == 0:
			# Search DB with LIKE
			print "- No exact match found. Extending search...\n"
			q = "SELECT wiki_name FROM activities WHERE wiki_name LIKE '%s%s'" % (s, "%")
			res = self.db.query(q)
			if len(res) == 0:
				print "  Activity '%s' not found.\n  Try '%s search'" % (s, sys.argv[0])
				return False
			else:
				s = res[0][0]
				res = self.db.query("SELECT xo_url, id FROM activities WHERE wiki_name='%s'" % s)

		# Format Filesize
		fs = self.get_activity_filesize(s)
		print "  Installing Activity '%s' (%s):" % (s, fs)

		# We send the to install_xofile .xo url now
		return self.install_xofile(res[0][0], res[0][1], False, silent)

	def install_gcompris_all(self):
		s = self.force_input("  - Really install all GCompris Activities (> 100)?", ["y", "n"])
		if s == "n": return False
		
		res = self.db.query("SELECT xo_url FROM activities WHERE category='GCompris'")

		i = 0
		for url in res:
			self.install_xofile(url[0], None, False, True)
	
	def install_xofile(self, url, db_id=None, local=False, silent=False):
		if silent: i = "y"
		else: i = self.force_input("  - Do you want to proceed?", ["y", "n"])									
		
		if i == "n": return False
		print 

		# make a fn from the url
		if local:
			# Use local .xo file
			fn = url
		
		else:
			fn = "%s/%s" % (self.localpath, url[url.rindex('/')+1:])
			if fn.count(";f=") > 0: fn = fn[fn.index(";f=")+3:] # dev.laptop.org hack
				
			# start Download
			print "- Download => %s" % (fn)

			# 1. Check if file exists
			download = True
			if os.path.isfile(fn):
				if silent:
					print "  - File already here. Skipping Download"
					download = False
				else:
					i = self.force_input("  - File already exists. Download again?", ["y", "n"])
					if i == "n": download = False
				print

			# 2. If wanted, download .xo
			if download:
				try: xo = urllib2.urlopen(url).read()
				except ValueError:
					print "- Could not contact server."
					return False
				except urllib2.HTTPError:
					print "- Could not download file."
					return False
				except urllib2.URLError:
					print "- Could not contact server."
					return False
				except KeyboardInterrupt:
					print "- Stopped"
					sys.exit(1)
				
				f = open(fn, "w")
				f.write(xo)
				f.close()

#		print fn
		# Start Installation - Try The Sugar Way
		print "- Starting Installation"

		try: 	
			sugar_loaded = True
			from sugar.bundle.activitybundle import ActivityBundle
		except: sugar_loaded = False

		try: 
			dbus_loaded = True
			from dbus.mainloop.glib import DBusGMainLoop
			DBusGMainLoop(set_as_default=True)
		except:	dbus_loaded = False
		
		if sugar_loaded and dbus_loaded:
			bundle = ActivityBundle(fn)
#			print bundle.get_name()
			try: 
				bundle.install()
				self.db.add_history("Activity Installed: '%s'" % bundle.get_name())

			except: 
				print "  - Error installing Activity. Maybe already installed."
				self.db.add_history("Activity Installation Failed: '%s'" % fn)
				return False

		else:
			if sugar_loaded == False: print "  - Couldn't load sugar.bundle.activitybundle"
			if dbus_loaded == False:  print "  - Couldn't load dbus.mainloop.glib"
			if silent == False: print
			
			if silent: i = "n"
			else: i = self.force_input("  - Unzip the Bundle to %s/?" % self.localpath, ["y", "n"])
			
			if i == "y":
				c = "unzip %s -d %s" % (fn, self.localpath)
				print "\n- %s" % c
				os.system(c)
				self.db.add_history("Unzipped Activity '%s'" % fn[fn.rindex('/')+1:])
			
			return False
	
		print
		print "- Installation Finished"
		return True

	def remove(self, activity_name=None, silent=False):
		# To remove, we need sugar, the .xo file, or an name
		if activity_name != None:
			app_name = activity_name
		else:
			app_name = None
			if len(sys.argv) > 2:
				app_name = sys.argv[2]
			
		if app_name != None:
			try: 
				sugar_loaded = True
				from sugar.bundle.activitybundle import ActivityBundle
			except: sugar_loaded = False

			try: 
				dbus_loaded = True
				from dbus.mainloop.glib import DBusGMainLoop
				DBusGMainLoop(set_as_default=True)
			except:	dbus_loaded = False

			if sugar_loaded and dbus_loaded:					
				print "  Starting to remove '%s'" % app_name
				print
				fn = None
				
				# NEW: remove activity from .xo-file / directory (outside repo)
				if os.path.isfile(app_name):
					print "  (Infos from .xo file)"
					fn = app_name
					
				elif os.path.isdir(app_name):
					print "  (Infos from Activity-Directory)"
					for a in self.activities:
						# Check Directories and set app_name and fn
						if app_name.replace("/", "") in a[2].replace("/", ""):
							app_name = a[0]
							fn = a[2]
						
					if fn == None:
						return False
					
				else:				
					app_name = app_name.lower()
					for a in self.activities:
						if app_name.replace("gcompris-", "").replace(" ", "").replace("_", "") in a[0].lower().replace(" ", "").replace("_", ""):
							app_name = a[0]
							fn = a[2] 	# a[2] is the local directory

#					print "1", fn
					if fn == None:
						# No Activity found yet.
						# Try searching the Database to get the .xo Filename
						q = "SELECT xo_url, id FROM activities WHERE wiki_name = '%s' OR system_name = '%s'" % (app_name, app_name)
						res = self.db.query(q)
						
						if len(res) > 0:
							# Put .xo link => fn
							fn = res[0][0]
							fn = os.path.basename(fn)
							fn = "%s/%s" % (self.localpath, fn)
							if not os.path.isfile(fn):
								print "- Sorry, no link found."
								print "  Try 'xo-get status' and 'xo-get remove ...' with the name from status"
								return False

						else:
							q = "SELECT wiki_name FROM activities WHERE wiki_name LIKE '%s' OR system_name LIKE '%s' " % (app_name, app_name)
							res = self.db.query(q)
						
							if len(res) > 0:
								app_name = res[0][0]
								q = "SELECT xo_url, id FROM activities WHERE wiki_name = '%s'" % app_name
								res = self.db.query(q)
								
								# Pur .xo link => fn
								fn = res[0][0]
								fn = os.path.basename(fn)
								fn = "%s/%s" % (self.localpath, fn)
								if not os.path.isfile(fn):
									print "- Sorry, no link found."
									print "  Try 'xo-get status' and 'xo-get remove ...' with the name from status"
									return False

#						print "2", fn
						if fn == None:
							# Really nothing found ... :(
							print "- No Activity '%s' installed" % app_name
							return False
							
					
				# Security Question
				if not silent:
					i = self.force_input("- Remove activity '%s'?" % app_name, ["y", "n"])
					if i == "n": return False
					
				# Open Activity Bundle
				try: bundle = ActivityBundle(fn)
				except:
					print "- Couldn't load Bundle. Stopping."
					return False

				try: bundle.uninstall()
				except: 
					print "- Failed"
					self.db.add_history("Removing Activity '%s' Failed" % app_name)
					return False
					
				self.db.add_history("Removed Activity '%s'" % app_name)

				print "- Removing Finished!"
				return True
										
			else:
				if dbus_loaded == False: print "- Couldn't load dbus.mainloop.glib"
				if sugar_loaded == False: 
					print "- Couldn't load sugar environment; removing not possible."
					print "  http://wiki.laptop.org/go/Sugar"
					return False
			
		else:
			# len(sys.argv) != 2
			print "- Plase supply an activity_name (eg: '%s remove imagequiz')" %  sys.argv[0]
			return False
		
		return True
		
if __name__ == "__main__":
	xoget = XOGet()
