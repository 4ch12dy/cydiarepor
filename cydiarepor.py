import requests
#import wget
import sys
import shlex
import optparse
import gzip
import StringIO
import bz2
import urlparse


def get_default_cydia_repo_array():
    default_repos = []
    # BigBoss of coolstar
    default_repos.append("https://repounclutter.coolstar.org")
    default_repos.append("https://repo.chimera.sh")
    default_repos.append("https://build.frida.re")
    default_repos.append("https://coolstar.org/publicrepo")
    default_repos.append("https://apt.bingner.com")
    default_repos.append("https://xia0z.github.io")
    
    return default_repos
    
    
def handle_old_cydia_repo(url):
    parse_result = urlparse.urlparse(url)
    scheme = '{uri.scheme}'.format(uri=parse_result)
    url = url[len(scheme):]
    
    old_BigBoss_repo = "://apt.thebigboss.org/repofiles/cydia"
    old_bingner_repo = "://apt.bingner.com"
    repo_package_url = ""
    zip_type = ""
    ret = []
    
    if url == old_BigBoss_repo:
        repo_package_url = scheme+old_BigBoss_repo + "/dists/stable/main/binary-iphoneos-arm/Packages.bz2"
        zip_type = "bz2"
        ret.append(repo_package_url)
        ret.append(zip_type)
    elif url == old_bingner_repo:
        repo_package_url = scheme+old_bingner_repo + "/dists/ios/1443.00/"+"main/binary-iphoneos-arm/Packages.bz2"
        zip_type = "bz2"
        ret.append(repo_package_url)
        ret.append(zip_type)
    else:
        ret = None

    return ret
    
def is_url_reachable(url):
    r = requests.get(url, allow_redirects = False)
    status = r.status_code
    
    if status == 200:
        return True
    
    return False
    
def unzip_data_to_string(data, unzip_type):
    unzip_string = ""
    if unzip_type == "gz":
        compressedstream = StringIO.StringIO(data)
        gziper = gzip.GzipFile(fileobj=compressedstream)
        unzip_string = gziper.read()
    elif unzip_type == "bz2":
        unzip_string = bz2.decompress(data)
    else:
        print("[-] unkown zip type!")
        exit(1)
    
    return unzip_string
    
def http_get(url):
    r = requests.get(url, stream=True)
    return r

def get_cydiarepo_packages(repoURL):
#    Package: com.archry.joker
#    Version: 1.0.30-1+debug
#    Architecture: iphoneos-arm
#    Installed-Size: 588
#    Depends: mobilesubstrate
#    Filename: ./debs/com.archry.joker.deb.deb
#    Size: 117922
#    MD5sum: c5d30e1b10177190ee56eecf5dbb5cfe
#    SHA1: 377d5c59926083b2acdd95028abe24edfeba6141
#    SHA256: fcb97af34c56d4a2bd67540df0427cb0cbd9b68e4c4e78f555265c3db1e2b67e
#    Section: Hack
#    Description: Archery king hack winde , zoom  and better Aiming
#    Author: @Kgfunn
#    Depiction: https://joker2gun.github.io/depictions/?p=com.archry.joker
#    Name: Archery King Hack
    
    cydiarepo_Packages_URL = repoURL + '/Packages'
    cydiarepo_Packages_bz2_URL = repoURL + '/Packages.bz2'
    cydiarepo_Packages_gz_URL = repoURL + '/Packages.gz'
    
    if handle_old_cydia_repo(repoURL):
        ret = handle_old_cydia_repo(repoURL)
        zip_type = ret[1]
        if zip_type == "gz":
            cydiarepo_Packages_gz_URL = ret[0]
        elif zip_type == "bz2":
            cydiarepo_Packages_bz2_URL = ret[0]
        else:
            print("[-] unknown old cydia repo zip type")
            exit(1)
    
    cydiarepo_reachable_URL = ''
    is_need_unzip = False
    unzip_type = ''
    
    if is_url_reachable(cydiarepo_Packages_URL):
        cydiarepo_reachable_URL = cydiarepo_Packages_URL
    elif is_url_reachable(cydiarepo_Packages_bz2_URL):
        cydiarepo_reachable_URL = cydiarepo_Packages_bz2_URL
        is_need_unzip = True
        unzip_type = "bz2"
        
    elif is_url_reachable(cydiarepo_Packages_gz_URL):
        cydiarepo_reachable_URL = cydiarepo_Packages_gz_URL
        is_need_unzip = True
        unzip_type = "gz"
    else:
        print("[-] {} repo not found Packages or Packages.bz2 or Packages.gz file, check it!".format(repoURL))
        exit(1)

    r = requests.get(cydiarepo_reachable_URL)
    raw_packages_data = r.content
    raw_packages_string = ""
    
    if is_need_unzip:
        raw_packages_string = unzip_data_to_string(raw_packages_data, unzip_type)
    else:
        raw_packages_string = raw_packages_data
    
    raw_packages_list = raw_packages_string.split("\n\n")
    
    repo_info = {"url":repoURL}
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
            
            for k in need_item_array:
                if not cur_deb.has_key(k):
                    cur_deb[k] = ""
            
            cur_deb["repo"]=repo_info

        if cur_deb:
            all_deb.append(cur_deb)
    
    return all_deb
    
    
