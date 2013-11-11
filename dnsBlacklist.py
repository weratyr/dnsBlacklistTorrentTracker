import re
import sqlite3
import hashlib
import urllib
import os
import gzip

def readFile(txtFile):
	f = open(txtFile, 'r')
	return f.readlines()


def parseLines(lines):
	x=getLastSqlID()+1
	for i in range(0, len(lines)):
		#print lines[i]
		matchObj = re.match( r'.*\|.*//(.*):|/{1}', lines[i], re.M|re.I)
		if matchObj:
			url=matchObj.group(1)
			row = getCurserForExistingUrl(url)
			if row == 1:
				print "already exist"
			else:
				insertEntryToSql(url,x,lines[i])
				print "Add URL to database successfully!!"
				x+=1
	

def getLastSqlID():
	conn = sqlite3.connect('blacklist.db')
	lastID = conn.execute("SELECT id FROM BLACKLIST ORDER BY ID DESC LIMIT 1").fetchone()
	if lastID:
		last=lastID[0]
		conn.close()
		return last
	else:
		return 1


def getCurserForExistingUrl(url):
	conn = sqlite3.connect('blacklist.db')
	count = conn.execute("SELECT url FROM BLACKLIST WHERE url = ?", (url,)).fetchall()
	conn.close()

	if len(count) >= 1:
		return 1
	else:
		return 0


def insertEntryToSql(url,rowId,line):
	conn = sqlite3.connect('blacklist.db')
	conn.execute("INSERT INTO BLACKLIST (ID,URL,PORT,original) \
		VALUES (?, ?, 0, ?)",(rowId, url,line))
	conn.commit()
	conn.close()


def determinCheckSum(fileName):
	with open(fileName) as file_to_check:
		return hashlib.md5(file_to_check.read()).hexdigest()

def createDnsmasqBlacklistFile():
	conn = sqlite3.connect('blacklist.db')
	cursor = conn.execute("SELECT url FROM BLACKLIST")
	dnsList=[]
	for row in cursor:
		dnsEntry = "address=/%s/127.0.0.1" % row[0]
		dnsList.append(dnsEntry)
	conn.close()

	blackistFile=open("blacklist.conf",'wb')
	for entry in dnsList:
		if entry.find(':')!=-1:
			print "exclude: ",
			print entry
		else:
			blackistFile.write(entry+'\n')
	blacklistCustom=open("blacklist_custom.conf").read()
	blackistFile.write(blacklistCustom)
	blackistFile.close()


try:
   with open('blacklist.db'):
   	print "Check for DB .... . Exist "
except IOError:
   conn = sqlite3.connect('blacklist.db')
   print "Opened database successfully";
   conn.execute('''CREATE TABLE BLACKLIST
       (ID INT PRIMARY KEY     NOT NULL,
       url           CHAR(100)    NOT NULL,
       port            INT     NOT NULL,
       original        CHAR(100));''')
   print "Table created successfully";
   conn.close()




print "Download current List"
#urllib.urlretrieve ("http://bitsnoop.eu/export/b3_e003_trackers.txt.gz", "b3_e003_trackers.txt.gz")
print "Checksum test"
oldDoNotExist=False
old=0
try:
	current=determinCheckSum("b3_e003_trackers.txt.gz")
	try:
		with open("b3_e003_trackers.txt.gz-old"):
			old=    determinCheckSum("b3_e003_trackers.txt.gz-old")
	except IOError:
		oldDoNotExist=True
		print "old list not exist"
		print ""
	if  current != old or oldDoNotExist == True:
		fileTrackers = gzip.open("b3_e003_trackers.txt.gz").readlines()
		os.rename("b3_e003_trackers.txt.gz","b3_e003_trackers.txt.gz-old")
		parseLines(fileTrackers)
	else:
		print "nothing to update"
		print "create blackist.txt"
		createDnsmasqBlacklistFile()
except IOError:
	print "No files found!!!"
