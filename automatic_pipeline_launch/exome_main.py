#!/apps/bio/software/anaconda2/envs/cre2py/bin/python
# -*- coding: utf-8 -*-
import configparser
from subprocess import call
import time
import shutil
import glob
import os
import sys
import cronseq_functions
import os.path
from multiprocessing import Pool
import contextlib

# Set start date and time for script
starttime = time.strftime("%Y-%m-%d-%H-%M-%S")

config = configparser.RawConfigParser()
config.read('exome_config.cfg')

################################################################
# Define static variables
# ------------------------------------------------------------->

# Directory where data arrives
bclpath = config.get("paths", "bclpath")

# Old list of runs from previous croninstance
oldrunidfile = config.get("paths", "oldrunidlist")

#################################################################
# Look for new data in bclpath, exit script of none is found
# -------------------------------------------------------------->
newruns = cronseq_functions.look_for_data(bclpath, oldrunidfile)
if not newruns:
	# NO NEW DATA FOUND
	# <<<<<<<<-- !!!!!!!!!!!!!
	# <<<<<<<<--  Exit script!  
	# <<<<<<<<-- !!!!!!!!!!!!!
	sys.exit()

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# >> NEW DATA DISCOVERED >> CONTINUING >>>>>>>>>>>>>>>>>>>>>>>>>
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

#################################################################
# Send mail to notify GeneCoreSU that they can put in SampleSheet.csv
# -------------------------------------------------------------->
seqmail, seqperson = config.get("emaillist", "MJ").split(",")
sender = 'CRE2 automatic script'
for newrun in newruns:
	subject = "{} Has been sequenced and transferred".format(newrun)
	message = "Sequencing run {} has been sequenced and transferred to medstore. Now waiting for SampleSheet.csv before analysis can be started.".format(newrun)
#	cronseq_functions.sendmail(seqmail, seqperson, subject, message, sender)

#################################################################
# Start main analysis function in parallel for each run
# ------------------------------------------------------------->

newrun_fullpath = [bclpath + x for x in newruns]
if __name__ == '__main__':
	numnewruns = len(newruns)
	with contextlib.closing(Pool(processes=numnewruns)) as pool:
		pool.map(cronseq_functions.run_start, newrun_fullpath)
	



#################################################################
# Waiting for SampleSheet.csv in new runs, when discov


################################################
# Sending list of new runs to next step -->
#for newrun in newruns:
#	cronseq_functions.run_start(newrun)
#	os.system("./exome_run_main.py %s" % newrun)

# Exit script <<<<-----



# Get samplesheet investigator from config 
#investigator = config.get("emaillist", "EWB").split(",")

