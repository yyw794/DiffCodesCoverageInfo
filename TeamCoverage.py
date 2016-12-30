#!/usr/bin/python
import sys
import datetime
from subprocess import *
import re
import os
import argparse
import yaml

svn_diff_info_file_name = "svn_diff.txt"

is_py_v2 = True if sys.version[0] == '2' else False
is_linux = True if 'linux' in sys.platform else False
if is_py_v2:
	reload(sys)  
	sys.setdefaultencoding('utf8')
def exec_shell_return_all(order_list):
	if not isinstance(order_list, list):
		order_list = order_list.split()
	#p = Popen(order_list,stdout=PIPE,stderr=PIPE)
	p = Popen(order_list,stdout=PIPE,stderr=PIPE, shell=not is_linux)
	stdout_str,stderr_str = p.communicate()
	return p.returncode, stdout_str, stderr_str

def exec_shell(order_list):
	returncode, stdout_str, stderr_str = exec_shell_return_all(order_list)
	if returncode != 0:
		#I show you two ways to write to stderr
		print >> sys.stderr , ' '.join(order_list)
		sys.stderr.write(stderr_str+"\n")
		#sys.exit(p.returncode)
#print(stdout_str)
	return stdout_str

def OpenFile(FileName, OP):
	try:
		File = open(FileName, OP)	
	except IOError,e:
		print ("Failed to open File %s:%s" % (FileName, e))
		sys.exit(1)

	return File


def get_filter_files(filter_file):
	filter_files = []
	if filter_file is not None:
		with open(filter_file, "r") as f:
			filter_files = f.readlines()
		filter_files = [x.strip() for x in filter_files]
	return filter_files



def FileIsFilter(FileName, FilterFileList):
	if len(FilterFileList) == 0:
		return True	
	
	if FileName in FilterFileList:
		return True
	else:
		return False 

def WriteBlankInfo():
        Cmd = "rm -rf %s" % (coverage_folder)
        call(Cmd, shell=True)

        os.mkdir(coverage_folder)

        OutFileName = os.path.join(coverage_folder, 'index.html')

        today = datetime.date.today()
        StrList = ["<html>\n",
                "<head>\n",
                "<title> Coverage for Difference </title>\n",
                "</head>\n",
                "<body style=\"font-family:consolas;\">\n",
                "<h2> </h2>\n",
                "<h1 style=\"border:1px solid #96c2f1;background:#eff7ff\" align=\"left\">",
                "<br> Since %s 00:00:00 to now, there is no difference found. </br> </h1>\n" % (today),
                "</body>\n",
                "</html>\n",
                ]
        OutFile = OpenFile(OutFileName, "w")
        OutFile.writelines(StrList)
        OutFile.close()


def svn_diff_info(DiffFileName, conf):
	svn_diff_str = exec_shell(['svn','diff','--no-diff-deleted','-r',"{{{}}}:HEAD".format(conf["base_date"]),conf["svn_url"]])
	#'' or None ?
	return svn_diff_str


def parse_svn_diff_info(svn_diff_str, filter_files):
	StartLine = -1 
	FileValid = 0
	diff_info_dict = {}
	svn_diff_lines = svn_diff_str.split('\n')

	for l in svn_diff_lines:
		reobj =  re.match("Index:(.*)", l)
		if reobj:
			FileName = reobj.group(1).strip()
			FileName = FileName.split(":")[-1].split("/")[-1]
			
			FileValid = 0	
			if FileIsFilter(FileName, filter_files):
				FileValid = 1 				
				diff_info_dict[FileName] = [] 

			continue

		if l[:3] == '+++' or l[:3] == '---' or re.match("[=]+$", l):
			continue
	
		if FileValid == 0:
			continue

		reobj = re.match("@@ -(.*),(.*) \+(.*),(.*) @@", l)
		if reobj:
			StartLine = int(reobj.group(3))
			#print "First: %d" % (StartLine)
			continue

		#print "%c: %d" % (l[0],StartLine)
		if l[0] == '+':
			if FileName in diff_info_dict:
				diff_info_dict[FileName].append(StartLine)	

		if l[0] != '-':
			StartLine += 1

	return diff_info_dict


def WriteDiffInfoPerFile(TNName, InfoDict):
	if len(InfoDict) == 0:
		return ''

	#TODO: tell what is TN DA LF LH
	user_diff_info = "TN:{}\n".format(TNName)

	for k, value in InfoDict.iteritems():
		LFCount, LHCount = 0
		for l in value:
			if l[:3] == "DA:":
				seq = l.strip().split(":")[-1].split(",")
				LFCount += 1 		
				LHCount += int(seq[-1]) > 0
			else if(l.strip() == "end_of_record"):
				user_diff_info += "LF:{}\n".format(LFCount)
				user_diff_info += "LH:{}\n".format(LHCount)
			user_diff_info += l
			
	return user_diff_info


