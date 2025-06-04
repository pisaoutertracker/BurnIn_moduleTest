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
scriptName = "POTATO_run.sh"
POTATOExpressFolder = "/home/thermal/potato/Express/"

skipWebdav = True
from moduleTest import verbose ## to be updated

verbose = 1000
outDir = "POTATOFiles"

def createCSVFromIVScan(iv_scan, path):
    """
    Convert a full scan dictionary (containing both metadata and the
    `scan["data"]` payload) into the CSV
    """

    data = iv_scan["data"]                     # shorthand

    # --------- 1) gather header fields (with graceful fall-backs) ----------
    name_label = iv_scan.get("nameLabel", "")
    date_str   = iv_scan.get("date")
    if not date_str:
        # If the scan doesn't supply its own timestamp, stamp the file now
        date_str = dt.datetime.now(tz=dt.timezone.utc) \
                     .astimezone().strftime("%Y-%m-%d %H:%M:%S")

    header_rows = [
        ("#NameLabel", name_label),
        ("#Date",      date_str),
        ("#Comment",   iv_scan.get("comment", "")),
        ("#Location",  iv_scan.get("location", "")),
        ("#Inserter",  iv_scan.get("inserter", "")),
        ("#RunType",   iv_scan.get("runType", "")),
    ]

    # --------- 2) station-level summary (use pre-computed averages if any) -
    av_temp = iv_scan.get("averageTemperature")
    if av_temp is None:
        av_temp = mean(data["TEMP_DEGC"])

    av_rh = iv_scan.get("averageHumidity")
    if av_rh is None:
        av_rh = mean(data["RH_PRCNT"])

    station_line = (
        iv_scan.get("station", "cleanroom"),
        av_temp,
        av_rh,
    )

    # --------- 3) write the CSV -------------------------------------------
    from pathlib import Path
    import csv
    path = Path(path)
    with path.open("w", newline="") as fp:
        w = csv.writer(fp)

        # metadata
        for row in header_rows:
            w.writerow(row)
        w.writerow([])                                     # blank spacer

        # station summary
        w.writerow(["STATION", "AV_TEMP_DEGC", "AV_RH_PRCNT"])
        w.writerow(station_line)
        w.writerow([])

        # per-point data block
        w.writerow(["VOLTS", "CURRNT_NAMP", "TEMP_DEGC",
                    "RH_PRCNT", "TIME"])

        for volts, amps, temp, rh, ts in zip(
            data["VOLTS"],
            data["CURRNT_NAMP"],
            data["TEMP_DEGC"],
            data["RH_PRCNT"],
            data["TIME"],
        ):
            w.writerow([volts, amps, temp, rh, ts])

    return path



def createIVScanCSVFile(runNumber, module_name, outDir):
    run = getRunFromDB(runNumber)
    session = run['runSession']
    from databaseTools import getIVscansOfModule
    iv_scans = getIVscansOfModule(module_name)
    iv_scan = None
    for iv_scan in iv_scans:
        if iv_scan["sessionName"] == session:
            print(iv_scan["sessionName"],iv_scan["runType"], iv_scan["IVScanId"])

    if not iv_scan:
        print("IV scans:")
        for iv_scan in iv_scans:
            print(iv_scan["sessionName"], iv_scan["runType"], iv_scan["IVScanId"])
        raise Exception("No IV scan found for run %s and module %s"%(runNumber, module_name))

    ## Take the last one
    csv_path = createCSVFromIVScan(iv_scan, os.path.join(outDir, f"{iv_scan['IVScanId']}_IVScan.csv"))
    print("IV scan CSV file created:", csv_path)
    return csv_path




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

test = getModuleTestFromDB(module_test)
run = getRunFromDB(test['test_runName'])
fName = run['runFile'].split("//")[-1].replace("/", "_")

remote_path=run['runFile'].split("//")[-1]
local_path="/tmp/%s"%fName

extracted_dir = downloadAndExtractZipFile(remote_path, local_path, skipWebdav=skipWebdav)

###############################################################################################

resultsFile = extracted_dir + "/Results.root"
## Get monitorDQM file
if not os.path.isfile(resultsFile):
    print("Results file not found in %s"%extracted_dir)
    exit(1)

