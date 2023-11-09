from moduleTest import verbose

#date, testID = getDateTimeAndTestID()

### Get hardware ID from ot_module_test log (obsolete)

def getID(output):
    output = output.stdout.decode() + output.stderr.decode()
    tag_word = "Fused Id is "
    id_pos = output.find(tag_word)
    id_txt = output[id_pos+len(tag_word):id_pos+20]
    id_txt = id_txt.split("\n")[0]
    if not id_txt.isdigit():
        raise Exception("Something wrong in getID() |%s|"%id_txt)
    return id_txt

### Get the lpGBT hardware ID for each module from the ROOT file (CHIPID registers, CHIPID0)
# Note: each module is identified by (board_id, opticalGroup_id)
# IDs is a map: IDs[(board_id, opticalGroup_id)] --> hardware ID

def getIDsFromROOT(rootFile, xmlConfig):
    if verbose>1: print("Calling getIDsFromROOT()", rootFile)
    IDs = {}
    for board_id, board in xmlConfig["boards"].items():
        for opticalGroup_id, opticalGroup in board["opticalGroups"].items():
            objName = "Detector/Board_%s/OpticalGroup_%s/D_B(%s)_InitialLpGBTConfiguration_OpticalGroup(%s);1"%(board_id, opticalGroup_id, board_id, opticalGroup_id)
            out = rootFile.Get(objName)
            if not out: 
                print("WARNING: Missing %s in %s. Skipping."%(objName, rootFile.GetName()))
                IDs[(board_id, opticalGroup_id)] = "-1"
                continue
            IDs[(board_id, opticalGroup_id)] = {}
            out = str(out.GetString()).split("CHIPID registers")[1].split("RegName")[1] ## Select CHIPID section
            for l in out.split("\n"):
                l = l.replace("     "," ").replace("    "," ").replace("   "," ").replace("  "," ")
                l = l.split(" ")
                if len(l)==5:
                    IDs[(board_id, opticalGroup_id)][l[0]]= l[3]
            ## just take "CHIPID0" for the moment
            IDs[(board_id, opticalGroup_id)]= IDs[(board_id, opticalGroup_id)]["CHIPID0"]
    return IDs

### Get mean of noise of chip board_id, opticalGroup_id, hybrid_id, ps_id for MPA (pixels) or SSA(strips)

allowedChips = ["MPA", "SSA"]
def getMean(rootFile, board_id, opticalGroup_id, hybrid_id, ps_id, chip):
    if not chip in allowedChips: raise Exception("Chip %s now allowed. Allowed chips: %s"%(chip, allowedChips))  
    histoName = "Detector/Board_%s/OpticalGroup_%s/Hybrid_%s/%s_%s/D_B(%s)_O(%s)_H(%s)_NoiseDistribution_Chip(%s)"%(board_id, opticalGroup_id, hybrid_id, chip, ps_id, board_id, opticalGroup_id, hybrid_id, ps_id)
    histo = rootFile.Get(histoName)
    if histo:
        return histo.GetMean(), histoName.split("/")[-1]+chip
    else:
        print("WARNING: Missing %s in %s"%(histoName, rootFile.GetName()))
        return -1, histoName.split("/")[-1]+chip

### Make a map [D_B(%s)_O(%s)_H(%s)_NoiseDistribution_Chip(%s) containing the mean noise of each chip per each module

def getNoise(rootFile, xmlConfig):
    if verbose>0: print("Calling getNoise()", rootFile.GetName())
    noises = {}
    for board_id, board in xmlConfig["boards"].items():
        for opticalGroup_id, opticalGroup in board["opticalGroups"].items():
            for hybrid_id, hybrid in opticalGroup["hybrids"].items():
                if not "strips" in hybrid: hybrid["strips"]=[]
                for strip_id in hybrid["strips"]:
                    noise, histoName = getMean(rootFile, board_id, opticalGroup_id, hybrid_id, strip_id, "SSA")
                    if histoName in noises: raise Exception("%s is already in noises (getNoise function): %s."%(histoName, noises.keys()))
                    noises[histoName] = noise
                if not "pixels" in hybrid: hybrid["pixels"]=[]
                for pixel_id in hybrid["pixels"]:
                    noise, histoName = getMean(rootFile, board_id, opticalGroup_id, hybrid_id, pixel_id, "MPA")
                    if histoName in noises: raise Exception("%s is already in noises (getNoise function): %s."%(histoName, noises.keys()))
                    noises[histoName] = noise
    return noises

### Make an output result "pass" or "failed" depending on the noise of all the chips of a single module.
##TODO
def getResult(noises):
    for noise in noises.values():
        if noise>5 or noise<2:
            return "failed"
    return "pass"

### Open the ROOT file with the results of the corresponding testID

def getROOTfile(testID):
    import ROOT, os
    matches = [folder for folder in os.listdir("Results") if testID in folder ]
    if len(matches) != 1: raise Exception("%d matches of %s in Result folder. %s"%( len(matches), testID, str(matches)))
    fName = "Results/%s/Hybrid.root"%matches[0]
    return ROOT.TFile.Open(fName)


### This code allow you to test this code using "python3 tools.py"

if __name__ == '__main__':
    testID = "T2023_11_08_17_57_54_302065"
    xmlConfigFile = "PS_Module_settings.py"
    rootFile = getROOTfile(testID)
    from makeXml import readXmlConfig
    xmlConfig = readXmlConfig(xmlConfigFile)
    noises = getNoise(rootFile , xmlConfig)
    from pprint import pprint
    print("\nnoises:")
    pprint(noises)
    result = getResult(noises)
    print("\nresult:")
    pprint(result)
    IDs = getIDsFromROOT(rootFile, xmlConfig)
    print("\nIDs:")
    pprint(IDs)

