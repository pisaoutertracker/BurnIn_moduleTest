skipInfluxDb= False
#skipInfluxDb= True
allVariables = ["2DPixelNoise", "VplusValue", "OffsetValues", "OccupancyAfterOffsetEqualization", "SCurve", "PedestalDistribution", "ChannelPedestalDistribution", "NoiseDistribution", "ChannelNoiseDistribution", "Occupancy"]
hybridPlots = ["HybridStripNoiseDistribution", "HybridPixelNoiseDistribution", "HybridNoiseDistribution",
"BitSlipValues", "WordAlignmentRetryNumbers", "PatternMatchingEfficiency", "CICinputPhaseHistogram", "BestCICinputPhases", "LockingEfficiencyCICinput", "CICwordAlignmentDelay", "PatternMatchingEfficiencyCIC", "PatternMatchingEfficiencyMPA_SSA"]

opticalGroupPlots = ["LpGBTinputAlignmentSuccess", "LpGBTinputBestPhase", "LpGBTinputFoundPhasesDistribution"]

exstensiveVariables = ["NoiseDistribution", "PedestalDistribution"]
useOnlyMergedPlots = True
version = "Test7"

#allVariables = ["NoiseDistribution"]

#from tools import getROOTfile, getNoisePerChip, getResultPerModule, getIDsFromROOT
from ROOT import TFile, TCanvas, gROOT, TH1F, TH2F, gStyle, TGraphErrors
import os
from databaseTools import getTestFromDB, getModuleTestFromDB, getRunFromDB, getModuleFromDB, makeModuleNameMapFromDB
import zipfile
from tools import getNoisePerChip, getIDsFromROOT, getResultPerModule
#from makeXml import readXmlConfig
from webdavclient import WebDAVWrapper
from moduleTest import webdav_url, xmlPyConfigFile, hash_value_read, hash_value_write ## to be updated

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

def makeMergedPlot(plots, chip):
    print("makeMergedPlot")
    merged = None
    for plot in plots:
        print(plot.GetName())
        if not merged: 
            chipN = "Chip(" + plot.GetName().split("Chip(")[1]
            chipN = chipN.split(")")[0] + ")"
            print(chipN)
            newName = plot.GetName().replace(chipN, "Merged")+chip
            print(newName)
            merged = plot.Clone(newName)
            merged.SetTitle(newName)
        else: 
            merged.Add(plot)
    return merged

import ctypes
def makeMultiplePlot2D(plots, chip):
    hybridN = list(plots)[0]
    if len(plots[hybridN])==0: return None
    if type(plots[hybridN][0])!=ROOT.TH2F: return None
    print("makeMultiplePlot2D")
    tempPlot = plots[hybridN][0]
    ## PS module:  https://ep-news.web.cern.ch/content/developing-new-electronics-cms-tracking-system 
    # along z: 5 cm long, divided in 2 hybrids, divided in 16 pixels 1.5mm each
    # along x: 10 cm long, divided in 8 chips, divided in 125 pixels/strips 0.1mm each
#    maxX = tempPlot.GetXaxis().GetXmax() ##119.5
#    maxY = tempPlot.GetYaxis().GetXmax() ##15.5 
    sizeX = tempPlot.GetNbinsX() ##120
    sizeY = tempPlot.GetNbinsY() ##16
    title = tempPlot.GetTitle()
    name = tempPlot.GetName()
    chipN = "Chip(" + name.split("Chip(")[1]
    chipN = chipN.split(")")[0] + ")"
    print(chipN)
    newName = name.replace(chipN, "Multiple")+chip
    Nchip = 8
    if "2DPixelNoise" in name:
        multiple = ROOT.TH2F(newName, title, sizeX*Nchip, -0.5, sizeX*Nchip-0.5, sizeY*2, -0.5, sizeY*2-0.5)
    else: ##SCurve
        multiple = ROOT.TH2F(newName, title, sizeX*Nchip*2, -0.5, sizeX*Nchip*2-0.5, sizeY, -0.5, sizeY-0.5)
        
    x, y, z = ctypes.c_int(0), ctypes.c_int(0), ctypes.c_int(0)
    for hybridN in plots:
        for plot in plots[hybridN]:
            hybridN = int(hybridN)
            name = plot.GetName()
            chipN = int(name.split("_Chip(")[1].split(")")[0])
            if chip == "MPA": chipN = chipN - 8 ## MPA chip [8, 15], SSSA [0, 7]
            for i in range(0, (sizeX+2)*(sizeY+2)):
                plot.GetBinXYZ(i, x, y, z)
                if x.value>0 and x.value<=sizeX and y.value>0 and y.value<=sizeY:
                    if "2DPixelNoise" in name:
                        x_ = x.value + int(sizeX*chipN)
                        y_ = y.value + sizeY*hybridN
                    else: ##SCurve
                        x_ = x.value + int(sizeX*chipN) + int(sizeX*8)*hybridN
                        y_ = y.value
                    #print(i, chipN, x_, y_, plot.GetBinContent(i), hybridN, name)
                    multiple.SetBinContent(x_, y_, plot.GetBinContent(i))
                    multiple.SetBinError(x_, y_, plot.GetBinError(i))

    return multiple