monitorDQMFile = None
for file in os.listdir(extracted_dir):
    if file.startswith("MonitorDQM") and file.endswith(".root"):
        monitorDQMFile = os.path.join(extracted_dir, file)
        break

if not monitorDQMFile:
    print("MonitorDQM file not found in %s"%extracted_dir)
    exit(1)


runNumber = test['test_runName']
moduleBurninName = "Module4L"
opticalGroup = str(test['opticalGroupName'])
moduleCarrierName = "01" ##FIXME: here we need a map between the OpticalGroup and the SLOT (slot number)

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

## Move all files in the output directory / old:
if not os.path.exists(outDir):
    os.makedirs(outDir)
if not os.path.exists(outDir+"/old"):
    os.makedirs(outDir+"/old")
for file in os.listdir(outDir):
    if os.path.isdir(f"{outDir}/{file}"):
        continue
    print(outDir, file)
    os.rename(os.path.join(outDir, file), os.path.join(outDir, "old", file))

## Copy the connection map file to the same folder as the ROOT file
connectionMapFile = "connectionMap_%s.json"%module_name
connectionMapFilePath = os.path.join(os.path.dirname(resultsFile), connectionMapFile)
if os.path.exists(connectionMapFilePath):
    os.system("cp " + connectionMapFilePath + " " + outDir)
    print("Connection map file %s copied to %s"%(connectionMapFile, outDir))
else:
    raise Exception("Connection map file not found: %s"%connectionMapFilePath)


rootTrackerFileName = outDir + "/" + f"{module_name}_{formatted_date}_{formatted_temp}C_{runType}_{tag}.root"

## Merge Results and MonitorDQM files
from POTATO_mergeFile import mergeTwoROOTfiles
print("Merged file created:", rootTrackerFileName)

## Run potatoconverter (or formatter)
from POTATO_PisaFormatter import POTATOPisaFormatter as Formatter
mergeTwoROOTfiles(resultsFile, monitorDQMFile, rootTrackerFileName)
iv_csv_path = createIVScanCSVFile(runNumber, module_name, outDir)
theFormatter = Formatter(outDir)
theFormatter.do_burnin_format(rootTrackerFileName, runNumber, opticalGroup, moduleBurninName, moduleCarrierName, iv_csv_path)

############### Prepare a script to run POTATO

def runPotatoExpress(rootTrackerFileName):
    rootTrackerPath = os.path.abspath(rootTrackerFileName)
    script = f""" cd {POTATOExpressFolder}
    source ../setupPotato.sh
    export POTATODIR={POTATOExpressFolder}
    mkdir -p backup
    mv data/LocalFiles/TestOutput/* backup
    mv data/LocalFiles/DropBox/* backup
    mv ReferenceFiles/* backup

    cp {rootTrackerPath} data/LocalFiles/TestOutput
    cp {rootTrackerPath} data/LocalFiles/DropBox
    cp {rootTrackerPath} ReferenceFiles/PS_16_FNL-00000_2025-04-07_16h18m13s_+15C_PSfullTest_v1-00_reference.root

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
    xmlFile = None
    for l in str(output.stdout).split("\\n"): 
        if ".xml"  in l:
            xmlFile = l.split(" ")[-1]
            break ## the first one is the one we want
    if not xmlFile:
        print("###########################################################")
        print("POTATO Express did not produce an XML file. Output:")
        print(output.stdout.decode('utf-8'))
        print()
        print("###########################################################")
        print("Script executed:", scriptPath)
        print("###########################################################")
        print("Error output:")
        print(output.stderr.decode('utf-8'))
        print()
        print("###########################################################")
        raise Exception("XML file not found in the output of POTATO Express. Output: %s. There must be a crash in POTATO Express. Try to run manually %s for debugging."%(output.stdout, scriptPath))

    ## Copy back the xml file
    os.system("cp %s %s/%s"%(xmlFile, outDir, xmlFile.split("/")[-1]))
    if verbose>10: print("XML file copied from %s to %s/%s"%(xmlFile, outDir, xmlFile.split("/")[-1]))
    return "%s/%s"%(outDir, xmlFile.split("/")[-1])

xmlFile = runPotatoExpress(rootTrackerFileName)
print("XML file created:", xmlFile)