def write_user_coverage_info(coverage_info, DiffDict, user, user_lines):
	InfoDict = {}
	
	DiffInfoOut = os.path.join(coverage_folder, coverage_diff_file)
	DiffInfoOutFile = OpenFile(DiffInfoOut, "w")

	DiffInfoInFile = OpenFile(coverage_info, "r") 
	DiffInfoInFileIter = iter(DiffInfoInFile)

	TNName = ""

	for l in DiffInfoInFileIter:
		if l[:3] == "TN:":
			WriteDiffInfoPerFile(DiffInfoOutFile,TNName,InfoDict)
			TNName = l[3:].strip()
			InfoDict = {}
	
		if l[:3] == "SF:":
			SF = l.strip().split(":")[-1].split("/")[-1]
			if SF in DiffDict:
				InfoDict[SF] = []	
				InfoDict[SF].append(l)	
	
			while(l.strip() != "end_of_record"):
				if SF in InfoDict:
					if l[:3] == "DA:":
						Line = int(l.strip().split(":")[-1].split(",")[0])
						if Line in DiffDict[SF] and (user is None or Line in user_lines[SF]):
							InfoDict[SF].append(l)
				l = DiffInfoInFileIter.next()
			else:
				if SF in InfoDict:
					if len(InfoDict[SF]) > 1:
						InfoDict[SF].append(l)
					else:
						del InfoDict[SF]
	else:
		WriteDiffInfoPerFile(DiffInfoOutFile,TNName,InfoDict)
				
	DiffInfoInFile.close()
	DiffInfoOutFile.close()
	
	FileLen = os.stat(DiffInfoOut).st_size
	if FileLen == 0:
		print("No diff info")
		os.remove(DiffInfoOut)
		WriteBlankInfo()
		sys.exit(0)
	else:
		for each in os.listdir(coverage_folder):
			if each == coverage_diff_file or each == svn_diff_info_file_name:
				continue
			os.system("rm -rf {}".format(each))
		#Cmd = "cd {} && shopt -s extglob && rm -rf !({}|{})".format(coverage_folder, coverage_diff_file, svn_diff_info_file_name)
		genhtml_output = exec_shell(['genhtml','-o',coverage_folder, DiffInfoOut])
		return genhtml_output

def parse_conf():
	conf = yaml.load(file('CoverageDifference.yaml'))
	if conf["users"] is None:
		#log error
		sys.exit(1)
	print(conf)
	return conf
	'''
	
	coverage_info = conf["coverage_info"]
	svn_url = conf["svn_url"]
	base_time = conf["base_time"]
	users = conf["users"]
	filter_file = conf["filter_file"]
	'''

def get_all_c_files(svn_url):
	cmd = "svn list --depth infinity {}".format(svn_url)
	files = exec_shell(cmd)
	#print(files)
	files = files.split('\n')

	c_files = []
	for each in files:
		if '.c' in each:
			c_files.append(each)
	return c_files

def get_user_LOC(svn_url, user):
	all_c_files = get_all_c_files(svn_url)

	user_lines = {}
	for c_file in all_c_files:
		c_file_name = os.path.basename(c_file)
		user_lines[c_file_name]=[]

		c_file_svn_url = os.path.join(svn_url, c_file)
		ret = exec_shell(['svn','blame', '-v', c_file_svn_url])
		ret = ret.split('\n')

		for sn, line in enumerate(ret):
			if line == '':
				continue
			line_sn = sn+1

			svn_ver, committer = line.split()[0:2]

			if user in committer:
				user_lines[c_file_name].append(line_sn)

	return user_lines

def main():
	#filter_file, BaseTime, coverage_all_file, svn_url, user = parse_input()
	conf = parse_conf()

	for user in conf["users"]:
		user_lines = get_user_LOC(conf["svn_url"], user) 

		svn_diff_str = svn_diff_info(conf)

		diff_info_dict = parse_svn_diff_info(svn_diff_str, conf["filter_files"])

		#TODO: combine this to the following
		if diff_info_dict == {}:
			WriteBlankInfo()
			sys.exit(0)	

		genhtml_output = write_user_coverage_info(conf["coverage_info"], diff_info_dict, user, user_lines)

	#TODO:get coverage rate and write it to file and show 


if __name__ == '__main__':
	parse_conf()
	#main()
