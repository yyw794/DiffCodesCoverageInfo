#!/usr/bin/python
import sys
import datetime
from subprocess import *
import re
import os
import argparse
import yaml

is_py_v2 = True if sys.version[0] == '2' else False
is_linux = True if 'linux' in sys.platform else False
if is_py_v2:
	reload(sys)  
	sys.setdefaultencoding('utf8')

#content of conf.yaml
global conf

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

def file_should_be_ingored(file_name, filter_files):
	return True if filter_files is None or file_name in filter_files else False

def write_blank_html():
        html_path = os.path.join(coverage_folder, 'index.html')

        content = '''
        <html>
        	<head>
            	<title> Coverage for Difference </title>
            </head>
            <body style="font-family:consolas;">
                <h2> </h2>
                <h1 style="border:1px solid #96c2f1;background:#eff7ff" align="left"
                <br> Since {} 00:00:00 to now, there is no difference found. </br>
                </h1>
            </body>
        </html>'''.format(datetime.date.today())

        with open(html_path, 'w') as f:
        	f.write(content)

def output_svn_diff_info():
	'''
	do not include the files which are deleted
	'''
	svn_diff_info = exec_shell(['svn','diff','--no-diff-deleted','-r',"{{{}}}:HEAD".format(conf["base_date"]),conf["svn_url"]])
	return svn_diff_str

def keep_interest_svn_diff_info(svn_diff_info):
	file_name_symbol = "Index:"
	interest_svn_diff_info = ''
	blocks_by_file = svn_diff_info.split(file_name_symbol)
	for block in blocks_by_file:
		file_name = block.splitlines()[0].strip()
		if not file_should_be_ingored(file_name, filter_files):
			interest_svn_diff_info += file_name_symbol
			interest_svn_diff_info += block
	return interest_svn_diff_info

def get_new_lines_no_in_each_file(svn_diff_info):
	'''
	svn diff info just like this:
	Index: unit_test.sh
	===================================================================
	--- unit_test.sh	(revision 36)
	+++ unit_test.sh	(revision 802)
	@@ -1,16 +1,8 @@
	...

	explaination:
	@@(old version) start_line, lines_count, (new version) start_line, lines_count@@

	only add new lines no of each file to the output
	'''
	added_line_no = -1 
	user_new_lines = {}
	svn_diff_lines = svn_diff_info.splitlines()
	file_name_symbol = "Index:"

	for l in svn_diff_lines:
		if l.startswith(file_name_symbol):
			file_name = os.path.basename(l[len(file_name_symbol):])
			user_new_lines[file_name] = []
		else if l[:3] == '+++' or l[:3] == '---' or re.match("[=]+$", l):
			continue
		else if re.match("@@ -(.*),(.*) \+(.*),(.*) @@", l)
			added_line_no = int(reobj.group(3))
		else if l.startswith('+'):
			user_new_lines[file_name].append(added_line_no)
		else if l.startswith(' '):
			start_line += 1

	return user_new_lines


def user_diff_info_per_file(TN_name, InfoDict):
	if len(InfoDict) == 0:
		return ''

	#TODO: tell what is TN DA LF LH
	user_diff_info = "TN:{}\n".format(TN_name)

	for k, value in InfoDict.iteritems():
		LF_count, LH_count = 0
		for l in value:
			if l[:3] == "DA:":
				seq = l.strip().split(":")[-1].split(",")
				LF_count += 1 		
				LH_count += int(seq[-1]) > 0
			else if(l.strip() == "end_of_record"):
				user_diff_info += "LF:{}\n".format(LF_count)
				user_diff_info += "LH:{}\n".format(LH_count)
			user_diff_info += l

	return user_diff_info

def make_user_coverage_info(user, user_new_lines, user_all_lines):
	'''
	SF: file name
	'''
	coverage_info_path = os.path.join(conf["coverage_folder"], conf["coverage_info"])
	with open(coverage_info_path, 'r') as f:
		coverage_info_lines = f.readlines()

	TN_name = ""
	user_diff_info = ""

	for l in coverage_info_lines:
		# TN means a new file parse
		if l.startswith("TN:"):
			TN_name = l[3:].strip()
			user_diff_info += user_diff_info_per_file(TN_name,InfoDict)
			coverage_lines = {}
		else if l.startswith("SF:"):
			file_name = os.path.basename(l[3:])
			#user_new_lines = {"xx.file":[2,4,5...],"yy.file":[1,2,3]}
			if file_name in user_new_lines:
				coverage_lines[file_name] = []	
				coverage_lines[file_name].append(l)	
	
			while(l.strip() != "end_of_record"):
				if file_name in coverage_lines:
					if l.startswith("DA:"):
						line_no = int(l[3:].split(",")[0])
						if line_no in user_new_lines[file_name] and (user is None or line_no in user_lines[file_name]):
							coverage_lines[file_name].append(l)
			else:
				if file_name in coverage_lines:
					if len(coverage_lines[file_name]) > 1:
						coverage_lines[file_name].append(l)
					else:
						del coverage_lines[file_name]
	else:
		user_diff_info += user_diff_info_per_file(TN_name,coverage_lines)	

	return user_diff_info


def create_user_coverage_info(user, user_new_lines, user_all_lines):
	user_diff_info = make_user_coverage_info(user, user_new_lines, user_all_lines)

	user_coverage_info_path = os.path.join(coverage_folder, user+coverage_info)
	with open(user_coverage_info_path, "w") as f:
		f.write(user_diff_info)	

	return user_coverage_info_path


def parse_conf():
	configure_file = 'Configure.yaml'
	global conf
	conf = yaml.load(file(configure_file))
	print(conf)
	if conf["users"] is None:
		print("you should add users in {}".format(configure_file))
		#log error
		sys.exit(1)

def get_c_files(svn_url):
	cmd = "svn list --depth infinity {}".format(svn_url)
	files = exec_shell(cmd).splitlines()

	c_files = [x for x in files if '.c' in x]

	return c_files

def get_user_LOC(user):
	'''
	dict info is  which c file contains which line belongs to the user
	using svn blame command
	'''
	svn_url = conf["svn_url"]
	all_c_files = get_c_files(svn_url)

	user_lines = {}
	for c_file in all_c_files:
		c_file_name = os.path.basename(c_file)
		user_lines[c_file_name]=[]

		c_file_svn_url = os.path.join(svn_url, c_file)
		svn_blame_info = exec_shell(['svn','blame', '-v', c_file_svn_url]).splitlines()

		for sn, line in enumerate(svn_blame_info):
			if line == '':
				continue
			line_sn = sn+1

			svn_ver, committer = line.split()[0:2]

			if user in committer:
				user_lines[c_file_name].append(line_sn)

	return user_lines

def user_coverage_info_2_html(user, user_coverage_info_path):
	'''
	each user has its own folder which contains index.html
	'''
	if os.stat(user_coverage_info_path).st_size == 0:
		write_blank_html()
	#genhtml will mkdir output folder if not exists
	exec_shell(['genhtml','-o',conf["coverage_info"]+user, user_coverage_info_path])

def write_user_html(user):
	user_all_lines = get_user_LOC(user) 

	svn_diff_info = output_svn_diff_info()
	interest_svn_diff_info = keep_interest_svn_diff_info(svn_diff_info)
	user_new_lines = get_new_lines_no_in_each_file(interest_svn_diff_info)

	user_coverage_info_path = create_user_coverage_info(user, user_new_lines, user_all_lines)
	user_coverage_info_2_html(user, user_coverage_info_path)

def main():
	parse_conf()

	for user in conf["users"]:
		write_user_html()

if __name__ == '__main__':
	main()