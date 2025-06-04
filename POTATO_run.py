#!/usr/bin/env python3
from ROOT import TFile, TCanvas, gROOT, TH1F, TH2F, gStyle, TGraphErrors
import os
from databaseTools import getTestFromDB, getModuleTestFromDB, getRunFromDB, getModuleFromDB, makeModuleNameMapFromDB, getSessionFromDB
import zipfile
from tools import getNoisePerChip, getIDsFromROOT, getResultPerModule
#from makeXml import readXmlConfig

import argparse
parser = argparse.ArgumentParser(description='Script used to run potato express test from an existing single test module. More info at https://github.com/pisaoutertracker/BurnIn_moduleTest. \n Example: python3  POTATO_run.py PS_26_IBA-10003__run500087 ')
#parser.add_argument('module_test', type=str, help='Single-module test name')
parser.add_argument('session', type=str, help='Session name (eg. session696)')
parser.add_argument('--skipPOTATO', type=bool, default=False, const=True, nargs='?', help='Skip the POTATO run and only prepare the files for it for debugging. Default: False')

#module_test = parser.parse_args().module_test
session = parser.parse_args().session
skipPOTATO = parser.parse_args().skipPOTATO
version = "v1-01"
scriptName_base = "POTATO_run_%s.sh"
POTATOExpressFolder = "/home/thermal/potato/Express/"

skipWebdav = True
from moduleTest import verbose ## to be updated

verbose = 1000
outDir = "POTATOFiles"

moveEverythingToOld = False
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
    from datetime import datetime
    run = getRunFromDB(runNumber)
    run_date = datetime.strptime(run['runDate'], "%Y-%m-%dT%H:%M:%S") 
    session = run['runSession']
    from databaseTools import getIVscansOfModule
    iv_scans = getIVscansOfModule(module_name)
    iv_scan = None
    ## Loop over the IV scans of a specific module, select the one of the same session, and take the last one before the run date
    iv_scan_date_last = datetime.strptime("2000-01-01T00:00:00", "%Y-%m-%dT%H:%M:%S")
    iv_scan_selected = None
    for iv_scan in iv_scans:
        if iv_scan["sessionName"] == session:
            iv_scan_date = datetime.strptime(iv_scan["date"], "%Y-%m-%d %H:%M:%S") 
            if iv_scan_date < run_date and iv_scan_date > iv_scan_date_last:
                iv_scan_date_last = iv_scan_date
                iv_scan_selected = iv_scan
    del iv_scan ## we don't need the loop variable anymore
    if not iv_scan_selected:
        print("IV scans:")
        for iv_scan in iv_scans:
            print(iv_scan["sessionName"], iv_scan["runType"], iv_scan["IVScanId"])
        raise Exception("No IV scan found for run %s and module %s which is later than %s"%(runNumber, module_name, run_date))

    ## Take the last one
    csv_path = createCSVFromIVScan(iv_scan_selected, os.path.join(outDir, f"{iv_scan_selected['IVScanId']}_IVScan.csv"))
    if verbose>10:
        print("Run date:", run_date)
        print("IV scan date:", iv_scan_selected["date"])
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

print("+"*200)
print("Session:", session)
session = getSessionFromDB(session)
if verbose>10:
    print(session)
runs = session['test_runName']
for run in runs:
    print("+"*200)
    print("Run:", run)
    run = getRunFromDB(run)
    if verbose>10:
        print(run)
    print("Module tests:", run['moduleTestName'])

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


    runNumber = run['test_runName']
