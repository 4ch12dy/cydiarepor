import requests
#import wget
import sys
import shlex
import optparse

def http_get(url):
	r = requests.get(url, stream=True)
	return r

def get_cydiarepo_packages(repoURL):
#	Package: com.archry.joker
#	Version: 1.0.30-1+debug
#	Architecture: iphoneos-arm
#	Installed-Size: 588
#	Depends: mobilesubstrate
#	Filename: ./debs/com.archry.joker.deb.deb
#	Size: 117922
#	MD5sum: c5d30e1b10177190ee56eecf5dbb5cfe
#	SHA1: 377d5c59926083b2acdd95028abe24edfeba6141
#	SHA256: fcb97af34c56d4a2bd67540df0427cb0cbd9b68e4c4e78f555265c3db1e2b67e
#	Section: Hack
#	Description: Archery king hack winde , zoom  and better Aiming
#	Author: @Kgfunn
#	Depiction: https://joker2gun.github.io/depictions/?p=com.archry.joker
#	Name: Archery King Hack
	cydiarepo_Packages_URL = repoURL + '/Packages'
	r = requests.get(cydiarepo_Packages_URL)

	raw_packages_string = r.content
	raw_packages_list = raw_packages_string.split("\n\n")

	all_deb = []
	for raw_package_string in raw_packages_list:
		raw_deb_list = raw_package_string.split("\n")
		cur_deb = {}
		for raw_deb_str in raw_deb_list:
			deb_item = raw_deb_str.split(":")

			if len(deb_item) != 2:
				continue
			deb_item_k = deb_item[0].strip()
			deb_item_v = deb_item[1].strip()
			
			need_item_array = ["Package", "Version", "Filename", "Name", "Description"]
			if deb_item_k in need_item_array:
				cur_deb[deb_item_k] = deb_item_v

		if cur_deb:
			all_deb.append(cur_deb)
	
	return all_deb
	
def is_need_by_search_string(deb, contained_str):
	name = deb['Name']
	package = deb['Package']
	description = ''
	if deb.has_key('Description'):
		description = deb['Description']
	
	if contained_str in description:
		return True
	
	if contained_str in name or contained_str in package:
		return True
	
	return False


def download_deb_file(repo_url, deb):
	deb_download_url = repo_url + deb['Filename'][1:]
	save_path = "./" + deb['Package'] + "_"+ deb['Version'] + ".deb"
	
	r = http_get(deb_download_url)
	deb_data = r.content
	with open(save_path, 'wb') as f:
		f.write(deb_data)
#	wget.download(deb_download_url, save_path)

def list_all_repo_deb(repo_url):
	debs = get_cydiarepo_packages(repo_url)
	print("-"*(3+30+30+4))
	print("|"+format("N", "^3") + "|" + format("package", "^30")+"|"+format("name", "^30")+"|")
	print("-"*(3+30+30+4))
	for i in range(len(debs)):
		if (i+1) % 40 == 0:
			print("|"+format(i,"<3")+"|" + format(debs[i]["Package"], "^30")+ "|" + format(debs[i]["Name"], "^30") + "|")
			print("-"*(3+30+30+4))
			choice = input("|" + "do you want to continue?[1/0]: ")
			print("-"*(3+30+30+4))
			
			if choice == 0:
				break
			elif choice == 1:
				continue
			else:
				print("[-] error choice")
				exit(1)
			

		print("|"+format(i,"<3")+"|" + format(debs[i]["Package"], "^30")+ "|" + format(debs[i]["Name"], "^30") + "|")
	
	print("-"*(3+30+30+4))
	
def list_deb(debs):
	print("-"*(3+30+30+4))
	print("|"+format("N", "^3") + "|" + format("package", "^30")+"|"+format("name", "^30")+"|")
	print("-"*(3+30+30+4))
	for i in range(len(debs)):
		print("|"+format(i,"<3")+"|" + format(debs[i]["Package"], "^30")+ "|" + format(debs[i]["Name"], "^30") + "|")
	print("-"*(3+30+30+4))
	
def generate_option_parser():
	usage = "[usage]: cydiarepor cydiarepo_url -s search_string -l"
	parser = optparse.OptionParser(usage=usage, prog="lookup")

	parser.add_option("-l", "--list",
						action="store_true",
						default=None,
						dest="listdeb",
						help="list all deb package of cydia repo")

	parser.add_option("-s", "--string",
				action="store",
				default=None,
				dest="searchstring",
				help="search deb by string")
				
	return parser

if __name__ == "__main__":		
	cydiarepoURL = ''
	parser = generate_option_parser()
	
	command_args = sys.argv[1:]
	if len(command_args) == 0:
		print(parser.usage)
		exit(1)
	
	try:
		(options, args) = parser.parse_args(command_args)
	except:
		print(parser.usage)
		exit(1)
		
	if options.listdeb:
		cydiarepoURL = args[0]
		list_all_repo_deb(cydiarepoURL)
		exit(0)
	
	if options.searchstring:
		need_debs = []
		search_string = options.searchstring
		cydiarepoURL = args[0]
		debs = get_cydiarepo_packages(cydiarepoURL)
		for deb in debs:
			if is_need_by_search_string(deb, search_string):
				need_debs.append(deb)
		
		list_deb(need_debs)
		num = input(">> inout number of deb want to download:")
		
		print("[*] you choose {} deb:\"{}\"".format(num, need_debs[num]['Name']))
		
		print("[*] start to download:{}".format(need_debs[num]['Name']))
		
		download_deb_file(cydiarepoURL, need_debs[num])
		
		print("[+] download deb done")
			
	