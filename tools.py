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
        board_id = int(board_id)
        for opticalGroup_id, opticalGroup in board["opticalGroups"].items():
            opticalGroup_id = int(opticalGroup_id)
            newMethod = True
            if newMethod:
                objName = "Detector/Board_%s/OpticalGroup_%s/D_B(%s)_LpGBTFuseId_OpticalGroup(%s)"%(board_id, opticalGroup_id, board_id, opticalGroup_id)
                out = rootFile.Get(objName)
                if not out: 
                    print("WARNING: Missing %s in %s. Skipping."%(objName, rootFile.GetName()))
                    IDs[(board_id, opticalGroup_id)] = "-1"
                    continue
                IDs[(board_id, opticalGroup_id)] = {}
                out = str(out.GetString()) ## Select CHIPID section
                
                ## just take "CHIPID0" for the moment
                IDs[(board_id, opticalGroup_id)]= int(out)
            else:
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
                ##
                val = 0
                for i, key in enumerate(["CHIPID0","CHIPID1","CHIPID2","CHIPID3","USERID0","USERID1","USERID2","USERID3"]):
                    val = val + int(IDs[(board_id, opticalGroup_id)][key], 16) * (32**i)
                
                combineAllKeys = False
                if combineAllKeys:
                    IDs[(board_id, opticalGroup_id)] = val
                else:
                    ## just take "CHIPID0" for the moment
                    IDs[(board_id, opticalGroup_id)] = IDs[(board_id, opticalGroup_id)]["CHIPID0"] 
                

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

## Compute noise ration between the edge and the rest of the chip

def getNoiseRatio(rootFile, board_id, opticalGroup_id, hybrid_id, ps_id, chip):
    if not chip in allowedChips: raise Exception("Chip %s now allowed. Allowed chips: %s"%(chip, allowedChips))
    if chip == "MPA":
        histoName = "Detector/Board_%s/OpticalGroup_%s/Hybrid_%s/%s_%s/D_B(%s)_O(%s)_H(%s)_2DPixelNoise_Chip(%s)"%(board_id, opticalGroup_id, hybrid_id, chip, ps_id, board_id, opticalGroup_id, hybrid_id, ps_id)
        histo2D = rootFile.Get(histoName)
        if not histo2D: 
            print("WARNING: Missing %s in %s"%(histoName, rootFile.GetName()))
            return -1, histoName.split("/")[-1]+chip
        histo = histo2D.ProjectionX()
    elif chip == "SSA":
        histoName = "Detector/Board_%s/OpticalGroup_%s/Hybrid_%s/%s_%s/D_B(%s)_O(%s)_H(%s)_ChannelNoiseDistribution_Chip(%s)"%(board_id, opticalGroup_id, hybrid_id, chip, ps_id, board_id, opticalGroup_id, hybrid_id, ps_id)
        histo = rootFile.Get(histoName)
        if not histo: 
            print("WARNING: Missing %s in %s"%(histoName, rootFile.GetName()))
            return -1, histoName.split("/")[-1]+chip
    else:
        print(rootFile, board_id, opticalGroup_id, hybrid_id, ps_id, chip)
        raise Exception("Error in getNoiseRatio")
    edge = []
    central = []
    for i in range(1,histo.GetNbinsX()+1):
        if i<=2 or i>=histo.GetNbinsX()-1:
            edge.append(histo.GetBinContent(i))
        else:
            central.append(histo.GetBinContent(i))
    central = sum(central)/len(central)
    edge = sum(edge)/len(edge)
    
    if histo:
        if central>0:
            return edge/central, histoName.split("/")[-1]+chip
        else:
            return 999, histoName.split("/")[-1]+chip
    else:
        print("WARNING: Missing %s in %s"%(histoName, rootFile.GetName()))
        return -1, histoName.split("/")[-1]+chip
        
### Make a map [D_B(%s)_O(%s)_H(%s)_NoiseDistribution_Chip(%s) containing the mean noise of each chip per each module

