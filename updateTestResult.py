#from tools import getROOTfile, getNoisePerChip, getResultPerModule, getIDsFromROOT
from ROOT import TFile, TCanvas, gROOT, TH1F, TH2F, gStyle, TGraphErrors
import os
from databaseTools import getTestFromDB, getModuleTestFromDB, getRunFromDB, getModuleFromDB, makeModuleIdMapFromDB
import zipfile
from tools import getNoisePerChip, getIDsFromROOT, getResultPerModule
from makeXml import readXmlConfig
from webdavclient import WebDAVWrapper
from moduleTest import webdav_url, xmlConfigFile, hash_value_read, hash_value_write ## to be updated

import ROOT

colors = [
ROOT.kYellow+1,
ROOT.kRed,
ROOT.kMagenta,
ROOT.kBlue,
ROOT.kCyan+1,
ROOT.kGreen+1,

ROOT.kOrange,
ROOT.kPink,
ROOT.kViolet,
ROOT.kAzure,
ROOT.kTeal,
ROOT.kSpring,

ROOT.kBlack,
ROOT.kGray,
]

import pprint 
hash_value_location = "~/private/webdav.sct" #echo "xxxxxxxxxxxxxxx|xxxxxxxxxxxxxxx\nxxxxxxxxxxxxxxx|xxxxxxxxxxxxxxx" > ~/private/webdav.sct
useOnlyMergedPlots = True
skipWebdav = False
webdav_website = None
webdav_wrapper = None
if not skipWebdav:
    hash_value_read, hash_value_write = open(os.path.expanduser(hash_value_location)).read()[:-1].split("\n")[1].split("|")
    from moduleTest import webdav_wrapper
    webdav_website = WebDAVWrapper(webdav_url, hash_value_read, hash_value_write)

allVariables = ["NoiseDistribution", "2DPixelNoise", "VplusValue", "OffsetValues", "OccupancyAfterOffsetEqualization", "SCurve", "PedestalDistribution", "ChannelPedestalDistribution", "NoiseDistribution", "ChannelNoiseDistribution", "Occupancy"]
exstensiveVariables = ["NoiseDistribution", "PedestalDistribution"]
#allVariables = []
gROOT.SetBatch()
gStyle.SetOptStat(0)

tmpFolder = "/tmp/"
testID = "PS_26_10-IPG_00103__run74"
tmpFolder = tmpFolder+testID+"/"

base = "/test2/"

version = "V2"

import pathlib
pathlib.Path(tmpFolder).mkdir(parents=True, exist_ok=True)

hwToModuleID, hwToMongoID = makeModuleIdMapFromDB()

def addHistoPlot(plots, canvas, plot, fName):
    ## save histo plot, and add it to "plots"
    if plot:
        ## skip single chip plots if useOnlyMergedPlots is activated
        if (("SSA" in fName) or ("MPA" in fName)) and (not ("Merged" in fName)) and (useOnlyMergedPlots): 
            return
        canvas.cd()
        if type(plot) == TGraphErrors:
            plot.Draw("AP")
        else:
            if plot.GetDimension()==2:
                plot.Draw("COLZ")
            else:
                if plot.GetName().split("_")[-2] in exstensiveVariables:
                    plot.Draw("HIST")
                else:
                    plot.Draw()
        canvas.Update()
        canvas.SaveAs(fName)
        print("Creating %s"%fName)
    ## append fName, even if it does not exist to show the missing plot
    plots.append(fName)
    return

def makeNoisePlot(rootFile, opticalGroup):
    noiseGraph = TGraphErrors()
    for hybrid_id in opticalGroup['hybrids']:
        hybrid = opticalGroup['hybrids'][str(hybrid_id)]
        hybridMod_id = opticalGroup_id*2 + int(hybrid_id)
        for chip in ["SSA", "MPA"]:
            if chip == "SSA": chipIds = hybrid['strips']
            elif chip == "MPA": chipIds = hybrid['pixels']
            ## "InitialReadoutChipConfiguration"
            for chipId in chipIds:
                plot = rootFile.Get("Detector/Board_%s/OpticalGroup_%s/Hybrid_%s/%s_%s/D_B(%s)_O(%s)_H(%s)_%s_Chip(%s)"%(board_id, opticalGroup_id, hybridMod_id, chip, chipId, board_id, opticalGroup_id, hybridMod_id, "NoiseDistribution", chipId))
                n = noiseGraph.GetN()
                x = 0.1 + int(hybrid_id) + int(chip == "MPA")*2 + (chipId-int(chip == "MPA")*8)/10
                noiseGraph.SetPoint(n, x, plot.GetMean())
                noiseGraph.SetPointError(n, 0, plot.GetStdDev())
    ax = noiseGraph.GetXaxis()
    ax.SetBinLabel(ax.FindBin(0.5), "SSA, H0")
    ax.SetBinLabel(ax.FindBin(1.5), "SSA, H1")
    ax.SetBinLabel(ax.FindBin(2.5), "MPA, H0")
    ax.SetBinLabel(ax.FindBin(3.5), "MPA, H1")
    return noiseGraph