def addHistoPlot(plots, canvas, plot, fName):
    ## save histo plot, and add it to "plots"
    if plot:
        ## skip single chip plots if useOnlyMergedPlots is activated
        if (("SSA" in fName) or ("MPA" in fName)) and (not ("Merged" in fName)) and (not ("Multiple" in fName)) and (useOnlyMergedPlots): 
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
        print("Creating %s"%fName)
        canvas.SaveAs(fName)
    ## append fName, even if it does not exist to show the missing plot
    if not("2DPixelNoise" in fName and "SSA" in fName):
        plots.append(fName)
    return

def addMultipleHistoPlot(plots, canvas, plotCollections, fName):
    ## save histo plot, and add it to "plots"
    max_ = 0
    min_ = 0
    import copy
    plotCollections = copy.deepcopy(plotCollections)
    for hybridN in plotCollections:
        for i, plot in enumerate(plotCollections[hybridN]):
            hybridN = int(hybridN)
            assert(type(plot)==ROOT.TH1F)
            canvas.cd()
            max_ = max(max_, plot.GetMaximum())
            min_ = min(min_, plot.GetMaximum())
    
#    leg = ROOT.TLegend(0.75,0.5,0.9,0.9)
    leg = ROOT.TLegend(0.9,0.1,0.99,0.9)
    leg.SetFillStyle(0)
    leg.SetLineStyle(0)
    leg.SetLineWidth(0)
    for hybridN in plotCollections:
        for i, plot in enumerate(plotCollections[hybridN]):
            plot.SetLineColor(colors[i])
            plot.SetMarkerColor(colors[i])
            if i == 0:
                plot.SetMaximum(max_*1.1)
                plot.SetMinimum(max(0, min_ - max_*0.2))
                plot.Draw()
            else:
                plot.Draw("same")
            chipN = int(plot.GetName().split("_Chip(")[1].split(")")[0])
            if "MPA" in fName: chipN = chipN - 8
            leg.AddEntry(plot,"H%s C%d"%(hybridN, chipN))
    leg.Draw()
    canvas.Update()
    print("Creating %s"%fName)
    canvas.SaveAs(fName)
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

def get_histograms(directory, path=""):
    """
    Recursively collect all histograms in a ROOT directory and its subdirectories.

    Parameters:
        directory (ROOT.TDirectory): The ROOT directory to search.
        path (str): The current path in the ROOT file.

    Returns:
        list: A list of tuples where each tuple contains the full path and the histogram object.
    """
    histograms = []

    for key in directory.GetListOfKeys():
        obj_name = key.GetName()
        obj = key.ReadObj()
        obj_class = obj.ClassName()
        full_path = f"{path}/{obj_name}" if path else obj_name

        if obj.IsA().InheritsFrom("TDirectory"):  # If the object is a folder
            histograms.extend(get_histograms(obj, full_path))  # Recursive call for subdirectory
        elif "TH" in obj_class:  # If the object is a histogram
            obj.SetDirectory(0)  # Detach the histogram from the ROOT file to prevent automatic deletion
            histograms.append((full_path, obj))

    return histograms

