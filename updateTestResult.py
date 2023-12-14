#from tools import getROOTfile, getNoisePerChip, getResultPerModule, getIDsFromROOT
from ROOT import TFile, TCanvas, gROOT, TH1F
import os
from databaseTools import getTestFromDB, getModuleTestFromDB, getRunFromDB, getModuleFromDB, makeModuleIdMapFromDB
import zipfile
from tools import getNoisePerChip, getIDsFromROOT, getResultPerModule
from makeXml import readXmlConfig
from webdavclient import WebDAVWrapper
from moduleTest import webdav_url, xmlConfigFile, hash_value_read, hash_value_write ## to be updated
import pprint 
hash_value_location = "~/private/webdav.sct" #echo "xxxxxxxxxxxxxxx|xxxxxxxxxxxxxxx\nxxxxxxxxxxxxxxx|xxxxxxxxxxxxxxx" > ~/private/webdav.sct
skipWebdav = True
webdav_website = None
webdav_wrapper = None
if not skipWebdav:
    hash_value_read, hash_value_write = open(os.path.expanduser(hash_value_location)).read()[:-1].split("\n")[1].split("|")
    from moduleTest import webdav_wrapper
    webdav_website = WebDAVWrapper(webdav_url, hash_value_read, hash_value_write)

gROOT.SetBatch()

tmpFolder = "/tmp/"
testID = "PS_26_10-IPG_00103__run71"
tmpFolder = tmpFolder+testID+"/"

base = "/test2/"

version = "V2"

import pathlib
pathlib.Path(tmpFolder).mkdir(parents=True, exist_ok=True)

hwToModuleID, hwToMongoID = makeModuleIdMapFromDB()

def  makePlots(rootFile, xmlConfig, board_id, opticalGroup_id):
    c1 = TCanvas("c1", "")
    hybrid0 =rootFile.Get("Detector/Board_%s/OpticalGroup_%s/Hybrid_0/D_B(%s)_O(%s)_HybridPixelNoiseDistribution_Hybrid(0)"%(board_id, opticalGroup_id, board_id, opticalGroup_id))
    hybrid1 =rootFile.Get("Detector/Board_%s/OpticalGroup_%s/Hybrid_1/D_B(%s)_O(%s)_HybridPixelNoiseDistribution_Hybrid(1)"%(board_id, opticalGroup_id, board_id, opticalGroup_id))
    fName0 = tmpFolder+"/hybrid0.png"
    fName1 = tmpFolder+"/hybrid1.png"
    print("AAAAAAAAA"+fName0)
    print("Detector/Board_%s/OpticalGroup_%s/D_B(%s)_O(%s)_HybridPixelNoiseDistribution_Hybrid(0)"%(board_id, opticalGroup_id, board_id, opticalGroup_id))
    print(hybrid0, hybrid1)
    if hybrid0: 
        hybrid0.Draw()
        c1.SaveAs(fName0)
    if hybrid1: 
        hybrid1.Draw()
        c1.SaveAs(fName1)
    
#    noisePerChip = getNoisePerChip(rootFile , xmlConfig )
#    plot = TH1F("plot", len(noisePerChip), 0, len(noisePerChip))
#    for len(noisePerChip)
#        plot.SetBinContent(343, 334)
    
    return [fName0, fName1]

#_file0->Get("Detector/Board_0/OpticalGroup_0/Hybrid_1")->ls()

# KEY: TH1F	D_B(0)_O(0)_HybridStripNoiseDistribution_Hybrid(1);1	D_B(0)_O(0)_HybridStripNoise_Hybrid(1)
# KEY: TH1F	D_B(0)_O(0)_HybridPixelNoiseDistribution_Hybrid(1);1	D_B(0)_O(0)_HybridPixelNoise_Hybrid(1)
# KEY: TH1F	D_B(0)_O(0)_HybridNoiseDistribution_Hybrid(1);1	D_B(0)_O(0)_HybridNoiseDistribution_Hybrid(1)

#root [7] _file0->Get("Detector/Board_0/OpticalGroup_0/Hybrid_1/SSA_1")->ls()

#TDirectoryFile*		SSA_1	SSA_1
# KEY: TDirectoryFile	Channel;1	Channel
# KEY: TObjString	D_B(0)_O(0)_H(1)_InitialReadoutChipConfiguration_Chip(1);1	Collectable string class
# KEY: TH2F	D_B(0)_O(0)_H(1)_ManualPhaseScan_Chip(1);1	D_B(0)_O(0)_H(1)__Chip(1)
# KEY: TH1I	D_B(0)_O(0)_H(1)_VplusValue_Chip(1);1	D_B(0)_O(0)_H(1)_Vplus Value_Chip(1)
# KEY: TH1I	D_B(0)_O(0)_H(1)_OffsetValues_Chip(1);1	D_B(0)_O(0)_H(1)_Offset Values_Chip(1)
# KEY: TH1F	D_B(0)_O(0)_H(1)_OccupancyAfterOffsetEqualization_Chip(1);1	D_B(0)_O(0)_H(1)_Occupancy After Offset Equalization_Chip(1)
# KEY: TH2F	D_B(0)_O(0)_H(1)_SCurve_Chip(1);1	D_B(0)_O(0)_H(1)_SCurve_Chip(1)
# KEY: TH1F	D_B(0)_O(0)_H(1)_PedestalDistribution_Chip(1);1	D_B(0)_O(0)_H(1)_PedestalDistribution_Chip(1)
# KEY: TH1F	D_B(0)_O(0)_H(1)_ChannelPedestalDistribution_Chip(1);1	D_B(0)_O(0)_H(1)_ChannelPedestal_Chip(1)
# KEY: TH1F	D_B(0)_O(0)_H(1)_NoiseDistribution_Chip(1);1	D_B(0)_O(0)_H(1)_NoiseDistribution_Chip(1)
# KEY: TH1F	D_B(0)_O(0)_H(1)_ChannelNoiseDistribution_Chip(1);1	D_B(0)_O(0)_H(1)_ChannelNoise_Chip(1)
# KEY: TH1F	D_B(0)_O(0)_H(1)_Occupancy_Chip(1);1	D_B(0)_O(0)_H(1)_Occupancy_Chip(1)

