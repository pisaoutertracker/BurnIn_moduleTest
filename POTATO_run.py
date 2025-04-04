from ROOT import TFile, TCanvas, gROOT, TH1F, TH2F, gStyle, TGraphErrors
import os
from databaseTools import getTestFromDB, getModuleTestFromDB, getRunFromDB, getModuleFromDB, makeModuleNameMapFromDB
import zipfile
from tools import getNoisePerChip, getIDsFromROOT, getResultPerModule
#from makeXml import readXmlConfig

from webdavclient import WebDAVWrapper
from moduleTest import verbose,webdav_url, xmlPyConfigFile, hash_value_read, hash_value_write ## to be updated


module_test = "PS_26_IBA-10003__run500084"
version = "tmp"
skipWebdav = False
tmpFolder = "/tmp/"

#allVariables = []
gROOT.SetBatch()
gStyle.SetOptStat(0)
tmpFolder = tmpFolder+module_test+"_forPOTATO_%s/"%version
base = "/test3/"

### Initialize webdav, if necessary
hash_value_location = "~/private/webdav.sct" #echo "xxxxxxxxxxxxxxx|xxxxxxxxxxxxxxx\nxxxxxxxxxxxxxxx|xxxxxxxxxxxxxxx" > ~/private/webdav.sct
webdav_website = None
webdav_wrapper = None
if not skipWebdav:
    hash_value_read, hash_value_write = open(os.path.expanduser(hash_value_location)).read()[:-1].split("\n")[1].split("|")
    from moduleTest import webdav_wrapper
    webdav_website = WebDAVWrapper(webdav_url, hash_value_read, hash_value_write)
    
import shutil
try:
    shutil.rmtree(tmpFolder[:-1]+"_bak")
    shutil.move(tmpFolder, tmpFolder[:-1]+"_bak")
except:
    pass
import pathlib
pathlib.Path(tmpFolder).mkdir(parents=True, exist_ok=True)

hwToModuleID, hwToMongoID = makeModuleNameMapFromDB()

test = getModuleTestFromDB(module_test)
if not ("test_runName" in test):
    raise Exception("%s not found in %s."%(module_test, ' curl -X GET -H "Content-Type: application/json" "http://192.168.0.45:5000/module_test"'))
print("Module test:",module_test, " Test:", test)
runName = test['test_runName']
moduleName = test['moduleName']
opticalGroup_id = test['opticalGroupName']
board = test['board']
run = getRunFromDB(runName)
boardToId = {v: k for k, v in run["runBoards"].items()}
board_id = boardToId[board]
module = getModuleFromDB(moduleName)
fName = run['runFile'].split("//")[-1].replace("/", "_")
if webdav_wrapper: 
    print("Downloading %s to %s"%(run['runFile'].split("//")[-1], "/tmp/%s"%fName))
    zip_file_path = webdav_wrapper.download_file(remote_path=run['runFile'].split("//")[-1] , local_path="/tmp/%s"%fName) ## drop
else: zip_file_path = "/tmp/%s"%fName

print("Unzipping %s to %s"%(zip_file_path, tmpFolder))
# Specify the directory where you want to extract the contents
# extracted_dir = zip_file_path.split(".")[0]
extracted_dir = tmpFolder

# Open the zip file
with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
    # Extract all the contents into the specified directory
    zip_ref.extractall(extracted_dir)

print("Unzipped to %s"%extracted_dir)

################################################

from POTATO_PisaFormatter import POTATOPisaFormatter as Formatter

from POTATO_mergeFile import mergeTwoROOTfiles


###############################################################################################

resultsFile = extracted_dir + "/Results.root"
monitorDQMFile = None
for file in os.listdir(extracted_dir):
    if file.startswith("MonitorDQM_") and file.endswith(".root"):
        monitorDQMFile = os.path.join(extracted_dir, file)
        break

resultsFile = "potatoconverters/TestFiles/Run_500009/Results.root"
monitorDQMFile = "potatoconverters/TestFiles/Run_500009/MonitorDQM_2025-03-25_17-17-32.root"

outDir = "POTATOFiles"
theFormatter = Formatter(outDir)

rootTrackerFileName = outDir + "/" + "ResultsWithMonitorDQM.root"

mergeTwoROOTfiles(resultsFile, monitorDQMFile, rootTrackerFileName)
print("Merged file created:", rootTrackerFileName)

runNumber = "150"
moduleBurninName = "Module4L"
moduleCarrierName = "ModuleCarrier4Left"
opticalGroup = '1'

theFormatter.do_burnin_format(rootTrackerFileName, runNumber, opticalGroup, moduleBurninName, moduleCarrierName)