def makePlots(rootFile, xmlConfig, board_id, opticalGroup_id, tmpFolder, dateTime):
    plots = []
    ## add Influxdb plot
    
    if not skipInfluxDb: plots.append(  makePlotInfluxdb(dateTime, tmpFolder) )

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
    histograms = get_histograms(rootFile)

    ## Check if the variables are in the root file#
    for collection in [allVariables, hybridPlots, opticalGroupPlots, exstensiveVariables]:
        print("Checking %s"%collection)
        for name in collection[:]:
            print("Checking %s"%name)
            found = False
            for hist_path, hist_obj in histograms:
                if name in hist_path:
                    found = True
                    break
            print("found", found)
            if histograms:
                print(hist_path)
            if not found:
                print("#####################################################################################")
                print("WARNING: %s not found in the root file. It will be excluded from the webpage"%name)
                print("#####################################################################################")
                collection.remove(name)

    ## if the plot is not found, it is removed from the list
    for hist_path, hist_obj in histograms:
        if "NoiseDistribution" in hist_path:
            print(hist_path)
            addHistoPlot(plots, c1, hist_obj, fName = tmpFolder+"/%s.png"%hist_path)
    for chip in ["SSA", "MPA"]:
        if chip == "SSA": chipIds = hybrid['strips']
        elif chip == "MPA": chipIds = hybrid['pixels']
        for name in allVariables:
            if "Pixel" in name and chip != "MPA": continue ## Skip 2DPixelNoise plot for strip
            print("Doing %s"%name)
            counter = 0
            global plotsToBeMerged
            plotsToBeMerged = {}
            for hybrid_id in opticalGroup['hybrids']:
                hybrid = opticalGroup['hybrids'][str(hybrid_id)]
                hybridMod_id = opticalGroup_id*2 + int(hybrid_id)
                plotsToBeMerged[hybrid_id] = []
                for chipId in chipIds:
                    print("chipId",str(chipId))
                    plot = None
                    count = 0
                    while(plot==None):
                        histoName = "Detector/Board_%s/OpticalGroup_%s/Hybrid_%s/%s_%s/D_B(%s)_O(%s)_H(%s)_%s_Chip(%s)"%(board_id, opticalGroup_id, hybridMod_id, chip, chipId, board_id, opticalGroup_id, hybridMod_id, name, chipId)
                        plot = rootFile.Get(histoName)
                        if count>0: 
                            print("WARNINGHERE:", count, "histoName ", histoName)
                            print(rootFile.Print())
                            from time import sleep
                            sleep(1)
                            rootFile.Recover()
                        if count>5: 
                            raise Exception("Problems with file %s"%rootFile.GetName())
                        count+=1
                    print("T",str(plot))
                    ## selct 2DPixelNoise plots to make the combined 2D histogram
                    if plot: plotsToBeMerged[hybrid_id].append(plot)
                    counter += 1
                    addHistoPlot(plots, c1, plot, fName = tmpFolder+"/%s_Hybrid%s_%s%s.png"%(name, hybrid_id, chip, chipId))
                ## re-normalize all non-extensive variable
                merged = makeMergedPlot(plotsToBeMerged[hybrid_id], chip)
                if merged and not name in exstensiveVariables:
                    merged.Scale(1./ counter)
                print(merged)
                addHistoPlot(plots, c1, merged, fName = tmpFolder+"/%s_Hybrid%s_%s%s.png"%(name, hybrid_id, chip, "Merged"+chip))
                
                ## add 1D projection 
                if merged and "2DPixelNoise" in name:
                    prx = merged.ProjectionX()
                    prx.SetTitle(merged.GetTitle() + " - X projection")
                    prx.Scale(1./merged.GetNbinsY())
                    addHistoPlot(plots, c1, prx, fName = tmpFolder+"/%s_Hybrid%s_%s%s.png"%(name+"projX", hybrid_id, chip, "Merged"+chip))
                    pry = merged.ProjectionY()
                    pry.SetTitle(merged.GetTitle() + " - Y projection")
                    pry.Scale(1./merged.GetNbinsX())
                    addHistoPlot(plots, c1, pry, fName = tmpFolder+"/%s_Hybrid%s_%s%s.png"%(name+"projY", hybrid_id, chip, "Merged"+chip))
            
#            if "2DPixelNoise" in name:
            if type(plot)==ROOT.TH2F and not "SCurve" in name: ## too many bins, very slow!
#            if type(plot)==ROOT.TH2F:
                multiple = makeMultiplePlot2D(plotsToBeMerged, chip)
                addHistoPlot(plots, c1, multiple, fName = tmpFolder+"/%s_%s%s.png"%(name, chip, "Multiple"+chip))
