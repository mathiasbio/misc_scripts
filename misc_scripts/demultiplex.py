#!/apps/bio/software/anaconda2/envs/sentieon_py/bin/python
import os
import sys
import json
import argparse
import subprocess
from sample_sheet import SampleSheet
from validate_samplesheet import SampleSheetVerifier
from mailer import send_mail
import investigators



def read_config():
    with open("analysis_config.json", 'r') as config:
        config_data = json.load(config)
        return config_data

def read_samplesheet(bcldir):
    # Check if SampleSheet.csv exists
    if not os.path.isfile("{}/SampleSheet.csv".format(bcldir)):
        print("No SampleSheet.csv found in %s. Nothing to do, exiting." % bcldir)
        sys.exit()
    samplesheet_path = "{}/SampleSheet.csv".format(bcldir)
    
    # Validate SampleSheet structure
    validate_samplesheet(samplesheet_path)
    # Create Investigators from SampleSheet
    investigator_dict = investigators.create_investigators(samplesheet_path)
    #for key in investigator_dict:
    #    print(investigator_dict[key].email)
    #    print(investigator_dict[key].name)
    return investigator_dict

def demultiplex_success(bcl2fastq_log):
    with open(bcl2fastq_log, 'r') as bcllog:
        lines = bcllog.read().splitlines()
        last_line = lines[-1]
        success_string = "Processing completed with 0 errors and 0 warnings"
        if success_string in last_line:
            return True
        else:
            return False

def demultiplex_stats(investigator_dict, demultiplex_dir, bcldir):
    conf = read_config()
    my_env = os.environ.copy()
    dmx_stats = conf["demultiplex"]["dmx_stats"]
    
    samplesheet_path = f"{bcldir}/SampleSheet.csv"
    dmx_stats_results = f"{demultiplex_dir}/{os.path.basename(demultiplex_dir)}_demultiplex_stats.tsv"
    
    if not os.path.isfile(dmx_stats_results):
        dmx_stats_args = [dmx_stats, samplesheet_path, demultiplex_dir]    
        subprocess.call(dmx_stats_args, shell=False, env=my_env) 
    
    email_list = []
    for key in investigator_dict:
        email_list.append(investigator_dict[key].email)    

    attachment = dmx_stats_results
    mailsubject=f"Demultiplex report: {os.path.basename(demultiplex_dir)}"
    mailbody = f"""
    Demultiplexing of {os.path.basename(demultiplex_dir)} is complete. The report is attached in this mail.

    If you have any question you can reach us at:
    clinicalgenomics@gu.se
    Or reply to this email.

    Kind regards,
    /Clinical Genomics Göteborg\n\n
    """
    send_mail(mailsubject, mailbody, attachment, email_list) 


def validate_samplesheet(samplesheet_path):
    SSverify = SampleSheetVerifier(samplesheet_path)
    if SSverify.errors:
        for error in SSverify.errors:
            print(error)
        print("SampleSheet.csv had errors, exiting.")
        sys.exit()
    return SSverify

def demultiplex_run(bcldir, email):
    my_env = os.environ.copy()
    conf = read_config()
   
    # Format bcldir-path (remove trailing /)
    if bcldir.endswith('/'):
        bcldir = bcldir[:-1]
 
    # Is bcldir actually a directory?
    if not os.path.isdir(bcldir):
        print(bcldir + " is not a directory. Exiting.")
        sys.exit()
   
    # Read SampleSheet.csv (Validate it and extract Investigator information)
    investigator_dict = read_samplesheet(bcldir)

    bcl2fastq = conf["demultiplex"]["bcl2fastq"]

    # Define DMX output directory
    demultiplex_output_home = conf["demultiplex"]["output"]
    if not os.path.isdir(demultiplex_output_home):
        print("Demultiplex output directory does not exist. Check path in analysis config.")
        sys.exit()
    # Get RunID
    run_id = os.path.basename(bcldir)
    demultiplex_results = "{}/{}".format(demultiplex_output_home, run_id)
    # Define DMX logfile-path
    demultiplex_log = "{}/{}_bcl2fastq.log".format(demultiplex_results, run_id)

    # Create DMX output directory if not already exists
    if not os.path.isdir(demultiplex_results):
        try:
            os.mkdir(demultiplex_results)
        except OSError:
            print("Creation of directory: %s failed. Exiting script" % demultiplex_results)
            sys.exit()
        else:
            print("Creation of directory: %s successful" % demultiplex_results)
    else:    
        # Check if DMX output directory contains bcl2fastq log
        if os.path.isfile(demultiplex_log):
            print(f"{demultiplex_results} contains {os.path.basename(demultiplex_log)}, likely contains demultiplex-results. Now checking if it appears to have been successful")
            # Check demultiplex success [ if successful --> create dmx-report and mail | if failed --> exit script ]
            if demultiplex_success(demultiplex_log): 
                print(f"{os.path.basename(demultiplex_log)} contains 0 errors and 0 warnings. Probably successful. Continuing.")
                demultiplex_stats(investigator_dict, demultiplex_results, bcldir)
                sys.exit()
            else:
                print("Demultiplexing appears to have failed or is incomplete. Exiting.")
                sys.exit()

    #bcl2fastq_args = [bcl2fastq, "--runfolder-dir", bcldir, "-o", demultiplex_results, "-r20", "-p20", "-w20", "--barcode-mismatches", "1", "--min-log-level", "TRACE", "&>>", demultiplex_log]
    bcl2fastq_args = f"{bcl2fastq} --runfolder-dir {bcldir} -o {demultiplex_results} -r20 -p20 -w20 --barcode-mismatches 1 --min-log-level TRACE &>> {demultiplex_log}"
    subprocess.call(bcl2fastq_args, shell=True, env=my_env)

    # Check if DMX output directory contains bcl2fastq log
    if os.path.isfile(demultiplex_log):
        print(f"{demultiplex_results} contains {os.path.basename(demultiplex_log)}, likely contains demultiplex-results. Now checking if it appears to have been successful")
        # Check demultiplex success [ if successful --> create dmx-report and mail | if failed --> exit script ]
        if demultiplex_success(demultiplex_log):
            print(f"{os.path.basename(demultiplex_log)} contains 0 errors and 0 warnings. Probably successful. Continuing.")
            demultiplex_stats(investigator_dict, demultiplex_results, bcldir)
            sys.exit()
        else:
            print("Demultiplexing appears to have failed or is incomplete. Exiting.")
            sys.exit()



if __name__ == '__main__':
        parser = argparse.ArgumentParser()
        parser.add_argument('-b', '--bcldir', nargs='?', help='Input full path to bcldir', required=True)
        parser.add_argument('-e', '--email', nargs='?', help='Input E-mail adress (overrides) samplesheet-intitials ', type=int, required=False)
        args = parser.parse_args()
        bcldir = args.bcldir
        email = args.email
        if not email:
            demultiplex_run(bcldir, email="none")
        else:
            demultiplex_run(bcldir, email)
