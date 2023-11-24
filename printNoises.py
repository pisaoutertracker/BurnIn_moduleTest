from tools import getROOTfile, getNoisePerChip, getResultPerModule, getIDsFromROOT
from ROOT import TFile

if __name__ == '__main__':
#    testID = "T2023_11_08_17_57_54_302065"
#    testID = "T2023_11_08_17_57_54_302065"
#    testID = "T2023_11_10_12_04_28_794907"
#    testID = "T2023_11_10_12_17_23_775314"
#    testID = "T2023_11_10_11_59_35_809872"
#    testID = "T2023_11_08_18_59_35_892171"
#    testID = "T2023_11_08_17_57_54_302065"
    xmlConfigFile = "PS_Module_settings.py"
    from makeXml import readXmlConfig
    xmlConfig = readXmlConfig(xmlConfigFile)
    fNames = [
    
#        "/home/thermal/Ph2_ACF_docker/Results4/OT_ModuleTest_test_Run0/Hybrid.root", ## ??? Nov 23 16:26 0 
#        "/home/thermal/Ph2_ACF_docker/Results4/OT_ModuleTest_test_Run1/Hybrid.root", ## ??? Nov 23 16:53 -10
#        "/home/thermal/Ph2_ACF_docker/Results4/OT_ModuleTest_test_Run2/Hybrid.root", ## ??? Nov 23 17:17 -20
        "/home/thermal/Ph2_ACF_docker/Results4/PS_26_5_IBA-00102_T10_v2p1_LV10.5/Hybrid.root", 
        "/home/thermal/Ph2_ACF_docker/Results4/PS_26_5_IBA-00102_T0_v2p1_LV10.5/Hybrid.root",
        "/home/thermal/Ph2_ACF_docker/Results4/PS_26_5_IBA-00102_Tm20_v2p1_LV10.5/Hybrid.root",
        "/home/thermal/Ph2_ACF_docker/Results4/PS_26_5_IBA-00102_Tm30_v2p1_LV10.5/Hybrid.root",
        "/home/thermal/Ph2_ACF_docker/Results4/OT_ModuleTest_test_Run1/Hybrid.root", ## ??? Nov 23 16:53 -10
        "/home/thermal/Ph2_ACF_docker/Results4/OT_ModuleTest_test_Run2/Hybrid.root", ## ??? Nov 23 17:17 -20
        "/home/thermal/Ph2_ACF_docker/Results4/OT_ModuleTest_PS_26_5_IBA-00102_Run3/Hybrid.root", ## PS_Module_v2p1 -35
#        "/home/thermal/Ph2_ACF_docker/Results4/OT_ModuleTest_PS_26_5_IBA-00102_Run4/Hybrid.root"  ## PS_Module_v2
    ]
    for fName in fNames:
        #testID = "test0gradi"
#        rootFile = getROOTfile(testID)
        rootFile = TFile.Open(fName)
        noisePerChip = getNoisePerChip(rootFile , xmlConfig)
        from pprint import pprint
        print(fName)
        print("\nnoisePerChip:")
#        pprint(noisePerChip)
#        result = getResultPerModule(noisePerChip, xmlConfig)
#        print("\nresult:")
#        pprint(result)
        print("\nAverage Noise:")
        subset = [noisePerChip[chip] for chip in noisePerChip if "H(0)" in chip and "MPA" in chip ]
        print("H0 - MPA: %f"%(sum(subset)/len(subset)) )
        subset = [noisePerChip[chip] for chip in noisePerChip if "H(0)" in chip and "SSA" in chip ]
        print("H0 - SSA: %f"%(sum(subset)/len(subset)) )
        subset = [noisePerChip[chip] for chip in noisePerChip if "H(1)" in chip and "MPA" in chip ]
        print("H1 - MPA: %f"%(sum(subset)/len(subset)) )
        subset = [noisePerChip[chip] for chip in noisePerChip if "H(1)" in chip and "SSA" in chip ]
        print("H1 - SSA: %f"%(sum(subset)/len(subset)) )
        
        "D_B(0)_O(0)_H(0)_NoiseDistribution_Chip(0)SSA"
#        IDs = getIDsFromROOT(rootFile, xmlConfig)
#        print("\nIDs:")
#        pprint(IDs)