#            elif "NoiseDistribution" in name:
            elif type(plot)==ROOT.TH1F:
                addMultipleHistoPlot(plots, c1, plotsToBeMerged, fName = tmpFolder+"/%s_%s%s.png"%(name, chip, "Multiple"+chip))
                
            merged = None
    for name in hybridPlots:
        for hybrid_id in opticalGroup['hybrids']:
            hybrid = opticalGroup['hybrids'][str(hybrid_id)]
            hybridMod_id = opticalGroup_id*2 + int(hybrid_id)
            plot2 = rootFile.Get("Detector/Board_%s/OpticalGroup_%s/Hybrid_%s/D_B(%s)_O(%s)_%s_Hybrid(%s)"%(board_id, opticalGroup_id, hybridMod_id, board_id, opticalGroup_id, name, hybridMod_id))
            addHistoPlot(plots, c1, plot2, fName = tmpFolder+"/%s_Hybrid%s.png"%(name, hybrid_id))
    
    for name in opticalGroupPlots:
        plot2 = rootFile.Get("Detector/Board_%s/OpticalGroup_%s/D_B(%s)_%s_OpticalGroup(%s)"%(board_id, opticalGroup_id, board_id, name, opticalGroup_id))
        addHistoPlot(plots, c1, plot2, fName = tmpFolder+"/%s_OpticalGroup%s.png"%(name, hybrid_id))
    
    return plots


def makeNoiseTable(noisePerChip, board_id, optical_id, ratio = False):
    # Create the HTML table header
    html_table = "<table border='1'>\n"
    html_table += "<tr><th>Chip</th><th>Hybrid0</th><th>Hybrid1</th><th>Chip</th><th>Hybrid0</th><th>Hybrid1</th></tr>\n" #<th>Board</th><th>Optical</th>
    # Loop through the dictionary items and add rows to the HTML table
    if not ratio:
        for lineN in range(0,8):
            html_table += "<tr><th>SSA%d</th><th>%.3f</th><th>%.3f</th><th>MPA%d</th><th>%.3f</th><th>%.3f</th></tr>\n"%(lineN, noisePerChip.get("D_B(%s)_O(%s)_H(%s)_NoiseDistribution_Chip(%s)SSA"%(board_id, optical_id, 2*int(optical_id)+0, lineN),0), noisePerChip.get("D_B(%s)_O(%s)_H(%s)_NoiseDistribution_Chip(%s)SSA"%(board_id, optical_id, 2*int(optical_id)+1, lineN),0), lineN+8, noisePerChip.get("D_B(%s)_O(%s)_H(%s)_NoiseDistribution_Chip(%s)MPA"%(board_id, optical_id, 2*int(optical_id)+0, lineN+8),0), noisePerChip.get("D_B(%s)_O(%s)_H(%s)_NoiseDistribution_Chip(%s)MPA"%(board_id, optical_id, 2*int(optical_id)+1, lineN+8),0)) #<th>Board</th><th>Optical</th>
        
        html_table += "</tr>\n"
        html_table += "</table>\n<br>\n"
        
        html_table += "<table border='1'>\n"
        html_table += "<tr><th>Chip</th><th>Hybrid0</th><th>Hybrid1</th><th>Chip</th><th>Hybrid0</th><th>Hybrid1</th></tr>\n" #<th>Board</th><th>Optical</th>
        html_table += "<tr><th>Aver.</th><th>%.3f</th><th>%.3f</th><th>Aver.</th><th>%.3f</th><th>%.3f</th></tr>\n"%(noisePerChip.get("Average_B%s_O%s_H%s_SSA"%(board_id, optical_id, 2*int(optical_id)+0),0), noisePerChip.get("Average_B%s_O%s_H%s_SSA"%(board_id, optical_id, 2*int(optical_id)+1),0), noisePerChip.get("Average_B%s_O%s_H%s_MPA"%(board_id, optical_id, 2*int(optical_id)+0),0), noisePerChip.get("Average_B%s_O%s_H%s_MPA"%(board_id, optical_id, 2*int(optical_id)+1),0)) #<th>Board</th><th>Optical</th>
        html_table += "<tr><th>Max.</th><th>%.3f</th><th>%.3f</th><th>Max.</th><th>%.3f</th><th>%.3f</th></tr>\n"%(noisePerChip.get("Maximum_B%s_O%s_H%s_SSA"%(board_id, optical_id, 2*int(optical_id)+0),0), noisePerChip.get("Maximum_B%s_O%s_H%s_SSA"%(board_id, optical_id, 2*int(optical_id)+1),0), noisePerChip.get("Maximum_B%s_O%s_H%s_MPA"%(board_id, optical_id, 2*int(optical_id)+0),0), noisePerChip.get("Maximum_B%s_O%s_H%s_MPA"%(board_id, optical_id, 2*int(optical_id)+1),0)) #<th>Board</th><th>Optical</th>
        html_table += "<tr><th>Min.</th><th>%.3f</th><th>%.3f</th><th>Min.</th><th>%.3f</th><th>%.3f</th></tr>\n"%(noisePerChip.get("Minimum_B%s_O%s_H%s_SSA"%(board_id, optical_id, 2*int(optical_id)+0),0), noisePerChip.get("Minimum_B%s_O%s_H%s_SSA"%(board_id, optical_id, 2*int(optical_id)+1),0), noisePerChip.get("Minimum_B%s_O%s_H%s_MPA"%(board_id, optical_id, 2*int(optical_id)+0),0), noisePerChip.get("Minimum_B%s_O%s_H%s_MPA"%(board_id, optical_id, 2*int(optical_id)+1),0)) #<th>Board</th><th>Optical</th>
    else:
        for lineN in range(0,8):
            html_table += "<tr><th>SSA%d</th><th>%.3f</th><th>%.3f</th><th>MPA%d</th><th>%.3f</th><th>%.3f</th></tr>\n"%(lineN, noisePerChip.get("D_B(%s)_O(%s)_H(%s)_ChannelNoiseDistribution_Chip(%s)SSA"%(board_id, optical_id, 2*int(optical_id)+0, lineN),0), noisePerChip.get("D_B(%s)_O(%s)_H(%s)_ChannelNoiseDistribution_Chip(%s)SSA"%(board_id, optical_id, 2*int(optical_id)+1, lineN),0), lineN+8, noisePerChip.get("D_B(%s)_O(%s)_H(%s)_2DPixelNoise_Chip(%s)MPA"%(board_id, optical_id, 2*int(optical_id)+0, lineN+8),0), noisePerChip.get("D_B(%s)_O(%s)_H(%s)_2DPixelNoise_Chip(%s)MPA"%(board_id, optical_id, 2*int(optical_id)+1, lineN+8),0)) #<th>Board</th><th>Optical</th>
        
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

