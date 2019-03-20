#!/bin/bash -l
#$ -cwd
#$ -S /bin/bash
#$ -pe mpi 20
#$ -q production.q
#$ -l excl=1

# FULL PATH! 
BCLDIR=$1 # full path here
DMX=/home/xjmatm/repos/misc_scripts/demultiplex.py

$DMX -b $BCLDIR