def makePlots(rootFile, xmlConfig, board_id, opticalGroup_id):
    c1 = TCanvas("c1", "")
    c1.SetGridx()
    c1.SetGridy()
    plots = []
    opticalGroup = xmlConfig["boards"][str(board_id)]["opticalGroups"][str(opticalGroup_id)]
    global noiseGraph
    noiseGraph = makeNoisePlot(rootFile, opticalGroup)
    addHistoPlot(plots, c1, noiseGraph, fName = tmpFolder+"/CombinedNoisePlot.png")
    for hybrid_id in opticalGroup['hybrids']:
        hybrid = opticalGroup['hybrids'][str(hybrid_id)]
        hybridMod_id = opticalGroup_id*2 + int(hybrid_id)
        for chip in ["SSA", "MPA"]:
            if chip == "SSA": chipIds = hybrid['strips']
            elif chip == "MPA": chipIds = hybrid['pixels']
            ## "InitialReadoutChipConfiguration"
            for name in allVariables:
                print("Doing %s"%name)
                merged = None
                counter = 0
                for chipId in chipIds:
                    plot = rootFile.Get("Detector/Board_%s/OpticalGroup_%s/Hybrid_%s/%s_%s/D_B(%s)_O(%s)_H(%s)_%s_Chip(%s)"%(board_id, opticalGroup_id, hybridMod_id, chip, chipId, board_id, opticalGroup_id, hybridMod_id, name, chipId))
                    if plot:
                        if not merged: 
                            merged = plot.Clone(plot.GetName().replace("Chip(%s)"%chipId, "Merged"))
                            print(type(merged), type(plot))
                            merged.SetTitle(merged.GetTitle().replace("Chip(%s)"%chipId, "Merged"))
                        else: merged.Add(plot)
                    counter += 1
                    print(plot)
                    addHistoPlot(plots, c1, plot, fName = tmpFolder+"/%s_Hybrid%s_%s%s.png"%(name, hybrid_id, chip, chipId))
                ## re-normalize all non-extensive variable
                if merged and not name in exstensiveVariables:
                    merged.Scale(1./ counter)
                addHistoPlot(plots, c1, merged, fName = tmpFolder+"/%s_Hybrid%s_%s%s.png"%(name, hybrid_id, chip, "Merged"))
        for name in ["StripNoise", "PixelNoise", "Noise"]:
            plot = rootFile.Get("Detector/Board_%s/OpticalGroup_%s/Hybrid_%s/D_B(%s)_O(%s)_Hybrid%sDistribution_Hybrid(%s)"%(board_id, opticalGroup_id, hybridMod_id, board_id, opticalGroup_id, name, hybridMod_id))
            print(plot)
            addHistoPlot(plots, c1, plot, fName = tmpFolder+"/%s_Hybrid%s.png"%(name, hybrid_id))
    
    return plots

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

def makeNoiseTable(noisePerChip, board_id, optical_id):
    # Create the HTML table header
    html_table = "<table border='1'>\n"
    html_table += "<tr><th>Chip</th><th>Hybrid0</th><th>Hybrid1</th><th>Chip</th><th>Hybrid0</th><th>Hybrid1</th></tr>\n" #<th>Board</th><th>Optical</th>
    # Loop through the dictionary items and add rows to the HTML table
    for lineN in range(0,8):
        html_table += "<tr><th>SSA%d</th><th>%.3f</th><th>%.3f</th><th>MPA%d</th><th>%.3f</th><th>%.3f</th></tr>\n"%(lineN, noisePerChip["D_B(%s)_O(%s)_H(%s)_NoiseDistribution_Chip(%s)SSA"%(board_id, optical_id, 0, lineN)], noisePerChip["D_B(%s)_O(%s)_H(%s)_NoiseDistribution_Chip(%s)SSA"%(board_id, optical_id, 1, lineN)], lineN+8, noisePerChip["D_B(%s)_O(%s)_H(%s)_NoiseDistribution_Chip(%s)MPA"%(board_id, optical_id, 0, lineN+8)], noisePerChip["D_B(%s)_O(%s)_H(%s)_NoiseDistribution_Chip(%s)MPA"%(board_id, optical_id, 1, lineN+8)]) #<th>Board</th><th>Optical</th>