def makeWebpage(rootFile, testID, moduleName, runName, module, run, test, noisePerChip, noiseRatioPerChip, xmlConfig, board_id, opticalGroup_id, result, plots, xmlFileLink, tmpFolder):
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
    print("All plots available:")
    for plot in plots:
        print(plot)
        if "SSA" in plot or "MPA" in plot: 
#            if "Merged" in plot or not useOnlyMergedPlots:
                plotsPerChip.append(plot)
        else: plotsInclusive.append(plot)
    print(plotsInclusive)
    print(plotsPerChip)
    imageCode = ""
#    imageCode += addPlotSection("Combined Noise plot", [p for p in plots if "CombinedNoisePlot"in p], 30.0)
    imageCode += addPlotSection("Sensors", [p for p in plots if "sensor"in p], 30.0)
    imageCode += addPlotSection("All-in-one plots", [p for p in plots if (("Multiple"in p or "CombinedNoisePlot"in p) and (not "MPA" in p and not "SSA" in p))], 30.0)
    imageCode += addPlotSection("All-in-one plots (MPA)", [p for p in plots if (("Multiple"in p or "CombinedNoisePlot"in p) and ("MPA" in p))], 30.0)
    imageCode += addPlotSection("All-in-one plots (SSA)", [p for p in plots if (("Multiple"in p or "CombinedNoisePlot"in p) and ("SSA" in p))], 30.0)
    imageCode += addPlotSection("OpticalGroup", [p for p in plotsInclusive if "_OpticalGroup"in p], 30.0)
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
    hwId = -1
    if 'hwId' in module: hwId = module['hwId']
    if 'children' in module and 'lpGBT' in module['children'] and 'CHILD_SERIAL_NUMBER' in module["children"]["lpGBT"]: hwId = str(module["children"]["lpGBT"]["CHILD_SERIAL_NUMBER"]) 
    body += grayText("Module: ") + moduleName + " (lpGBT Fuse Id: %s)"%hwId + "\n"
    
    ### Run
    body += "<h1> %s %s  </h1>"%(grayText("Run: "), runName) + "\n"
    date, time =  run['runDate'].split("T")
    body += grayText("Run: ") + runName 
    body += ". " + grayText("Date: ") +date + ". " + grayText("Time: ") + time + "<br>" +"\n"
    body += grayText("CalibrationStartTimestamp: ") + str(rootFile.Get("Detector/CalibrationStartTimestamp_Detector")) + "<br>" +"\n"
    body += grayText("CalibrationStopTimestamp: ") + str(rootFile.Get("Detector/CalibrationStopTimestamp_Detector")) + "<br>" +"\n"
    body += grayText("GitCommitHash: ") + str(rootFile.Get("Detector/GitCommitHash_Detector")) + "<br>" +"\n"
    body += grayText("HostName: ") + str(rootFile.Get("Detector/HostName_Detector")) + "<br>" +"\n"
    body += grayText("Username: ") + str(rootFile.Get("Detector/Username_Detector")) + "<br>" +"\n"
