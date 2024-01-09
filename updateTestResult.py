import pprint 
allVariables = ["NoiseDistribution", "2DPixelNoise", "VplusValue", "OffsetValues", "OccupancyAfterOffsetEqualization", "SCurve", "PedestalDistribution", "ChannelPedestalDistribution", "NoiseDistribution", "ChannelNoiseDistribution", "Occupancy"]
exstensiveVariables = ["NoiseDistribution", "PedestalDistribution"]
useOnlyMergedPlots = True
version = "Test2"

#from tools import getROOTfile, getNoisePerChip, getResultPerModule, getIDsFromROOT
from ROOT import TFile, TCanvas, gROOT, TH1F, TH2F, gStyle, TGraphErrors
import os
from databaseTools import getTestFromDB, getModuleTestFromDB, getRunFromDB, getModuleFromDB, makeModuleNameMapFromDB
import zipfile
from tools import getNoisePerChip, getIDsFromROOT, getResultPerModule
#from makeXml import readXmlConfig
from webdavclient import WebDAVWrapper
from moduleTest import webdav_url, xmlConfigFile, hash_value_read, hash_value_write ## to be updated

verbose = 10000

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
    if not("2DPixelNoise" in fName and "SSA" in fName):
        plots.append(fName)
    return

#def makeNoisePlot(rootFile, opticalGroup, opticalGroup_id, ):
#    noiseGraph = TGraphErrors()
#    for hybrid_id in opticalGroup['hybrids']:
#        hybrid = opticalGroup['hybrids'][str(hybrid_id)]
#        hybridMod_id = opticalGroup_id*2 + int(hybrid_id)
#        for chip in ["SSA", "MPA"]:
#            if chip == "SSA": chipIds = hybrid['strips']
#            elif chip == "MPA": chipIds = hybrid['pixels']
#            ## "InitialReadoutChipConfiguration"
#            for chipId in chipIds:
#                plot = rootFile.Get("Detector/Board_%s/OpticalGroup_%s/Hybrid_%s/%s_%s/D_B(%s)_O(%s)_H(%s)_%s_Chip(%s)"%(board_id, opticalGroup_id, hybridMod_id, chip, chipId, board_id, opticalGroup_id, hybridMod_id, "NoiseDistribution", chipId))
#                n = noiseGraph.GetN()
#                x = 0.1 + int(hybrid_id) + int(chip == "MPA")*2 + (chipId-int(chip == "MPA")*8)/10
#                noiseGraph.SetPoint(n, x, plot.GetMean() if plot else 0)
#                noiseGraph.SetPointError(n, 0, plot.GetStdDev() if plot else 5)
#    ax = noiseGraph.GetXaxis()
#    ax.SetBinLabel(ax.FindBin(0.5), "SSA, H0")
#    ax.SetBinLabel(ax.FindBin(1.5), "SSA, H1")
#    ax.SetBinLabel(ax.FindBin(2.5), "MPA, H0")
#    ax.SetBinLabel(ax.FindBin(3.5), "MPA, H1")
#    return noiseGraph

def makePlots(rootFile, xmlConfig, board_id, opticalGroup_id, tmpFolder, dateTime):
    plots = []
    ## add Influxdb plot
    plots.append(  makePlotInfluxdb(dateTime, tmpFolder) )

    c1 = TCanvas("c1", "")
    c1.SetGridx()
    c1.SetGridy()
    try:
        opticalGroup = xmlConfig["boards"][str(board_id)]["opticalGroups"][str(opticalGroup_id)]
    except:
        opticalGroup = xmlConfig["boards"][int(board_id)]["opticalGroups"][int(opticalGroup_id)]
    global noiseGraph
    
    ### Make Noise Plot