#    for histoName, value in noisePerChip.items():
#        parts = histoName.split('_')
#        board = parts[1][2:-1]
#        optical = parts[2][2:-1]
#        hybrid = parts[3][2:-1]
#        chip = parts[-1][5:]
#        chip, chipNumber = chip.split(")")
#        noise = value
#        # Add a row to the HTML table
#        html_table += f"<tr><td>{hybrid}</td><td>{chip}</td><td>{chipNumber}</td><td>{noise}</td></tr>\n" #<td>{board}</td><td>{optical}</td>
    
    # Close the HTML table
    html_table += "</table>"
    
    return html_table


def addPlotSection(title, plots, width):
    imageCode = "<h1> %s </h1>"%title + "\n"
    imageCode += "<p>"
    for plot in plots:
        imageCode += '<img src="%s" style="width: %f%%;">\n'%(plot.split("/")[-1], width)
    return imageCode

def grayText(text):
    return '<font color="gray"> %s </font>'%text

def makeWebpage(rootFile, testID, moduleKey, runKey, module, run, test, noisePerChip, xmlConfig, board_id, opticalGroup_id, result, plots, xmlFileLink):
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>%s_%s_</title>
</head>
<body>
    [ADD BODY]
    [ADD IMAGE CODE]
    [ADD TEXT CODE]
    [ADD FINALBODY]