#    body += grayText("InitialDetectorConfiguration: ") + str(rootFile.Get("Detector/InitialDetectorConfiguration_Detector")) + "<br>" +"\n"
#    body += grayText("FinalDetectorConfiguration: ") + str(rootFile.Get("Detector/FinalDetectorConfiguration_Detector")) + "<br>" +"\n"
    body += grayText("CalibrationName: ") + str(rootFile.Get("Detector/CalibrationName_Detector")) + "<br>" +"\n"
    body += grayText("NameId_Board: ") + str(rootFile.Get("Detector/Board_0/D_NameId_Board_(0)")) + "<br>" +"\n"
    directLinkToZip = run['runFile'].replace("files/link/public", "remote.php/dav/public-files")
    testId,zipFile = directLinkToZip.split("/")[-2:]
    directLinkToROOTFile = "https://cmstkita.web.cern.ch/Pisa/TBPS/root.html?file=https://cmstkita.web.cern.ch/Pisa/TBPS/navigator_eos.php/"+"/%s/%s/"%(testId,zipFile)+"/Results.root"
    directLinkToXmlFile = "https://cmstkita.web.cern.ch/Pisa/TBPS/navigator_eos.php/"+"/%s/%s/"%(testId,zipFile)+"ModuleTest_settings.xml"
    directLinkToLogFile = "https://cmstkita.web.cern.ch/Pisa/TBPS/navigator_eos.php/"+"/%s/%s/%s.log"%(testId,zipFile,testId)
    folderLink =  '/'.join(run['runFile'].split("/")[:-1])
#    linkToROOTFile = folderLink.replace("files/link/public", "rootjs/public") + "Results/OT_ModuleTest_M103_Run176/Hybrid_jkkfb.root"
    body += "<br>" + "\n"
#    https://cmstkita.web.cern.ch/Pisa/TBPS/root.html?file=https://cmstkita.web.cern.ch/Pisa/TBPS/navigator_eos.php/Run_24/output_rtmxq.zip/Results.root
    body += grayText("Browse ROOT file: ") + '<a href="%s">'%directLinkToROOTFile + directLinkToROOTFile + "</a><br>" + "\n"
    body += grayText("Zip file: ") + '<a href="%s">'%directLinkToZip + directLinkToZip + "</a><br>" + "\n"
    body += grayText("Folder: ") + '<a href="%s">'%folderLink + folderLink + "</a><br>" + "\n"
    body += grayText("Log file: ") + '<a href="%s">'%directLinkToLogFile + directLinkToLogFile + "</a><br>" + "\n"
    body += grayText("Xml file: ") + '<a href="%s">'%directLinkToXmlFile + directLinkToXmlFile + "</a><br>" + "\n"
    utc, myTime_grafana = getTime(run["runDate"], timeFormat = "%Y-%m-%dT%H:%M:%S")
    from datetime import timedelta
    start_time_grafana = (myTime_grafana - timedelta(hours=2))
    stop_time_grafana = (myTime_grafana + timedelta(hours=2))
    GrafanaLink = "http://pccmslab1.pi.infn.it:3000/d/ff666241-736f-4d30-b490-dc8655d469a9/burn-in?orgId=1&%%20from={__from}\&to=%d&from=%d"%((int(start_time_grafana.timestamp())*1000), (int(stop_time_grafana.timestamp())*1000))
    start_time_grafana_d, start_time_grafana_t = str(start_time_grafana).split(" ")
    stop_time_grafana_d, stop_time_grafana_t = str(stop_time_grafana).split(" ")
    if start_time_grafana_d == stop_time_grafana_d:
        GrafanaText = "%s -> %s (%s)"%(start_time_grafana_t, stop_time_grafana_t, stop_time_grafana_d)
    else:
        GrafanaText = "%s %s -> %s %s"%(start_time_grafana_d, start_time_grafana_t, stop_time_grafana_d, stop_time_grafana_t)
    
    body += grayText("Link to Grafana (available only from INFN Pisa): ") + '<a href="%s">'%GrafanaLink + GrafanaText + "</a><br>" + "\n"
    
    ### Single Module Run
    boardToId = {v: k for k, v in run["runBoards"].items()}
    body += "<h1> %s %s  </h1>"%(grayText("Single Module Run:"), testID) + "\n"