def get_debs_in_default_cydia_repo():
    default_repo_ulrs = get_default_cydia_repo_array()
    defult_debs = []
    
    for url in default_repo_ulrs:
        debs = get_cydiarepo_packages(url)
        defult_debs += debs
        
    return defult_debs
    
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
    deb_download_url = repo_url + "/./" + deb['Filename']
    save_path = "./" + deb['Package'] + "_"+ deb['Version'] + ".deb"
    
    r = http_get(deb_download_url)
    deb_data = r.content
    with open(save_path, 'wb') as f:
        f.write(deb_data)
#	wget.download(deb_download_url, save_path)

def list_all_repo_deb(debs):
    print("-"*(3+30+30+4))
    title = "Developed By xia0@2019 Blog:https://4ch12dy.site"
    print("|"+format(title,"^65")+"|")
    
    print("-"*(3+30+30+4))
    total_str = "Total:{}".format(len(debs))
    print("|"+format(total_str,"^65")+"|")
    print("-"*(3+30+30+4))
    print("|"+format("N", "^3") + "|" + format("package", "^30")+"|"+format("name", "^30")+"|")
    print("-"*(3+30+30+4))
    for i in range(len(debs)):
        if (i+1) % 40 == 0:
            print("|"+format(i,"<3")+"|" + format(debs[i]["Package"], "^30")+ "|" + format(debs[i]["Name"]+"("+debs[i]["Version"]+")", "^30") + "|")
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
    com_item_wid = 30
    total_wid = 1+3+ (com_item_wid +1) *3 + 1
    
    print("-"*total_wid)
    print("|"+format("N", "^3") + "|" + format("package", "^30")+"|"+format("name", "^30")+"|"+format("repo url", "^30")+"|")
    print("-"*total_wid)
    for i in range(len(debs)):
        print("|"+format(i,"<3")+"|" + format(debs[i]["Package"], "^30")+ "|" + format(debs[i]["Name"]+"("+debs[i]["Version"]+")", "^30") + "|" + format(debs[i]["repo"]["url"], "^30") + "|")
    
    print("-"*total_wid)
    
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
                
    parser.add_option("-d", "--default",
                action="store_true",
                default=None,
                dest="defaultrepos",
                help="search deb by string in default repos")
                
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
        
    if options.defaultrepos:
        if options.searchstring:
            need_debs = []
            search_string = options.searchstring

            debs = get_debs_in_default_cydia_repo()
            for deb in debs:
                if is_need_by_search_string(deb, search_string):
                    need_debs.append(deb)
            
            list_deb(need_debs)
            num = input(">> inout number of deb want to download:")
            
            print("[*] you choose {} deb:\"{}\"".format(num, need_debs[num]['Name']))
            
            print("[*] start to download:{}".format(need_debs[num]['Name']))
            cydiarepoURL = need_debs[num]["repo"]["url"]
            download_deb_file(cydiarepoURL, need_debs[num])
            
            print("[+] download deb done")
            exit(0)
            
        if options.listdeb:
            all_defualt_debs = []
            
            for url in get_default_cydia_repo_array():
                debs = get_cydiarepo_packages(url)
                all_defualt_debs += debs
            
            list_all_repo_deb(all_defualt_debs)
            exit(0)
        
    if options.listdeb:
        cydiarepoURL = args[0]
        debs = get_cydiarepo_packages(cydiarepoURL)
        list_all_repo_deb(debs)
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
        exit(0)
            
    print("[-] you can not reach here!!!")
    