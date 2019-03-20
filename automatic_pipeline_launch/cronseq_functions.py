#!/apps/bio/software/anaconda2/envs/cre2py/bin/python
# -*- coding: utf-8 -*-
import configparser
from subprocess import call
import subprocess
import time
import shutil
import glob
import os
import sys
import os.path
import ntpath
import csv
import re

config = configparser.RawConfigParser()
config.read('exome_config.cfg')

# LOOK FOR NEW DATA FUNCTION
def look_for_data(datapath, olddatalist):
	###############################
	# Look for new analysable runs in seqdir
	# If new data is discovered, replace old list with current list
	# Set date and time for tmpfile
	starttime = time.strftime("%Y-%m-%d-%H-%M-%S")
	# Current list of runs in seqdir
	newrunids = [os.path.basename(x) for x in glob.glob(datapath + "[0-9][0-9][0-9][0-9][0-9][0-9]*") if os.path.isfile("{}/RunCompletionStatus.xml".format(x))]

	# Read old list of runs from previous croninstance
	oldrunids = []
	with open(olddatalist, 'r' ) as oldrunid:
		oldrunids = [entry.strip('\n') for entry in oldrunid.readlines()]

	# Compare current list from previous list
	newruns = list(set(newrunids) - set(oldrunids))
	if not newruns:
		# Exit function <<<<-----
		return None

	###################################
	# Replace old runid-list with new
	# Create file with new runid-list
	newrunidfile = "{}_{}.tmp".format(olddatalist,starttime)
	with open(newrunidfile, 'w') as newrunidout:
		for runid in newrunids:
			newrunidout.write(runid + "\n")

	# Replace old list with new list
	os.remove(olddatalist)
	shutil.move(newrunidfile, olddatalist)

	# Return list of new analysable runs
	return newruns

# SEND MAIL FUNCTION
def sendmail(emails, users, subject, message, sender):
	# Prepare emails
	emaillist = emails.split(',')
	userlist = users.split(',')
	email_list = []
	for emailnum, email in enumerate(emaillist):
		user = userlist[emailnum]	
		email_list.append('From: \"%s\" <clinical.genomics@medair.sahlgrenska.gu.se>' % sender + '\n'
				+ 'To: \"%s\" <%s>' % (user, email) + '\n'
				+ 'Subject: %s' % subject + '\n'
				+ '%s' % message + '\n'
				+ '\n'
				+ 'Best regards,' + '\n'
				+ 'Clinical Genomics Gothenburg')

	# Send prepared emails
	for mail in email_list:
		subprocess.call('echo "%s" | /usr/sbin/sendmail -i -t' % mail, shell=True)

# RUN START WRAPPER FUNCTION
def run_start(run_path):
	newrun=ntpath.basename(run_path)
	# Wait for samplesheet
	sleepcount=8638
	while os.path.isfile("{}/SampleSheet.csv".format(run_path)) is False:
		time.sleep(60)
		sleepcount+=1
		# Check if script has waited 4 days for SampleSheet.csv
		if sleepcount == 5760:
			genomicsmail, genomicsperson = config.get("emaillist", "MJ").split(",")
			sender = 'CRE2 automatic script'
			subject = "Waited 4 days for SampleSheet.csv in {}".format(newrun)
			message = "Sequencing run {} has been sequenced and transferred to medstore. This email is a reminder to put SampleSheet.csv into the sequencingdirectory. Will wait for 2 more days then the script will exit and the run will be ignored.".format(newrun)
			sendmail(genomicsmail, genomicsperson, subject, message, sender)
		# Check if script has waited for 6 days for SampleSheet.csv and if so, break out of loop
		if sleepcount == 8640:
			break
	
	samplesheet_fix("{}/SampleSheet.csv".format(run_path))
	samplelist_dicts, investigator_dicts = samplesheet_info("{}/SampleSheet.csv".format(run_path), newrun)
#	warnings_and_errors(samplelist_dicts)
	bcldir = config.get("paths", "bclpath") + newrun
	demultidir = config.get("paths", "demultipath") + newrun
	
	demultiplex_run(bcldir, demultidir)

def demultiplex_run(bcldir, demultidir):
	print(bcldir)
	print(demultidir)
	run = ntpath.basename(demultidir)
	print("{}/logs/{}_bcl2fastq.log".format(demultidir, run))
	if os.path.isfile("{}/logs/{}_bcl2fastq.log".format(demultidir, run)):
		last_line = subprocess.check_output(['tail', '-1', "{}/logs/{}_bcl2fastq.log".format(demultidir, run)])
		if "0 errors" in last_line:
			print("Has not been successfully demultiplexed")
		else:
			print("Has encountered errors during demultiplexing")
		#qsub /root/cronscripts/cron_exome/demultiplex_script.sh bcldir demultidir
	else:
		print("Has not been demultiplexed")