def getNoisePerChip(rootFile, xmlConfig, ratio = False):
    if verbose>0: print("Calling getNoisePerChip()", rootFile.GetName())
    noisePerChip = {}
    for board_id, board in xmlConfig["boards"].items():
        for opticalGroup_id, opticalGroup in board["opticalGroups"].items():
            for hybrid_id, hybrid in opticalGroup["hybrids"].items():
                hybrid_plus_opt = str(int(opticalGroup_id)*2 + int(hybrid_id))
                noises = []
                if not "strips" in hybrid: hybrid["strips"]=[]
                for strip_id in hybrid["strips"]:
                    if ratio:
                        noise, histoName = getNoiseRatio(rootFile, board_id, opticalGroup_id, hybrid_plus_opt, strip_id, "SSA")
                    else:
                        noise, histoName = getMean(rootFile, board_id, opticalGroup_id, hybrid_plus_opt, strip_id, "SSA")
                    if histoName in noisePerChip: raise Exception("%s is already in noisePerChip (getNoisePerChip function): %s."%(histoName, noisePerChip.keys()))
                    noisePerChip[histoName] = noise
                    if noise>0: noises.append(noise)
                noisePerChip["Average_B%s_O%s_H%s_SSA"%(board_id, opticalGroup_id, hybrid_plus_opt)] = sum(noises)/len(noises) if len(noises)>0 else 0
                noisePerChip["Maximum_B%s_O%s_H%s_SSA"%(board_id, opticalGroup_id, hybrid_plus_opt)] = max(noises) if len(noises)>0 else 0
                noisePerChip["Minimum_B%s_O%s_H%s_SSA"%(board_id, opticalGroup_id, hybrid_plus_opt)] = min(noises) if len(noises)>0 else 0
                noises = []
                if not "pixels" in hybrid: hybrid["pixels"]=[]
                for pixel_id in hybrid["pixels"]:
                    if ratio:
                        noise, histoName = getNoiseRatio(rootFile, board_id, opticalGroup_id, hybrid_plus_opt, pixel_id, "MPA")
                    else:
                        noise, histoName = getMean(rootFile, board_id, opticalGroup_id, hybrid_plus_opt, pixel_id, "MPA")
                    if histoName in noisePerChip: raise Exception("%s is already in noisePerChip (getNoisePerChip function): %s."%(histoName, noisePerChip.keys()))
                    noisePerChip[histoName] = noise
                    if noise>0: noises.append(noise)
                noisePerChip["Average_B%s_O%s_H%s_MPA"%(board_id, opticalGroup_id, hybrid_plus_opt)] = sum(noises)/len(noises) if len(noises)>0 else 0
                noisePerChip["Maximum_B%s_O%s_H%s_MPA"%(board_id, opticalGroup_id, hybrid_plus_opt)] = max(noises) if len(noises)>0 else 0
                noisePerChip["Minimum_B%s_O%s_H%s_MPA"%(board_id, opticalGroup_id, hybrid_plus_opt)] = min(noises) if len(noises)>0 else 0
    return noisePerChip

### Make an output result "pass" or "failed" depending on the noise of all the chips of a single module.
##TODO

def getResultsPerModule(noisePerChip, xmlConfig):
    results = {}
    for board_id, board in xmlConfig["boards"].items():
        results[board_id] = {}
        for opticalGroup_id, opticalGroup in board["opticalGroups"].items():
            results[opticalGroup_id] = getResultPerModule(noisePerChip, xmlConfig, board_id, opticalGroup_id)
    return results

def getResultPerModule(noisePerChip, xmlConfig, board_id, opticalGroup_id):
    try:
        opticalGroup = xmlConfig["boards"][board_id]["opticalGroups"][opticalGroup_id]
    except:
        opticalGroup = xmlConfig["boards"][int(board_id)]["opticalGroups"][int(opticalGroup_id)]
    for hybrid_id, hybrid in opticalGroup["hybrids"].items():
        hybrid_plus_opt = str(int(opticalGroup_id)*2 + int(hybrid_id))
        for strip_id in hybrid["strips"]:
            noise = noisePerChip ["D_B(%s)_O(%s)_H(%s)_NoiseDistribution_Chip(%s)SSA"%(board_id, opticalGroup_id, hybrid_plus_opt, strip_id)]
            if noise>5 or noise<0: return "failed"
        for pixel_id in hybrid["pixels"]:
            noise = noisePerChip ["D_B(%s)_O(%s)_H(%s)_NoiseDistribution_Chip(%s)MPA"%(board_id, opticalGroup_id, hybrid_plus_opt, pixel_id)]
            if noise>5 or noise<0: return "failed"
    
    return "pass"

### Open the ROOT file with the results of the corresponding testID

def getInfoFromXml(xmlPyConfigFile):
    from makeXml import readXmlConfig
    xmlConfig = readXmlConfig(xmlPyConfigFile)
    return xmlConfig

def getROOTfile(testID):
    import ROOT, os
    matches = [folder for folder in os.listdir("Results") if testID in folder ]
    if len(matches) != 1: raise Exception("%d matches of %s in ./Results/ folder. %s"%( len(matches), testID, str(matches)))
    fName = "Results/%s/Results.root"%matches[0]
    return ROOT.TFile.Open(fName)


### This code allow you to test this code using "python3 tools.py"

import xml.etree.ElementTree as ET