#    noiseGraph = makeNoisePlot(rootFile, opticalGroup)
    noiseGraph = TGraphErrors()
    ## add fake points at x=0 and x=4
    noiseGraph.SetPoint(0, 0, 0) 
    noiseGraph.SetPoint(1, 4, 0)
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
                noiseGraph.SetPoint(n, x, plot.GetMean() if plot else 0)
                noiseGraph.SetPointError(n, 0, plot.GetStdDev() if plot else 5)
    ax = noiseGraph.GetXaxis()
    ax.SetBinLabel(ax.FindBin(0.5), "SSA, H0")
    ax.SetBinLabel(ax.FindBin(1.5), "SSA, H1")
    ax.SetBinLabel(ax.FindBin(2.5), "MPA, H0")
    ax.SetBinLabel(ax.FindBin(3.5), "MPA, H1")

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
                
                ## add 1D projection 
                if merged and "2DPixelNoise" in name:
                    prx = merged.ProjectionX()
                    prx.SetTitle(merged.GetTitle() + " - X projection")
                    prx.Scale(1./merged.GetNbinsY())
                    addHistoPlot(plots, c1, prx, fName = tmpFolder+"/%s_Hybrid%s_%s%s.png"%(name+"projX", hybrid_id, chip, "Merged"))
                    pry = merged.ProjectionY()
                    pry.SetTitle(merged.GetTitle() + " - Y projection")
                    pry.Scale(1./merged.GetNbinsX())
                    addHistoPlot(plots, c1, pry, fName = tmpFolder+"/%s_Hybrid%s_%s%s.png"%(name+"projY", hybrid_id, chip, "Merged"))
                    
                del merged
        for name in ["StripNoise", "PixelNoise", "Noise"]:
            plot = rootFile.Get("Detector/Board_%s/OpticalGroup_%s/Hybrid_%s/D_B(%s)_O(%s)_Hybrid%sDistribution_Hybrid(%s)"%(board_id, opticalGroup_id, hybridMod_id, board_id, opticalGroup_id, name, hybridMod_id))
            print(plot)
            addHistoPlot(plots, c1, plot, fName = tmpFolder+"/%s_Hybrid%s.png"%(name, hybrid_id))
    
#    print(plots)
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
        html_table += "<tr><th>SSA%d</th><th>%.3f</th><th>%.3f</th><th>MPA%d</th><th>%.3f</th><th>%.3f</th></tr>\n"%(lineN, noisePerChip.get("D_B(%s)_O(%s)_H(%s)_NoiseDistribution_Chip(%s)SSA"%(board_id, optical_id, 2*int(optical_id)+0, lineN),0), noisePerChip.get("D_B(%s)_O(%s)_H(%s)_NoiseDistribution_Chip(%s)SSA"%(board_id, optical_id, 2*int(optical_id)+1, lineN),0), lineN+8, noisePerChip.get("D_B(%s)_O(%s)_H(%s)_NoiseDistribution_Chip(%s)MPA"%(board_id, optical_id, 2*int(optical_id)+0, lineN+8),0), noisePerChip.get("D_B(%s)_O(%s)_H(%s)_NoiseDistribution_Chip(%s)MPA"%(board_id, optical_id, 2*int(optical_id)+1, lineN+8),0)) #<th>Board</th><th>Optical</th>
    
    html_table += "</tr>\n"
    html_table += "</table>\n<br>\n"
    
    html_table += "<table border='1'>\n"
    html_table += "<tr><th>Chip</th><th>Hybrid0</th><th>Hybrid1</th><th>Chip</th><th>Hybrid0</th><th>Hybrid1</th></tr>\n" #<th>Board</th><th>Optical</th>
    html_table += "<tr><th>Aver.</th><th>%.3f</th><th>%.3f</th><th>Aver.</th><th>%.3f</th><th>%.3f</th></tr>\n"%(noisePerChip.get("Average_B%s_O%s_H%s_SSA"%(board_id, optical_id, 2*int(optical_id)+0),0), noisePerChip.get("Average_B%s_O%s_H%s_SSA"%(board_id, optical_id, 2*int(optical_id)+1),0), noisePerChip.get("Average_B%s_O%s_H%s_MPA"%(board_id, optical_id, 2*int(optical_id)+0),0), noisePerChip.get("Average_B%s_O%s_H%s_MPA"%(board_id, optical_id, 2*int(optical_id)+1),0)) #<th>Board</th><th>Optical</th>
    html_table += "<tr><th>Max.</th><th>%.3f</th><th>%.3f</th><th>Max.</th><th>%.3f</th><th>%.3f</th></tr>\n"%(noisePerChip.get("Maximum_B%s_O%s_H%s_SSA"%(board_id, optical_id, 2*int(optical_id)+0),0), noisePerChip.get("Maximum_B%s_O%s_H%s_SSA"%(board_id, optical_id, 2*int(optical_id)+1),0), noisePerChip.get("Maximum_B%s_O%s_H%s_MPA"%(board_id, optical_id, 2*int(optical_id)+0),0), noisePerChip.get("Maximum_B%s_O%s_H%s_MPA"%(board_id, optical_id, 2*int(optical_id)+1),0)) #<th>Board</th><th>Optical</th>
    html_table += "<tr><th>Min.</th><th>%.3f</th><th>%.3f</th><th>Min.</th><th>%.3f</th><th>%.3f</th></tr>\n"%(noisePerChip.get("Minimum_B%s_O%s_H%s_SSA"%(board_id, optical_id, 2*int(optical_id)+0),0), noisePerChip.get("Minimum_B%s_O%s_H%s_SSA"%(board_id, optical_id, 2*int(optical_id)+1),0), noisePerChip.get("Minimum_B%s_O%s_H%s_MPA"%(board_id, optical_id, 2*int(optical_id)+0),0), noisePerChip.get("Minimum_B%s_O%s_H%s_MPA"%(board_id, optical_id, 2*int(optical_id)+1),0)) #<th>Board</th><th>Optical</th>
    
    
    html_table += "</tr>\n"
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

