import re
import sqlite3
import hashlib
import urllib
import os
import gzip
import subprocess

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
			if getCurserForExistingUrl(url) == 1:
				print "already exist"
			else:
				insertEntryToSql(url,x,lines[i])
				print "Add URL to database successfully!!"
				x+=1


def parseLinesLogFiles():
	x=getLastSqlID()+1

	cmd= [ 'egrep -E \'torrent|transmis|vuze|bitcomet|bitlord|donkey|shareaza\' logs/*']
	#cmd1 = ['grep "query\[A\]" | awk  -F" " \'{print $8}\'']
	cmd1 = ['awk  -F" " \'{print $8}\'']
	egrep = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
	lines = egrep.stdout.readlines()
	#awk  = subprocess.Popen(cmd1,shell=True,stdin=lines, stdout=subprocess.PIPE)
	#print lines
	for line in lines:
		line = line.split(" ")
		lineToSave = line[7],line[8],line[9].rstrip()
		url=line[7]
		if getCurserForExistingUrl(url) == 1:
			print "already exist!!!!"
		else:
			#insertEntryToSql(url,x,lines[i])
			print "add URL to db!!"
			x+=1
			print "test:", url
	

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




#print parseLinesLogFiles()
#quit()
#dnsmasqPid=subprocess.call('ssh -t root@isp  ps  |grep dnsmasq|awk -F" " \'{print $1}\'', shell=True)
#ssh=subprocess.call('ssh -t root@isp  ps  |grep dnsmasq|awk -F" " \'{print $1}\'', shell=True)


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


###### TODO 
#### import scp
# client = scp.Client(host=host, user=user, keyfile=keyfile)
# # or
# client = scp.Client(host=host, user=user)
# client.use_system_keys()
# # or
# client = scp.Client(host=host, user=user, password=password)
# client.transfer('/etc/local/filename', '/etc/remote/filename')

### restart dnsmasq



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