#    date, time =  run['runDate'].split("T")
    body += grayText("Single Module Run: ") + testID + "<br>" +"\n"
    board_id = boardToId[str(test['board'])]
    optical_id = str(test['opticalGroupName'])
    body += grayText("Board: ") + str(test['board']) + grayText(". BoardId: ") + board_id + grayText(". OpticalGroup: ")  + optical_id + "<br>" +"\n"
    body += "<br>" + "\n"
#    body += grayText("NameId: ") + str(rootFile.Get("Detector/Board_%s/OpticalGroup_%s/D_B(%s)_NameId_OpticalGroup(%s)"%(board_id, optical_id, board_id, optical_id))) + "<br>" +"\n"
    body += grayText("LpGBTFuseId: ") + str(rootFile.Get("Detector/Board_%s/OpticalGroup_%s/D_B(%s)_LpGBTFuseId_OpticalGroup(%s)"%(board_id, optical_id, board_id, optical_id))) + "<br>" +"\n"
    body += grayText("VTRxFuseId: ") + str(rootFile.Get("Detector/Board_%s/OpticalGroup_%s/D_B(%s)_VTRxFuseId_OpticalGroup(%s)"%(board_id, optical_id, board_id, optical_id))) + "<br>" +"\n"
#    body += ". Date:" + date + ". Time:" + time + "<br>" +"\n"
#    directLinkToZip = run['runFile'].replace("files/link/public", "remote.php/dav/public-files")
#    folderLink =  '/'.join(run['runFile'].split("/")[:-1])
##    linkToROOTFile = folderLink.replace("files/link/public", "rootjs/public") + "Results/OT_ModuleTest_M103_Run176/Hybrid_jkkfb.root"
#    body += 'Zip file: <a href="%s">'%directLinkToZip + directLinkToZip + "</a><br>" + "\n"
#    body += 'Folder: <a href="%s">'%folderLink + folderLink + "</a><br>" + "\n"
    
    body += "<h1> %s  </h1>"%("SSA and MPA noise table") + "\n"
    body += makeNoiseTable(noisePerChip, board_id, optical_id)

    body += "<h1> %s  </h1>"%("SSA and MPA noise edge ratio table") + "\n"
    body += makeNoiseTable(noiseRatioPerChip, board_id, optical_id, ratio = True)
    
    html = html.replace("[ADD BODY]", body)

    print(noiseRatioPerChip)
#    1/0
    
    finalbody = "<h1> XML configuration </h1>" + "\n"
    import pprint
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

def getTime(time, timeFormat="%Y-%m-%dT%H:%M:%S"):
    from datetime import datetime, timedelta
    myTime = datetime.strptime(time, timeFormat)
    import pytz
    rome_timezone = pytz.timezone('Europe/Rome')
    rome_time = myTime.astimezone(rome_timezone)
    ## Move to UTC time
    myTime = myTime - rome_time.utcoffset()
    return myTime, rome_time

def makePlotInfluxdb(time, folder):
    print("makePlotInfluxdb")

    token_location = "~/private/influx.sct" 
    token = open(os.path.expanduser(token_location)).read()[:-1]
    
    from datetime import datetime, timedelta
    
    from influxdb_client import InfluxDBClient
    
    import numpy as np
    
    org = "pisaoutertracker"
    bucket = "sensor_data"
    
#    timeFormat = "%Y-%m-%dT%H:%M:%S"
    
#    currentTime = datetime.strptime(time, timeFormat)
#    import pytz
#    rome_timezone = pytz.timezone('Europe/Rome')
#    rome_time = currentTime.astimezone(rome_timezone)
#    ## Move to UTC time
#    currentTime = currentTime - rome_time.utcoffset()
    myTime, rome_time = getTime(time, timeFormat = "%Y-%m-%dT%H:%M:%S")

    start_time = (myTime - timedelta(hours=2)).isoformat("T") + "Z"
    stop_time = (myTime + timedelta(hours=2)).isoformat("T") + "Z"
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
    
    time = []
    value = []
    
    client = InfluxDBClient(url="http://cmslabserver:8086/", token=token)
    tables = client.query_api().query(query, org=org)
    client.__del__()
    
    for table in tables:
       for record in table.records:
           time.append(record.get_time())
           value.append(record.get_value())
    
    # Plot the data
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.figure(figsize=(10, 5))
    plt.plot(time, value, label=sensorName)
    plt.axvline(x=myTime, color='r', linestyle='--', label=myTime.strftime('%H:%M:%S'))
    ## Set the x and y axis labels
    timezone_h = "%+.1f"%(-rome_time.utcoffset().seconds/3600)
    plt.xlabel('UTC Time (= Rome Time %s h)'%timezone_h)
    plt.ylabel('Temperature')
    plt.title('Sensor Data Over Time')
    plt.legend()
    plt.grid(True)
    fName = folder+"/sensor_data_plot.png"
    
    ## Orario UTC
    plt.savefig(fName)
    print("InfluxDb: saved ", fName)
    
    # del plt
    
    # if not 'LC_ALL' in os.environ or os.environ['LC_ALL'] != 'C': 
    #     raise Exception('Please type on shell: export LC_ALL="C"')