def makeWebpage(rootFile, testID, moduleName, runName, module, run, test, noisePerChip, xmlConfig, board_id, opticalGroup_id, result, plots, xmlFileLink, tmpFolder):
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
"""%(moduleName, runName)
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
    imageCode += addPlotSection("Sensors", [p for p in plots if "sensor"in p], 30.0)
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
    body += "<h1> %s %s  </h1>"%(grayText("Module:"), moduleName) + "\n"
    body += grayText("Module: ") + moduleName + " (lpGBT Fuse Id: %s)"%module['hwId'] + "\n"
    
    ### Run
    body += "<h1> %s %s  </h1>"%(grayText("Run: "), runName) + "\n"
    date, time =  run['runDate'].split("T")
    body += grayText("Run: ") + runName 
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
    optical_id = str(test['opticalGroupName'])
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
    print(noisePerChip)
    
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

def makePlotInfluxdb(time, folder):
#    se  committi in github il token ti taglio le dita 🙂
    token_location = "~/private/influx.sct" 
    token = open(os.path.expanduser(token_location)).read()[:-1]
    
    from datetime import datetime, timedelta
    
    from influxdb_client import InfluxDBClient, Point, WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS
    
    import numpy as np
    import matplotlib.pyplot as plt
    
    org = "pisaoutertracker"
    bucket = "sensor_data"
    
    client = InfluxDBClient(url="http://cmslabserver:8086/", token=token)
    
    timeFormat = "%Y-%m-%dT%H:%M:%S"
    
    currentTime = datetime.strptime(time, timeFormat) - timedelta(hours=1) ## to move to UTC
    start_time = (currentTime - timedelta(hours=2)).isoformat("T") + "Z"
    stop_time = (currentTime + timedelta(hours=2)).isoformat("T") + "Z"
#    stop_time = time + "Z"
#    start_time = "2023-12-20T03:03:34Z"
#    stop_time = "2023-12-20T15:03:34Z"
    
#    start_time = (datetime.utcnow() - timedelta(hours=12)).isoformat("T") + "Z"
#    stop_time = datetime.utcnow().isoformat("T") + "Z"

    print(start_time)
    print(stop_time)
    
    sensorName = "Temp0"
    query = f'''
    from(bucket: "sensor_data")
     |> range(start: {start_time}, stop: {stop_time})
     |> filter(fn: (r) => r["_measurement"] == "mqtt_consumer")
     |> filter(fn: (r) => r["_field"] == "%s" )
     |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
     |> yield(name: "mean")
    '''%sensorName
    
    tables = client.query_api().query(query, org=org)
    
    time = []
    value = []
    
    for table in tables:
       for record in table.records:
           time.append(record.get_time())
           value.append(record.get_value())
    
    # Plot the data
    plt.figure(figsize=(10, 5))
    plt.plot(time, value, label=sensorName)
    plt.axvline(x=currentTime, color='r', linestyle='--', label=currentTime.strftime('%H:%M:%S'))
    plt.title('Sensor Data Over Time')
    plt.legend()
    plt.grid(True)
    fName = folder+"/sensor_data_plot.png"
    
    ## Orario UTC
    plt.savefig(fName)
    print("InfluxDb: saved ", fName)
    
#    client.__del__()
    
    import locale
    locale.setlocale(locale.LC_ALL, 'C')
    
    return fName

def updateTestResult(module_test, skipWebdav = False):
#    testID = "PS_26_10-IPG_00103__run6"
    tmpFolder = "/tmp/"

    #allVariables = []
    gROOT.SetBatch()
    gStyle.SetOptStat(0)
    tmpFolder = tmpFolder+module_test+"__%s/"%version
    base = "/test3/"
#    base = "/ReReco1/"

    import shutil
    try:
        shutil.rmtree(tmpFolder[:-1]+"_bak")
        shutil.move(tmpFolder, tmpFolder[:-1]+"_bak")
    except:
        pass
    import pathlib
    pathlib.Path(tmpFolder).mkdir(parents=True, exist_ok=True)

    hwToModuleID, hwToMongoID = makeModuleNameMapFromDB()

    ### Initialize webdav, if necessary
    hash_value_location = "~/private/webdav.sct" #echo "xxxxxxxxxxxxxxx|xxxxxxxxxxxxxxx\nxxxxxxxxxxxxxxx|xxxxxxxxxxxxxxx" > ~/private/webdav.sct
    webdav_website = None
    webdav_wrapper = None
    if not skipWebdav:
        hash_value_read, hash_value_write = open(os.path.expanduser(hash_value_location)).read()[:-1].split("\n")[1].split("|")
        from moduleTest import webdav_wrapper
        webdav_website = WebDAVWrapper(webdav_url, hash_value_read, hash_value_write)
    
    
    test = getModuleTestFromDB(module_test)
    if not ("test_runName" in test):
        raise Exception("%s not found in %s."%(module_test, ' curl -X GET -H "Content-Type: application/json" "http://192.168.0.45:5000/module_test"'))
    print(module_test, test)
    runName = test['test_runName']
    moduleName = test['moduleName']
    opticalGroup_id = test['opticalGroupName']
    board = test['board']
    run = getRunFromDB(runName)
    boardToId = {v: k for k, v in run["runBoards"].items()}
    board_id = boardToId[board]
    module = getModuleFromDB(moduleName)
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
#    xmlConfig = readXmlConfig(xmlConfigFile=xmlConfigFile, folder=extracted_dir)
    xmlConfig = run["runConfiguration"] ## take configuration from db instead of python file
    print(xmlConfig)
    global noisePerChip
    noisePerChip = getNoisePerChip(rootFile , xmlConfig )
    moduleHwIDs = getIDsFromROOT(rootFile, xmlConfig)
    
#    for board_optical in moduleHwIDs:
#    board_id, opticalGroup_id = board_optical
    result = getResultPerModule(noisePerChip, xmlConfig, str(board_id), str(opticalGroup_id))
    plots = makePlots(rootFile, xmlConfig, board_id, opticalGroup_id, tmpFolder, run['runDate'])
    fff = plots+[xmlConfigFile]
    folder = "Module_%s_Run_%s_Result_%s"%(moduleName, runName, version)
    nfolder = base+folder
    print("mkDir %s"%nfolder)
    if webdav_website: webdav_website.mkDir(nfolder)
##        print(webdav_website.list_files(nfolder))
    fff = [f for f in fff if os.path.exists(f)]
#        newNames = uploadToWebDav(nfolder, fff)
    webpage = makeWebpage(rootFile, module_test, moduleName, runName, module, run, test, noisePerChip, xmlConfig, board_id, opticalGroup_id, result, plots, xmlConfigFile, tmpFolder)
    zipFile = "results" 
    import shutil
    tmpUpFolder = tmpFolder.replace("//","/").replace("//","/")
    tmpUpFolder = '/'.join(tmpUpFolder.split("/")[:-1])
    name = tmpUpFolder.split("/")[-1]
    tmpUpFolder = '/'.join(tmpUpFolder.split("/")[:-1])+"/"
    print(tmpUpFolder, name, tmpFolder, zipFile, nfolder)
    if verbose>20: print("shutil.make_archive(zipFile, 'zip', resultFolder)", tmpUpFolder+name, tmpFolder)
    shutil.make_archive(tmpUpFolder+name, 'zip', tmpFolder)
    if verbose>20: print("Done")
    if webdav_website: 
        newFile = webdav_website.write_file(tmpUpFolder+name+".zip", "%s/results.zip"%(nfolder))
        if verbose>0: print("Uploaded %s"%newFile)
#        if webdav_website: newfile = webdav_website.write_file(webpage, nfolder+"/index.html")
#        print(webdav_website.list_files(nfolder))
    
#        for f in webdav_website.list_files("/test2/Module_PS_26_10-IPG_00103_Run_PS_26_10-IPG_00103__run6_Result_V3/"):
#            print (f)
    print(extracted_dir)
    print(webpage)
    print("file:///run/user/1000/gvfs/sftp:host=pccmslab1.tn,user=thermal%s"%webpage)
    if webdav_website:
        print("CERN box link (folder): https://cernbox.cern.ch/files/link/public/%s/%s"%(hash_value_read,nfolder))
        print("https://cmstkita.web.cern.ch/Pisa/TBPS/")
        download = "https://cmstkita.web.cern.ch/Pisa/TBPS/Uploads/%s"%(newFile)
        print(download)
        navigator = "https://cmstkita.web.cern.ch/Pisa/TBPS/navigator.php/Uploads/%s/"%(newFile)
        print(navigator)
    else:
        download = "dummy"
        navigator = "dummy"
#            print("https://cmstkita.web.cern.ch/Pisa/TBPS/navigator.php/Uploads//test2/Module_PS_26_10-IPG_00103_Run_PS_26_10-IPG_00103__run6_Result_V3/results_jvmze.zip/")
    
    from databaseTools import createAnalysis
    json = {
        "moduleTestAnalysisName": folder, #"PS_26_05-IBA_00004__run79__Test", 
        "moduleTestName": module_test, #"PS_26_05-IBA_00004__run79", 
        "analysisVersion": version, #"Test", 
        "analysisResults": {module_test:result},
        "analysisSummary": noisePerChip,
        "analysisFile": navigator
    }
    status = createAnalysis(json)
    if int(status) != 201:
        pass
#        raise Exception("createAnalysis failed of moduleTestAnalysisName %s."%folder)
    from databaseTools import appendAnalysisToModule
    status = appendAnalysisToModule(folder)
    if int(status) != 200:
        raise Exception("appendAnalysisToModule failed of moduleTestAnalysisName %s."%folder)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Script used to elaborate the results of the Phase-2 PS module test. More info at https://github.com/pisaoutertracker/BurnIn_moduleTest. \n Example: python3  updateTestResult.py PS_26_10-IPG_00103__run9 . ')
    parser.add_argument('module_test', type=str, help='Single-module test name')
    parser.add_argument('--skipWebdav', type=bool, nargs='?', const=True, default=False, help='Skip upload to webdav (for testing).')
    args = parser.parse_args()
    updateTestResult(args.module_test , args.skipWebdav )


