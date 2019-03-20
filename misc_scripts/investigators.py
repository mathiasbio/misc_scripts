#!/apps/bio/software/anaconda2/envs/sentieon_py/bin/python
import os
import sys
import json
import argparse
import subprocess
from sample_sheet import SampleSheet
from validate_samplesheet import SampleSheetVerifier


class Investigator:
    def __init__(self, initials):
        self.initials, self.name, self.email = investigator_info(initials)


def investigator_info(initials):
    investigator_data = read_investigatorlist()
    investigator = investigator_data["investigators"][initials]
    name = investigator["name"]
    email = investigator["email"]
    return initials, name, email

def read_investigatorlist():
    with open("investigator_list.json", 'r') as investigators:
        investigator_data = json.load(investigators)
        return investigator_data

def create_investigators(samplesheet_path):
    samplesheet_data = SampleSheet(samplesheet_path)
    header_info = samplesheet_data.Header
    investigator_initials_list = header_info['Investigator Name'].split(";")
    investigator_dict = {}
    for investigator_initials in investigator_initials_list:
        investigator_dict[investigator_initials] = Investigator(investigator_initials)

    return investigator_dict