#    runNumber = test['test_runName']
    moduleBurninName = "Module4L"
    date = run['runDate']
    from updateTestResult import getTemperatureAt, getTimeFromRomeToUTC
    dateTime_rome, dateTime_utc = getTimeFromRomeToUTC(date)
    temp = getTemperatureAt(dateTime_utc.isoformat("T").split("+")[0] , sensorName="Temp0")
    #formatted_temp = format(temp, "+.1f")
    formatted_temp = format(int(temp), "+d")
    formatted_date = dateTime_rome.strftime("%Y-%m-%d_%Hh%Mm%Ss")
    runType = run['runType']
    tag = version

    for module_test in run['moduleTestName']:
        if len(run['moduleTestName']) > 1:
            print("Run: ", run)
            raise Exception("More than one module test found in the run %s. Please specify a single module test. Multiple modules in a single modules might bot be supported"%runNumber)
        print("#"*200)
        print("Single Module Test:", module_test)
        test = getModuleTestFromDB(module_test)
        print("#"*200)
        if verbose>10:
            print(test)
        print()
        module_name = test['moduleName']
        opticalGroup = str(test['opticalGroupName'])
        moduleCarrierName = "01" ##FIXME: here we need a map between the OpticalGroup and the SLOT (slot number)
        #from datetime import datetime
        #datetimeParsed = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")


        #PS_16_FNL-00002_2024-09-15_11h42m33s_+15C_PSfullTest_v1-01.root
        #PS_26_IBA-10003_2025-04-04_11h34m04s_+20C_PSfullTest_v1-01.root

        ## Move all files in the output directory / old:
        if moveEverythingToOld:
            print("Moving all files in the output directory to /old")
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
        connectionMapFilePath_new = os.path.join(outDir, connectionMapFile.replace(".json", "_%s.json"%(runNumber)))
        if os.path.exists(connectionMapFilePath):
            os.system("cp " + connectionMapFilePath + " " + connectionMapFilePath_new)
            print("Connection map file %s copied to %s"%(connectionMapFilePath, connectionMapFilePath_new))
        else:
            raise Exception("Connection map file not found: %s"%connectionMapFilePath)

        connectionMapFilePath = connectionMapFilePath_new
        del connectionMapFile ##obsolete variable

        rootTrackerFileName = outDir + "/" + f"{module_name}_{formatted_date}_{formatted_temp}C_{runType}_{tag}.root"

        ## Merge Results and MonitorDQM files
        from POTATO_mergeFile import mergeTwoROOTfiles
        print("Merged file created:", rootTrackerFileName)

        ## Run potatoconverter (or formatter)
        from POTATO_PisaFormatter import POTATOPisaFormatter as Formatter
        print("#"*200)
        mergeTwoROOTfiles(resultsFile, monitorDQMFile, rootTrackerFileName)
        iv_csv_path = createIVScanCSVFile(runNumber, module_name, outDir)
        theFormatter = Formatter(outDir)
        print(f"Calling POTATO Pisa Formatter version with files {rootTrackerFileName}, {iv_csv_path}")
        print(f"using as input {resultsFile} and {monitorDQMFile}")
        print("#"*200)
        theFormatter.do_burnin_format(rootTrackerFileName, runNumber, opticalGroup, moduleBurninName, moduleCarrierName, iv_csv_path, connectionMapFilePath)

        ############### Prepare a script to run POTATO

        def runPotatoExpress(rootTrackerFileName, descriptionLine="", skipPOTATO=False):
            rootTrackerPath = os.path.abspath(rootTrackerFileName)
            if skipPOTATO: 
                skipPOTATO_string = "## Skipping POTATO express##"
                print("Skipping POTATO Express run. Only preparing the files for it.")
            else:
                skipPOTATO_string = ""
            script = f"""{descriptionLine}
cd {POTATOExpressFolder}
source ../setupPotato.sh
export POTATODIR={POTATOExpressFolder}
mkdir -p backup
mv data/LocalFiles/DropBox/* backup

cp {rootTrackerPath} data/LocalFiles/DropBox

## Compile POTATO express, if necessary
#./compile.py

## Run POTATO express
{skipPOTATO_string}./PotatoExpress
            """
            scriptName = scriptName_base%rootTrackerPath.split("/")[-1].replace(".root", "")
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
            if not xmlFile and not skipPOTATO:
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
            if not skipPOTATO:
                os.system("cp %s %s/%s"%(xmlFile, outDir, xmlFile.split("/")[-1]))
                if verbose>10: print("XML file copied from %s to %s/%s"%(xmlFile, outDir, xmlFile.split("/")[-1]))
                return "%s/%s"%(outDir, xmlFile.split("/")[-1])
            else:
                print("Skipping POTATO Express run. Only preparing the files for it. No 'cp %s %s/...' command executed."%(xmlFile, outDir))
                return "%s/%s"%(outDir, "fake.xml")

        descriptionLine = f"""
# resultsFile = {rootTrackerFileName} created from 
# rootTrackerFileName = {resultsFile}
# monitorDQMFile = {monitorDQMFile}
#
# iv_csv_path = {iv_csv_path}
# runNumber = {runNumber}
# moduleBurninName = {moduleBurninName}
# moduleCarrierName = {moduleCarrierName}
# connectionMapFilePath = {connectionMapFilePath}
# module_name = {module_name}
# test_module_test = {module_test}
#
"""
        xmlFile = runPotatoExpress(rootTrackerFileName, descriptionLine, skipPOTATO=skipPOTATO)
        print("XML file created:", xmlFile)