# CAPTURE MISTAKES AND SEND MAILS
#def warnings_and_errors(sample_dicts):
	# dep_name = UNKNOWN (specified department not found)
	# prins_mail = N (principal investigator not found)
	# insilico = Y, path = N (insilico panel specified but bed-file not found in CLC)
	

# COPY AND REMOVE ILLEGAL CHARACTERS FROM SAMPLESHEET
def samplesheet_fix(samplesheet):
	# Change name to Samplesheet.csv_original
	originalname = "{}_original".format(samplesheet)
	os.rename(samplesheet, originalname)
	# Remove illegal characters
	with open("{}_original".format(samplesheet), 'r') as infile, open(samplesheet, 'w') as newssheet:
		chars = {'å' : 'a', 'ä' : 'a', 'ö' : 'o', '"' : '_'}
		data = infile.read()	
		for char, replace in chars.items():		
			data = data.replace(char, replace)
		newssheet.write(data)

# GET INFORMATION FROM SAMPLESHEET
def samplesheet_info(samplesheet, runid):
	##################################################################
	# Validate, correct and extract metadata from SampleSheet.csv
	# ------------------------------------------------------------->
	with open(samplesheet, 'r') as samplesheetcsv:
		samplesheet = csv.reader(samplesheetcsv)
		# Create list with sample-data dictionaries
		# Samplename, Department, Principal investigator, InSilico
		samplelist = []
		investigatorlist = []
		datarows = False
		######################################################
		# -------------->>>>>>>>> Loop through SampleSheet
		for row in samplesheet:
			# Get GeneCoreSU personel-information
			if row[0].lower() == "investigator name":
				# Loop through investigator initials in samplesheet
				for initials in row[1:]:
					if initials:
						try:
							# Search for investigator details in config 
							seqmail, seqperson = config.get("emaillist", initials).split(",")
						except: 
							# Investigator details not found, switching to genomics-mail
							seqmail, seqperson = config.get("emaillist" "MJ").split(",")
						seqpersondict = {'seqmail' : seqmail, 'seqperson' : seqperson}
						investigatorlist.append(seqpersondict)
				
			if datarows:
				dep_init = row[9].split("_")[0]
				if re.findall('[BG][1-3][0-9]-[0-9]{3}', dep_init):
					clc_dep_path = config.get("departmentlist", "RSEARCH")
					dep_name, dep_igv_user = dep_init, "None"
					sampledict = {'runid' : runid, 'sample' : row[0], 'dep_name' : dep_name, 'clc_path' : clc_dep_path, 'igv_user' : "None", 'prins_name' : "None", 'prins_mail' : "None", 'insilico_name' : "None", 'insilico_path' : "None"}
				else:
					try:
						clc_dep_path, dep_name, dep_igv_user = config.get("departmentlist", dep_init).split(",")
					except:
						clc_dep_path, dep_name, dep_igv_user = config.get("departmentlist", "UNKNOWN").split(",")
					try:
						prins_init = row[9].split("_")[1]
						prins_mail, prins_name = config.get("emaillist", prins_init).split(",")
					except:
						prins_mail, prins_name = ["None", "None"]
					try:
						insilico_name = row[9].split("_")[2]
						insilico_path = config.get("department_insilico", dep_init)
						if os.path.isfile("/medstore/{}{}.clc".format(insilico_path, insilico_name.lower())):
							insilico_path = "{}{}.clc".format(insilico_path, insilico_name.lower())
						else:
							insilico_path = "None"
					except:
						insilico_name, insilico_path = ["None", "None"] 
					sampledict = {'runid' : runid, 'sample' : row[0], 'dep_name' : dep_name, 'prins_name' : prins_name, 'prins_email' : prins_mail, 'insilico_name' : insilico_name, 'insilico_path' : insilico_path, 'clc_dep_path' : clc_dep_path, 'igv_user' : dep_igv_user}
				samplelist.append(sampledict)	
			if row[0].lower() == "sample_id":
				datarows = True
	return(samplelist, investigatorlist)

#def samplesheet_errors():
			




#def samplesheet_valid(runid_path)


#def samplesheet_info(runid_path)
#	return samplesheet_data
