import sys
import json
import os
import requests
from bs4 import BeautifulSoup
from artifactory import ArtifactoryPath


NOOS_PATH = sys.argv[1]
BUILD_PATH = sys.argv[2]
HDL_SERVER_BASE_PATH = sys.argv[3]
NEW_HW_DIR_NAME = 'new_hardware'
FOLDERS_NR = 30 #number of folders to check for missing hardware file

list_hardware = []
for dir in os.listdir(NOOS_PATH + '/projects'):
    file = NOOS_PATH + '/projects/' + str(dir) + '/builds.json'
    if os.path.exists(file):
        with open(file) as f:
            data = json.load(f)
        for (platform, config) in data.items():
            for (build_name, params) in config.items():
                if 'hardware' in params:
                    for hardware_value in params['hardware']:
                        list_hardware.append(hardware_value)

new_harware_dir= os.path.join(BUILD_PATH, NEW_HW_DIR_NAME)
soup = BeautifulSoup(requests.get(HDL_SERVER_BASE_PATH).content, 'html.parser')
latest = str(soup).split("\n")[-3].split(" ")[1].split('/">')[1].split('/')[0]
release_link = HDL_SERVER_BASE_PATH + "/" + latest + "/"
unique_hardware_list = set(list_hardware)
os.system("rm -rf %s/*" % (new_harware_dir))
for hardware in unique_hardware_list:
    FOUND = False
    file_path = release_link + hardware + "/system_top.xsa"
    if requests.get(file_path, stream=True).status_code == 200:
        os.system("mkdir -p %s" % (str(new_harware_dir) + '/' + hardware))
        os.system("wget -q -nv -P %s %s" % (str(new_harware_dir) + '/' + hardware, file_path))
        FOUND = True
    else:
        print("Missing " + hardware + " from latest timestamp " + latest)
        artifactory_lines = str(soup).split("\n")
        for line_number in range(-4, -FOLDERS_NR-4, -1) :
            line = artifactory_lines[line_number]
            if 'href=' in line and '<pre>' not in line:
                timestamp_folder = line.split(" ")[1].split('/">')[1].split('/')[0]
                d_path = HDL_SERVER_BASE_PATH + "/" + timestamp_folder + "/" + hardware + "/system_top.xsa"
                if requests.get(d_path, stream=True).status_code == 200:
                    os.system("mkdir -p %s" % (str(new_harware_dir) + '/' + hardware))
                    os.system("wget -q -nv -P %s %s" % (str(new_harware_dir) + '/' + hardware, d_path))
                    if sys.version_info[:2] <= (3, 8):
                        #get_properties works just with python3.8 or older versions
                        timestamp_folder_info = str(ArtifactoryPath(HDL_SERVER_BASE_PATH + "/" + timestamp_folder).properties)
                        folder_git_sha = timestamp_folder_info.split('[')[2].split(']')[0]
                        folder_commit_date = timestamp_folder_info.split('[')[1].split(']')[0]
                        print("Hardware " + hardware + " found on next timestamp " + timestamp_folder + " with next properties git sha: " + \
                            str(folder_git_sha) + " commit date: " + str(folder_commit_date))
                    else:
                        print("Hardware " + hardware + " found on next timestamp " + timestamp_folder)
                    FOUND = True
                    break
            else:
                break
    if FOUND is False:
        print("Project " + hardware + " was not found on server")
