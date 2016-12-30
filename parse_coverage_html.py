# encoding=utf8 
import os
from bs4 import BeautifulSoup
#jenkins job has env var ${WORKSPACE}, if you are in debug mode, you set this and then run 
ut_folder = os.path.join(os.getenv('WORKSPACE'), 'unittest')

#CHANGE by your project
person_ids = {'10064088':'严勇文','10072341':'陈振','10114492':'汪勇','10164269':'吴来强','00190995':'龙明星'}
#CHANGE by your project, the output file
team_coverage_file = os.path.join(ut_folder, 'team_cov.txt')
#CHANGE by your project, how to get your team members' index.html which is from genhtml
def get_persons_html_path():
	person_cov_html = {}
	for each in person_ids:
		person_coverage_folder = os.path.join(ut_folder,'coveragediff'+each)
		if os.path.exists(os.path.join(person_coverage_folder,'coverage_diff.info')):
			index_html = os.path.join(person_coverage_folder, 'index.html')	
			person_cov_html[each] = index_html
	return person_cov_html


def __parse_coverage_info_from_html(target_html):
	cov_info = {}
	with open(target_html, "r") as f:
		lines = f.read()
	soup=BeautifulSoup(lines,'html.parser')
	
	for each_tr in soup.find_all('tr'):
		tds = each_tr.find_all('td')
		for i, each_td in enumerate(tds):
			if 'class' in each_td.attrs and each_td.string is not None and each_td.string in ('Lines:', 'Functions:'):
				cov_info[each_td.string] = (tds[i+1].string, tds[i+2].string, tds[i+3].string)
	
	return cov_info

def persons_coverage_from_htmls(person_cov_html):
	coverage_info = {}
	for person_id in person_ids:
		if person_id in person_cov_html:
			coverage_info[person_id]= __parse_coverage_info_from_html(person_cov_html[person_id])
	return coverage_info	

def __cal_color(line_cov, line_all):
	color = 'green' if float(line_cov)/line_all >= 0.8 else 'red'
	return color

def __cal_output_line(who, color, cov_percent, line_cov, line_all):
	line = "h3. {}:   {{color:{}}}{} ({}/{}){{color}}\n".format(who, color, cov_percent, line_cov, line_all)
	return line
def write_confluence_file(coverage_info):
	lines = []
	team_cov = 0
	team_all = 0
	for person_id in person_ids:
		if person_id in coverage_info:
			person_cov = coverage_info[person_id]
			line_cov, line_all, cov_percent = person_cov['Lines:']
			line_cov = int(line_cov)
			line_all = int(line_all)
			team_cov = team_cov + line_cov
			team_all = team_all + line_all
			#func_cov, func_all, func_percent = person_cov['Functions:']
			color = __cal_color(line_cov, line_all)
			line = __cal_output_line(person_ids[person_id], color, cov_percent, line_cov, line_all)
			lines.append(line)

	team_percent = "{:.1%}".format(float(team_cov)/team_all)
	team_color = __cal_color(team_cov, team_all)

	team_line = __cal_output_line('team', team_color, team_percent, team_cov, team_all)
	lines.append(team_line)
	print(lines)

	with open(team_coverage_file,"w") as f:
		f.writelines(lines)


def main():
	persons_html = get_persons_html_path()
	coverage_info = persons_coverage_from_htmls(persons_html)
	write_confluence_file(coverage_info)


if __name__ == '__main__':
	main()

