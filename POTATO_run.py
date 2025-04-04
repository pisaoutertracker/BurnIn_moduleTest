#!/usr/bin/env python3
from ROOT import TFile, TCanvas, gROOT, TH1F, TH2F, gStyle, TGraphErrors
import os
from databaseTools import getTestFromDB, getModuleTestFromDB, getRunFromDB, getModuleFromDB, makeModuleNameMapFromDB
import zipfile
from tools import getNoisePerChip, getIDsFromROOT, getResultPerModule
#from makeXml import readXmlConfig

import argparse
parser = argparse.ArgumentParser(description='Script used to run potato express test from an existing single test module. More info at https://github.com/pisaoutertracker/BurnIn_moduleTest. \n Example: python3  POTATO_run.py PS_26_IBA-10003__run500087 ')
parser.add_argument('module_test', type=str, help='Single-module test name')

module_test = parser.parse_args().module_test
version = "v1-01"
tmpFolder = "/tmp/"
scriptName = "POTATO_run.sh"
POTATOExpressFolder = "/home/thermal/potato/Express/"


skipWebdav = True
from moduleTest import verbose ## to be updated

verbose = 1000
outDir = "POTATOFiles"


def downloadAndExtractZipFile(remote_path, local_path, webdav_wrapper=None, skipWebdav=False):
    if verbose>2: print("downloadAndExtractZipFile")
    webdav_wrapper = None
    if not skipWebdav and not webdav_wrapper: 
        from moduleTest import webdav_wrapper

    # Download the zip file from the remote path
    if webdav_wrapper: 
        zip_file_path = webdav_wrapper.download_file(remote_path=run['runFile'].split("//")[-1] , local_path="/tmp/%s"%fName) ## drop
    else: zip_file_path = "/tmp/%s"%fName

    # Specify the directory where you want to extract the contents
    extracted_dir = zip_file_path.split(".")[0]

    # Open the zip file
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        # Extract all the contents into the specified directory
        zip_ref.extractall(extracted_dir)

    print("Unzipped to %s"%extracted_dir)
    return extracted_dir



#allVariables = []
gROOT.SetBatch()
gStyle.SetOptStat(0)
tmpFolder = tmpFolder+module_test+"_forPOTATO_%s/"%version
base = "/test3/"
hwToModuleID, hwToMongoID = makeModuleNameMapFromDB()

test = getModuleTestFromDB(module_test)
runName = test['test_runName']
moduleName = test['moduleName']
run = getRunFromDB(runName)
fName = run['runFile'].split("//")[-1].replace("/", "_")
run = getRunFromDB(runName)

remote_path=run['runFile'].split("//")[-1]
local_path="/tmp/%s"%fName

extracted_dir = downloadAndExtractZipFile(remote_path, local_path, skipWebdav=skipWebdav)


###############################################################################################

resultsFile = extracted_dir + "/Results.root"
## Get monitorDQM file
monitorDQMFile = None
for file in os.listdir(extracted_dir):
    if file.startswith("MonitorDQM_") and file.endswith(".root"):
        monitorDQMFile = os.path.join(extracted_dir, file)
        break


runNumber = test['test_runName']
moduleBurninName = "Module4L"
moduleCarrierName = "ModuleCarrier4Left"
opticalGroup = str(test['opticalGroupName'])

module_name = test['moduleName']
date = run['runDate']
from datetime import datetime
#datetimeParsed = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")
from updateTestResult import getTemperatureAt, getTimeFromRomeToUTC
dateTime_rome, dateTime_utc = getTimeFromRomeToUTC(date)

temp = getTemperatureAt(dateTime_utc.isoformat("T").split("+")[0] , sensorName="Temp0")
#formatted_temp = format(temp, "+.1f")
formatted_temp = format(int(temp), "+d")
formatted_date = dateTime_rome.strftime("%Y-%m-%d_%Hh%Mm%Ss")
runType = run['runType']
tag = version

#PS_16_FNL-00002_2024-09-15_11h42m33s_+15C_PSfullTest_v1-01.root
#PS_26_IBA-10003_2025-04-04_11h34m04s_+20C_PSfullTest_v1-01.root
rootTrackerFileName = outDir + "/" + f"{module_name}_{formatted_date}_{formatted_temp}C_{runType}_{tag}.root"

## Merge Results and MonitorDQM files
from POTATO_mergeFile import mergeTwoROOTfiles
print("Merged file created:", rootTrackerFileName)

## Run potatoconverter (or formatter)
from POTATO_PisaFormatter import POTATOPisaFormatter as Formatter
mergeTwoROOTfiles(resultsFile, monitorDQMFile, rootTrackerFileName)
theFormatter = Formatter(outDir)
theFormatter.do_burnin_format(rootTrackerFileName, runNumber, opticalGroup, moduleBurninName, moduleCarrierName)

############### Prepare a script to run POTATO

rootTrackerPath = os.path.abspath(rootTrackerFileName)
script = f""" cd {POTATOExpressFolder}
source ../setupPotato.sh
export POTATODIR={POTATOExpressFolder}
mkdir -p backup
mv data/LocalFiles/TestOutput/* backup
mv data/LocalFiles/DropBox/* backup
mv data/ReferenceFiles/* backup

cp {rootTrackerPath} data/LocalFiles/TestOutput
cp {rootTrackerPath} data/LocalFiles/DropBox
cp {rootTrackerPath} data/ReferenceFiles

## Compile POTATO express, if necessary
#./compile.py

## Run POTATO express
./PotatoExpress
"""

scriptPath = "%s/%s"%(outDir, scriptName)
open(scriptPath, "w").write(script)

## make script executable
os.system("chmod +x %s"%scriptPath)

from shellCommands import runCommand
output = runCommand(scriptPath)
for l in str(output.stdout).split("\\n"): 
    if ".xml"  in l:
        xmlFile = l.split(" ")[-1]
        break ## the first one is the one we want

## Copy back the xml file
os.system("cp %s/%s %s/%s"%(POTATOExpressFolder, xmlFile, outDir, xmlFile))
print("XML file copied from %s/%s to %s/%s"%(POTATOExpressFolder, xmlFile, outDir, xmlFile))