def makeNoiseTable(noisePerChip):
    # Create the HTML table header
    html_table = "<table border='1'>\n"
    html_table += "<tr><th>Hybrid</th><th>Type</th><th>Chip</th><th>Noise</th></tr>\n" #<th>Board</th><th>Optical</th>
    # Loop through the dictionary items and add rows to the HTML table
    for histoName, value in noisePerChip.items():
        parts = histoName.split('_')
        board = parts[1][2:-1]
        optical = parts[2][2:-1]
        hybrid = parts[3][2:-1]
        chip = parts[-1][5:]
        chip, chipNumber = chip.split(")")
        noise = value
        # Add a row to the HTML table
        html_table += f"<tr><td>{hybrid}</td><td>{chip}</td><td>{chipNumber}</td><td>{noise}</td></tr>\n" #<td>{board}</td><td>{optical}</td>
    return html_table

    # Close the HTML table
    html_table += "</table>"

def makeWebpage(noisePerChip, xmlConfig, board_id, opticalGroup_id, result, plots, xmlFileLink):
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Two Images</title>
</head>
<body>
    [ADD BODY]
<div style="display: flex;">
    [ADD IMAGE CODE]
</div>
    [ADD TEXT CODE]

</body>
</html>
"""
    imageCode = ""
    for plot in plots:
        imageCode += '<img src="%s" alt="Image 1" style="width: 50%%;">\n'%plot.split("/")[-1]
    html = html.replace("[ADD IMAGE CODE]",imageCode)
    txt = ""
    txt += result+"\n"
    txt += pprint.pformat(noisePerChip)+"\n"
    txt += pprint.pformat(xmlConfig)+"\n"
    html = html.replace("[ADD TEXT CODE]",txt.replace("\n","<br>\n"))
    html = html.replace("[ADD BODY]",makeNoiseTable(noisePerChip))
    
    fName = tmpFolder+"index.html"
    webpage = open(fName, 'w')
    webpage.write(html)
    webpage.close
    return fName

def  uploadToWebDav(folder, files):
    print(folder, files)
    newfiles = {}
    for file in files:
        fileName = file.split("/")[-1]
        target = "%s/%s"%(folder, fileName)
        print("Uploading %s %s"%(file, target))
        if webdav_website: 
            newfile = webdav_website.write_file(file, target)
            newfiles[file] = newfile
        else:
            newfiles[file] = file
    return newfiles

if __name__ == '__main__':
    test = getModuleTestFromDB(testID)
    runKey = test['run'] ## it doesn't work now
    moduleKey, runKey = testID.split("__") ## assuming name like 'PS_26_10-IPG_00103__run70'
    run = getRunFromDB(runKey)
    module = getModuleFromDB(moduleKey)
    fName = run['runFile'][1:].replace("/","_")
    if webdav_wrapper: zip_file_path = webdav_wrapper.download_file(remote_path=run['runFile'].split("//")[-1] , local_path="/tmp/%s"%fName) ## drop
    else: zip_file_path = "/tmp/%s"%fName
    
    # Specify the directory where you want to extract the contents
    extracted_dir = zip_file_path.split(".")[0]

    # Open the zip file
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        # Extract all the contents into the specified directory
        zip_ref.extractall(extracted_dir)
    
    rootFile = TFile.Open(extracted_dir+"/Hybrid.root")
    xmlConfig = readXmlConfig(xmlConfigFile=xmlConfigFile, folder=extracted_dir)
    noisePerChip = getNoisePerChip(rootFile , xmlConfig )
    moduleHwIDs = getIDsFromROOT(rootFile, xmlConfig)
    
    for board_optical in moduleHwIDs:
        moduleID = hwToModuleID[moduleHwIDs[board_optical]]
        board_id, opticalGroup_id = board_optical
        result = getResultPerModule(noisePerChip, xmlConfig, str(board_id), str(opticalGroup_id))
        plots = makePlots(rootFile, xmlConfig, board_id, opticalGroup_id)
        fff = plots+[xmlConfigFile]
        folder = "Module_%s_Run_%s_Result_%s"%(moduleID, testID, version)
        nfolder = base+folder
        print("mkDir %s"%nfolder)
        if webdav_website: webdav_website.mkDir(nfolder)
#        print(webdav_website.list_files(nfolder))
        newNames = uploadToWebDav(nfolder, fff)
        webpage = makeWebpage(noisePerChip, xmlConfig, board_id, opticalGroup_id, result, [newNames[p] for p in plots], newNames[xmlConfigFile])
        if webdav_website: newfile = webdav_website.write_file(webpage, nfolder+"/index.html")
#        print(webdav_website.list_files(nfolder))
        
        if webdav_website:
            print("CERN box link (folder): https://cernbox.cern.ch/files/link/public/%s/%s"%(hash_value_read,nfolder))
            print("https://cmstkita.web.cern.ch/Pisa/TBPS/")
            print("https://cmstkita.web.cern.ch/Pisa/TBPS/Uploads/%s"%(newfile))
        else:
            print(webpage)
            print("file:///run/user/1000/gvfs/sftp:host=pccmslab1.tn,user=thermal/tmp/PS_26_10-IPG_00103__run71/index.html")


