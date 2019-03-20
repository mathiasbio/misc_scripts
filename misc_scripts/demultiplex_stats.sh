#!/bin/bash -l


muttMail()
{
EMAILCONTENT=$"""

Hello

$4

If you have any question you can reach us at:
clinicalgenomics@gu.se
Or reply to this email.

Best regards,
Clinical Genomics Gothenburg
"""
echo "$EMAILCONTENT" | mutt -s "$3" -e "my_hdr From: Demultiplex-script CGG  <clinicalgenomics@gu.se>" $5 -- "$1 <$2>"
}

SAMPLESHEET=$1
DMXDIR=$2
RUNNAME=$(basename $(dirname $SAMPLESHEET))
RUNID=$(echo "$RUNNAME" | cut -d"_" -f4 | cut -c2-)

ALL_DATA=$(echo "")
PREVLANES=0
SREADSTOT=0
for samplerow in $(awk '/Sample_ID/{flag=1;next}/*/{flag=0}flag' $SAMPLESHEET);
do
	samplename=$(echo "$samplerow" | cut -d"," -f1)
	project=$(echo "$samplerow" | cut -d"," -f10)
	I7_Index_ID=$(echo "$samplerow" | cut -d"," -f7)
	I5_Index_ID=$(echo "$samplerow" | cut -d"," -f9)
	DMXINFO=$(find $DMXDIR/Reports/html/$RUNID -name "lane.html" | grep "/$project/$samplename/all/")
	READSHTML=$(grep "<td>" $DMXINFO | sed "4q;d" | sed 's/[<td>|,|</td>]//g')
	SREADSTOT=$(($READSHTML+$SREADSTOT))
	LANES=$(grep "<td>[1-9]</td>" $DMXINFO | wc -l)
	SUMR=0
	HEADER=$(echo -e "SampleName\tProject\tI7_Index_ID\tI5_Index_ID\t# Readpairs\t# MegaReadpairs")
	MREADS=$(echo "scale=2; $READSHTML/1000000" | bc)
	DATA=$(echo -e "$samplename\t$project\t$I7_Index_ID\t$I5_Index_ID\t$READSHTML\t$MREADS")
	for lane in $(seq 1 $LANES);
	do
		HEADER=$(echo -e "$HEADER\t# Readpairs Lane$lane")
		LANER=$(grep "<td>" $DMXINFO | grep "<td>$lane</td>" -A1 | sed "2q;d" | sed 's/[<td>|,|</td>]//g')

		DATA=$(echo -e "$DATA\t$LANER")
	done
	ALL_DATA=$(echo -e "$ALL_DATA${DATA}\\\n")
	if [ "$LANES" -gt "$PREVLANES" ];
	then
		FINALHDR=$HEADER
	fi
	PREVLANES=$LANES
done
# Get undetermined stats
UNDETERINFO=$(find $DMXDIR/Reports/html/$RUNID/default/Undetermined/unknown -name "lane.html")
UNREADS=$(grep "<td>" $UNDETERINFO | sed "4q;d" | sed 's/[<td>|,|</td>]//g')
RAWREADS=$(grep "<td>" $UNDETERINFO | sed "3q;d" | sed 's/[<td>|,|</td>]//g')
FAILEDREADS=$(($RAWREADS-$UNREADS))
READSTOT=$(($SREADSTOT+$UNREADS))
# % Failed calc
PERCENTFAILED=$(echo "scale=2; 100*$FAILEDREADS/$READSTOT" | bc)
# % Demultiplexed calculation
PERCENTDMX=$(echo "scale=2; 100*$UNREADS/$READSTOT" | bc)

write_report_file()
{
echo -e "Demultiplex stats of $RUNNAME"
echo "Generated: $(date)"
echo "------------------------------------------------------------------------------------------"
echo "$FINALHDR"
echo "$ALL_DATA" | sed 's/\\n//g'
echo "------------------------------------------------------------------------------------------"
echo "# Total Demultiplexed reads: $SREADSTOT"
echo "# Total Undetermined reads: $UNREADS"
echo "Percent Undetermined: ${PERCENTDMX}%"
echo "# Reads Failed-Filter: $FAILEDREADS"
echo "Percent Failed-Filter: ${PERCENTFAILED}%"
}

if [ ! -f $DMXDIR/${RUNNAME}_demultiplex_stats.tsv ];
then
	write_report_file >> $DMXDIR/${RUNNAME}_demultiplex_stats.tsv
fi