</body>
</html>
"""%(moduleKey, runKey)
    plotsInclusive = []
    plotsPerChip = []
    for plot in plots:
        if "SSA" in plot or "MPA" in plot: 
#            if "Merged" in plot or not useOnlyMergedPlots:
                plotsPerChip.append(plot)
        else: plotsInclusive.append(plot)
    print(plotsInclusive)
    print(plotsPerChip)
    imageCode = ""
    imageCode += addPlotSection("Combined Noise plot", [p for p in plots if "CombinedNoisePlot"in p], 30.0)
    imageCode += addPlotSection("Hybrid 0", [p for p in plotsInclusive if "_Hybrid0"in p], 30.0)
    imageCode += addPlotSection("Hybrid 1", [p for p in plotsInclusive if "_Hybrid1"in p], 30.0)
    imageCode += addPlotSection("Hybrid 0 - MPA - Merged plots", [p for p in plotsPerChip if "_Hybrid0"in p and "MPA" in p], 30.0)
    imageCode += addPlotSection("Hybrid 0 - SSA - Merged plots", [p for p in plotsPerChip if "_Hybrid0"in p and "SSA" in p], 30.0)
    imageCode += addPlotSection("Hybrid 1 - MPA - Merged plots", [p for p in plotsPerChip if "_Hybrid1"in p and "MPA" in p], 30.0)
    imageCode += addPlotSection("Hybrid 1 - SSA - Merged plots", [p for p in plotsPerChip if "_Hybrid1"in p and "SSA" in p], 30.0)
    html = html.replace("[ADD IMAGE CODE]",imageCode)
    txt = ""
#    txt += result+"\n"
#    txt += pprint.pformat(noisePerChip)+"\n"
#    txt += pprint.pformat(xmlConfig)+"\n"
    html = html.replace("[ADD TEXT CODE]",txt.replace("\n", "<br>\n"))
    ### Analysis
    body = "<h1> %s %s  </h1>"%(grayText("Analysis:") ,version) + "\n"
    
    ### Module
    body += "<h1> %s %s  </h1>"%(grayText("Module:"), moduleKey) + "\n"
    body += grayText("Module: ") + moduleKey + " (lpGBT Fuse Id: %s)"%module['hardwareID'] + "\n"
    
    ### Run
    body += "<h1> %s %s  </h1>"%(grayText("Run: "), runKey) + "\n"
    date, time =  run['runDate'].split("T")
    body += grayText("Run: ") + runKey 
    body += ". " + grayText("Date: ") +date + ". " + grayText("Time: ") + time + "<br>" +"\n"
    body += grayText("CalibrationStartTimestamp: ") + str(rootFile.Get("Detector/CalibrationStartTimestamp_Detector")) + "<br>" +"\n"
    body += grayText("GitCommitHash: ") + str(rootFile.Get("Detector/GitCommitHash_Detector")) + "<br>" +"\n"
    body += grayText("HostName: ") + str(rootFile.Get("Detector/HostName_Detector")) + "<br>" +"\n"
    body += grayText("Username: ") + str(rootFile.Get("Detector/Username_Detector")) + "<br>" +"\n"
    body += grayText("DetectorConfiguration: ") + str(rootFile.Get("Detector/DetectorConfiguration_Detector")) + "<br>" +"\n"
    body += grayText("CalibrationName: ") + str(rootFile.Get("Detector/CalibrationName_Detector")) + "<br>" +"\n"
    directLinkToZip = run['runFile'].replace("files/link/public", "remote.php/dav/public-files")
    ##TODO aggiungere il link diretto al ROOT file
    ##TODO aggiungere il link diretto al log file
    ##TODO aggiungere il link diretto al xml file
    ##TODO aggiungere il link diretto al xml config
    folderLink =  '/'.join(run['runFile'].split("/")[:-1])
#    linkToROOTFile = folderLink.replace("files/link/public", "rootjs/public") + "Results/OT_ModuleTest_M103_Run176/Hybrid_jkkfb.root"
    body += "<br>" + "\n"
    body += grayText("Zip file: ") + '<a href="%s">'%directLinkToZip + directLinkToZip + "</a><br>" + "\n"
    body += grayText("Folder: ") + '<a href="%s">'%folderLink + folderLink + "</a><br>" + "\n"
    
    ### Single Module Run
    boardToId = {v: k for k, v in run["runBoards"].items()}
    body += "<h1> %s %s  </h1>"%(grayText("Single Module Run:"), testID) + "\n"
#    date, time =  run['runDate'].split("T")
    body += grayText("Single Module Run: ") + testID + "<br>" +"\n"
    board_id = boardToId[str(test['board'])]
    optical_id = str(test['opticalGroupID'])
    body += grayText("Board: ") + str(test['board']) + grayText(". BoardId: ") + board_id + grayText(". OpticalGroup: ")  + optical_id + "<br>" +"\n"
    body += "<br>" + "\n"
    body += grayText("LpGBTFuseId: ") + str(rootFile.Get("Detector/Board_%s/OpticalGroup_%s/D_B(%s)_LpGBTFuseId_OpticalGroup(%s)"%(board_id, optical_id, board_id, optical_id))) + "<br>" +"\n"
    body += grayText("VTRxFuseId: ") + str(rootFile.Get("Detector/Board_%s/OpticalGroup_%s/D_B(%s)_VTRxFuseId_OpticalGroup(%s)"%(board_id, optical_id, board_id, optical_id))) + "<br>" +"\n"
#    body += ". Date:" + date + ". Time:" + time + "<br>" +"\n"
#    directLinkToZip = run['runFile'].replace("files/link/public", "remote.php/dav/public-files")
#    folderLink =  '/'.join(run['runFile'].split("/")[:-1])
##    linkToROOTFile = folderLink.replace("files/link/public", "rootjs/public") + "Results/OT_ModuleTest_M103_Run176/Hybrid_jkkfb.root"
#    body += 'Zip file: <a href="%s">'%directLinkToZip + directLinkToZip + "</a><br>" + "\n"
#    body += 'Folder: <a href="%s">'%folderLink + folderLink + "</a><br>" + "\n"
    
    body += "<h1> %s  </h1>"%("SSA and MPA noise table") + "\n"
    html = html.replace("[ADD BODY]",body + makeNoiseTable(noisePerChip, board_id, optical_id))
    
    finalbody = "<h1> XML configuration </h1>" + "\n"
    finalbody += pprint.pformat(xmlConfig)+"\n"
    finalbody += "<h1> InitialLpGBTConfiguration </h1>" + "\n"
    finalbody += "InitialLpGBTConfiguration: %s"%rootFile.Get("Detector/Board_%s/OpticalGroup_%s/D_B(%s)_InitialLpGBTConfiguration_OpticalGroup(%s)"%(board_id, optical_id, board_id, optical_id)) + "<br>" +"\n"
    finalbody = finalbody.replace("\n","\n<br>").replace(" ","&nbsp;")
    html = html.replace("[ADD FINALBODY]",finalbody)

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
    fName = run['runFile'].split("//")[-1].replace("/", "_")
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
        fff = [f for f in fff if os.path.exists(f)]
        newNames = uploadToWebDav(nfolder, fff)
        webpage = makeWebpage(rootFile, testID, moduleKey, runKey, module, run, test, noisePerChip, xmlConfig, board_id, opticalGroup_id, result, [newNames[p] for p in plots if p in newNames], newNames[xmlConfigFile])
        if webdav_website: newfile = webdav_website.write_file(webpage, nfolder+"/index.html")
#        print(webdav_website.list_files(nfolder))
        
        print(extracted_dir)
        print(webpage)
        if webdav_website:
            print("CERN box link (folder): https://cernbox.cern.ch/files/link/public/%s/%s"%(hash_value_read,nfolder))
            print("https://cmstkita.web.cern.ch/Pisa/TBPS/")
            print("https://cmstkita.web.cern.ch/Pisa/TBPS/Uploads/%s"%(newfile))
        else:
            print("file:///run/user/1000/gvfs/sftp:host=pccmslab1.tn,user=thermal/tmp/PS_26_10-IPG_00103__run71/index.html")


