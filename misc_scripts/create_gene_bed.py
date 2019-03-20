#!/apps/bio/software/anaconda2/envs/mathias_general/bin/python3.6
import os
import argparse


def get_data(transcriptinfo, keep_cols_dict):
	t_transcript = transcriptinfo[keep_cols_dict["name"]]
	t_strand = transcriptinfo[keep_cols_dict["strand"]]
	t_start = transcriptinfo[keep_cols_dict["txStart"]]
	t_stop = transcriptinfo[keep_cols_dict["txEnd"]]
	t_chrom = transcriptinfo[keep_cols_dict["chrom"]]
	return t_transcript, t_strand, int(t_start), int(t_stop), t_chrom

def expand_regions(expand, start, stop):
	start -= expand
	stop += expand
	return int(start), int(stop)

def refseq_gene(gtf, expand):
	with open(gtf, 'r') as refgtf:
		header = refgtf.readline().split("\t")
		keep_cols = ["name", "chrom", "strand", "txStart", "txEnd", "name2"]
		keep_cols_dict = {}
		for keepcol in keep_cols:
			for colnumber, column in enumerate(header):
				if column == keepcol:
					keep_cols_dict.update({keepcol:colnumber})


		genelist = []
		
		# Get First Line
		first_line = refgtf.readline().split("\t")
		t_transcript, t_strand, t_start, t_stop, t_chrom = get_data(first_line, keep_cols_dict)	
		gene = first_line[keep_cols_dict["name2"]]	
		g_startlist = [t_start]
		g_stoplist = [t_stop]
		g_tlist = [t_transcript]

		for transcript in refgtf:

			transcriptlist = transcript.split("\t")
			
			if gene != transcriptlist[keep_cols_dict["name2"]]:
				# New Gene Detected
				# Find longest start and stop of previous gene
				gene_start = min(g_startlist)
				gene_stop = max(g_stoplist)
				if int(expand) > 0:
					gene_start, gene_stop = expand_regions(expand, gene_start, gene_stop)
				tlist_string = ";".join(g_tlist)
				# Append Gene data to table
				gene_info = [t_chrom, gene_start, gene_stop, gene, "0", t_strand, tlist_string]
				genelist.append(gene_info)
			
				# Reset gene values	
				g_startlist = []
				g_stoplist = []
				g_tlist = []
				# Assign new Genename
				gene = transcriptlist[keep_cols_dict["name2"]]

			
			t_transcript, t_strand, t_start, t_stop, t_chrom = get_data(transcriptlist, keep_cols_dict)

			
			g_startlist.append(t_start)
			g_stoplist.append(t_stop)
			g_tlist.append(t_transcript)
		
		# End of For-loop
		# Write Last Gene
		gene_start = min(g_startlist)
		gene_stop = max(g_stoplist)
		gene_start, gene_stop = expand_regions(expand, gene_start, gene_stop)

		tlist_string = ";".join(g_tlist)
		gene_info = [t_chrom, gene_start, gene_stop, gene, "0", t_strand, tlist_string]
		genelist.append(gene_info)
	if expand == 0:
		region = "gene_regions"
	else:
		region = "expanded_%sbases" % expand

	with open(gtf + "_" + region + ".bed", "w") as refgene:
		for geneinfo in genelist:
			gene_write = "\t".join(str(x) for x in geneinfo)
			refgene.write(gene_write + "\n")







if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-g', '--refseqgtf', nargs='?', help='Input Refseq GTF file with transcripts, will output bedfile based on longest gene-region', required=True)
	parser.add_argument('-e', '--expand', nargs='?', help='expand gene-regions (+/-) with bases supplied', type=int, required=False)
	args = parser.parse_args()
	refseqgtf = args.refseqgtf
	expand = args.expand
	if expand:
		refseq_gene(refseqgtf, expand)
	else:
		refseq_gene(refseqgtf, expand=0)