#    import locale
#    locale.setlocale(locale.LC_ALL, 'C')
    
    return fName

def updateTestResult(module_test, skipWebdav = False):
    global plots
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
    if webdav_wrapper: 
        print("Downloading %s to %s"%(run['runFile'].split("//")[-1], "/tmp/%s"%fName))
        zip_file_path = webdav_wrapper.download_file(remote_path=run['runFile'].split("//")[-1] , local_path="/tmp/%s"%fName) ## drop
    else: zip_file_path = "/tmp/%s"%fName
    
    # Specify the directory where you want to extract the contents
    extracted_dir = zip_file_path.split(".")[0]

    # Open the zip file
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        # Extract all the contents into the specified directory
        zip_ref.extractall(extracted_dir)
    
    ## check if the file is there
    if os.path.exists(extracted_dir+"/Results.root"):
        rootFile = TFile.Open(extracted_dir+"/Results.root")
    elif os.path.exists(extracted_dir+"/Hybrid.root"):
        rootFile = TFile.Open(extracted_dir+"/Hybrid.root")
    else:
        raise Exception("No Results.root or Hybrid.root found in %s"%extracted_dir)
#    xmlConfig = readXmlConfig(xmlPyConfigFile=xmlPyConfigFile, folder=extracted_dir)
    xmlConfig = run["runConfiguration"] ## take configuration from db instead of python file
    print(xmlConfig)
    global noisePerChip
    noisePerChip = getNoisePerChip(rootFile , xmlConfig )
    noiseRatioPerChip = getNoisePerChip(rootFile , xmlConfig, ratio = True)
    moduleHwIDs = getIDsFromROOT(rootFile, xmlConfig)
    
#    for board_optical in moduleHwIDs:
#    board_id, opticalGroup_id = board_optical
    result = getResultPerModule(noisePerChip, xmlConfig, str(board_id), str(opticalGroup_id))
    plots = makePlots(rootFile, xmlConfig, board_id, opticalGroup_id, tmpFolder, run['runDate'])
    fff = plots+[xmlPyConfigFile]
    folder = "Module_%s_Run_%s_Result_%s"%(moduleName, runName, version)
    nfolder = base+folder
    print("mkDir %s"%nfolder)
    if webdav_website: webdav_website.mkDir(nfolder)
##        print(webdav_website.list_files(nfolder))
    fff = [f for f in fff if os.path.exists(f)]
#        newNames = uploadToWebDav(nfolder, fff)
    webpage = makeWebpage(rootFile, module_test, moduleName, runName, module, run, test, noisePerChip, noiseRatioPerChip, xmlConfig, board_id, opticalGroup_id, result, plots, xmlPyConfigFile, tmpFolder)
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
#        import locale
#        locale.setlocale(locale.LC_ALL, 'C')
        newFile = webdav_website.write_file(tmpUpFolder+name+".zip", "%s/results.zip"%(nfolder))
        if verbose>0: print("Uploaded %s"%newFile)
#        if webdav_website: newfile = webdav_website.write_file(webpage, nfolder+"/index.html")
#        print(webdav_website.list_files(nfolder))
    
#        for f in webdav_website.list_files("/test2/Module_PS_26_10-IPG_00103_Run_PS_26_10-IPG_00103__run6_Result_V3/"):
#            print (f)
    for p in plots:
        print(p)
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

    os.system("rm -rf /tmp/latest_ana")
    os.system("mv %s /tmp/latest_ana"%tmpFolder)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Script used to elaborate the results of the Phase-2 PS module test. More info at https://github.com/pisaoutertracker/BurnIn_moduleTest. \n Example: python3  updateTestResult.py PS_26_05-IBA_00102__run418 . ')
    parser.add_argument('module_test', type=str, help='Single-module test name')
    parser.add_argument('--skipWebdav', type=bool, nargs='?', const=True, default=False, help='Skip upload to webdav (for testing).')
    args = parser.parse_args()
    updateTestResult(args.module_test , args.skipWebdav )