def parse_module_settings(xml_file):
    """
    Parse the given ModuleTest_settings.xml file and extract:
      - board: The board host extracted from the connection URI (e.g., "fc7ot3")
      - slots: A list of OpticalGroup Ids (each as integer)
      - hybrids: A list of Hybrid Ids present in all OpticalGroup elements
      - strips: A sorted list of unique SSA2 Ids collected from all Hybrid elements
      - pixels: A sorted list of unique MPA2 Ids collected from all Hybrid elements
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Extract board URI from <connection id="board"> and get the host part.
    connection_elem = root.find(".//BeBoard/connection[@id='board']")
    board_uri = connection_elem.get("uri")  # e.g., "ipbusudp-2.0://fc7ot3:50001"
    board = board_uri.split("://")[1].split(":")[0]

    # Find all OpticalGroup elements under BeBoard.
    optical_groups = root.findall(".//BeBoard/OpticalGroup")
    slots = []
    hybrids = []
    pixel_set = set()
    strip_set = set()

    for optical_group in optical_groups:
        # Add OpticalGroup Id to slots list.
        try:
            slot_id = int(optical_group.get("Id"))
            slots.append(slot_id)
        except (TypeError, ValueError):
            pass

        # Find all Hybrid elements under this OpticalGroup.
        hybrid_elements = optical_group.findall("Hybrid")
        hybrids.extend([int(hybrid.get("Id")) for hybrid in hybrid_elements if hybrid.get("Id") is not None])
        
        # For each Hybrid, look for any SSA2 and MPA2 elements.
        for hybrid in hybrid_elements:
            for ssa2 in hybrid.findall("SSA2"):
                try:
                    ssa2_id = int(ssa2.get("Id"))
                    strip_set.add(ssa2_id)
                except (TypeError, ValueError):
                    pass

            for mpa2 in hybrid.findall("MPA2"):
                try:
                    mpa2_id = int(mpa2.get("Id"))
                    pixel_set.add(mpa2_id)
                except (TypeError, ValueError):
                    pass

    # Convert sets to sorted lists.
    strips = sorted(list(strip_set))
    pixels = sorted(list(pixel_set))

    return board, slots, hybrids, strips, pixels

def checkAndFixRunNumbersDat(file="RunNumbers.dat", target_dir="~"):
    import os
    target = os.path.expanduser(os.path.join(target_dir, file))
    if os.path.abspath(target) == os.path.abspath(os.path.join(".", file)):
        print("You are in %s folder, and you have already %s file in %s. Nothing to do."%(target_dir, file, os.path.abspath(target)))
        return
    old_file = file + ".old"
    try:
        if os.path.exists(file):
            if os.path.isfile(file) and not os.path.islink(file) :
                os.rename(file, old_file)
                os.symlink(target, file)
                print(f"Moved {file} -> {old_file}, symlinked to {target}")
            elif os.path.islink(file) and os.readlink(file) != target:
                os.remove(file)
                os.symlink(target, file)
                print(f"Replaced incorrect symlink, now points to {target}")
            elif os.path.islink(file): # correct symlink
                print(f"{file} is already a correct symlink")
            else:  # Other file types
                print(f"{file} exists but is not a file or symlink. Doing nothing.")
        else:
            if not os.path.exists(target):  # Create target if it doesn't exist
                open(target, 'w').close()
            os.symlink(target, file)
            print(f"Created symlink {file} -> {target}")
    except OSError as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    filename = "ModuleTest_settings.xml"
    board, slots, hybrids, strips, pixels = parse_module_settings(filename)
    print("Slot:", slot)
    print("Board:", boad)
    print("Pixel channels:", pixel)
    print("Strip channels:", strip)
    print("Hybrids:", hybrids)
#    testID = "T2023_11_08_17_57_54_302065"
#    testID = "T2023_11_08_17_57_54_302065"
#    testID = "T2023_11_10_12_04_28_794907"
#    testID = "T2023_11_10_12_17_23_775314"
#    testID = "T2023_11_10_11_59_35_809872"
#    testID = "T2023_11_08_18_59_35_892171"
#    testID = "T2023_11_08_17_57_54_302065"
    testID = "test10gradi"
    #testID = "test0gradi"
    xmlPyConfigFile = "PS_Module_settings.py"
    rootFile = getROOTfile(testID)
    from makeXml import readXmlConfig
    xmlConfig = readXmlConfig(xmlPyConfigFile)
    noisePerChip = getNoisePerChip(rootFile , xmlConfig)
    noiseRatioPerChip = getNoisePerChip(rootFile , xmlConfig, ratio = True)
    from pprint import pprint
    print("\nnoisePerChip:")
    pprint(noisePerChip)
    result = getResultPerModule(noisePerChip, xmlConfig)
    print("\nresult:")
    pprint(result)
    IDs = getIDsFromROOT(rootFile, xmlConfig)
    print("\nIDs:")
    pprint(IDs)


    

