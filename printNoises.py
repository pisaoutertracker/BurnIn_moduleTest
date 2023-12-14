from tools import getROOTfile, getNoisePerChip, getResultPerModule, getIDsFromROOT
from ROOT import TFile

import sys
print(sys.argv)

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
    fNames = [
    
#        "/home/thermal/Ph2_ACF_docker/Results4/OT_ModuleTest_test_Run0/Hybrid.root", ## ??? Nov 23 16:26 0 
#        "/home/thermal/Ph2_ACF_docker/Results4/OT_ModuleTest_test_Run1/Hybrid.root", ## ??? Nov 23 16:53 -10
#        "/home/thermal/Ph2_ACF_docker/Results4/OT_ModuleTest_test_Run2/Hybrid.root", ## ??? Nov 23 17:17 -20
        #"/home/thermal/Ph2_ACF_docker/BurnIn_moduleTest/Results/OT_ModuleTest_M103_Run137/Hybrid.root", 
#        "/home/thermal/Ph2_ACF_docker/BurnIn_moduleTest/Results/OT_ModuleTest_T2023_12_04_17_52_39_141176_Run174/Hybrid.root", 
#        "/home/thermal/Ph2_ACF_docker/BurnIn_moduleTest/Results/OT_ModuleTest_T2023_12_04_17_27_49_862692_Run165/Hybrid.root", 
        "/home/thermal/Ph2_ACF_docker/BurnIn_moduleTest/Results/OT_ModuleTest_T2023_12_06_10_03_41_659414_Run186/Hybrid.root", 
     #   "/home/thermal/Ph2_ACF_docker/Results4/PS_26_5_IBA-00102_T0_v2p1_LV10.5/Hybrid.root",
     #   "/home/thermal/Ph2_ACF_docker/Results4/PS_26_5_IBA-00102_Tm20_v2p1_LV10.5/Hybrid.root",
     #   "/home/thermal/Ph2_ACF_docker/Results4/PS_26_5_IBA-00102_Tm30_v2p1_LV10.5/Hybrid.root",
     #   "/home/thermal/Ph2_ACF_docker/Results4/OT_ModuleTest_test_Run1/Hybrid.root", ## ??? Nov 23 16:53 -10
     #   "/home/thermal/Ph2_ACF_docker/Results4/OT_ModuleTest_test_Run2/Hybrid.root", ## ??? Nov 23 17:17 -20
     #   "/home/thermal/Ph2_ACF_docker/Results4/OT_ModuleTest_PS_26_5_IBA-00102_Run3/Hybrid.root", ## PS_Module_v2p1 -35
#        "/home/thermal/Ph2_ACF_docker/Results4/OT_ModuleTest_PS_26_5_IBA-00102_Run4/Hybrid.root"  ## PS_Module_v2
    ]
    if len(sys.argv)>1:
        fNames = sys.argv[1:]
        print(sys.argv)
    for fName in fNames:
        #testID = "test0gradi"
#        rootFile = getROOTfile(testID)
        rootFile = TFile.Open(fName)
        folder = '/'.join(fName.split("/")[:-1])
        xmlConfig = readXmlConfig(xmlConfigFile, folder = folder)
        noisePerChip = getNoisePerChip(rootFile , xmlConfig)
        from pprint import pprint
        print(fName)
        print("\nnoisePerChip:")
        pprint(noisePerChip)
#        result = getResultPerModule(noisePerChip, xmlConfig)
#        print("\nresult:")
#        pprint(result)
        for board_id, board in xmlConfig["boards"].items():
            for opticalGroup_id, opticalGroup in board["opticalGroups"].items():
                print("\nAverage Noise:")
                for hybrid_id, hybrid in opticalGroup["hybrids"].items():
                    hybrid_plus_opt = "H(%s)"%str(int(opticalGroup_id)*2 + int(hybrid_id)) ## H(0)
                    subset = [noisePerChip[chip] for chip in noisePerChip if hybrid_plus_opt in chip and "MPA" in chip ]
                    print("Hybrid%s - MPA: %f"%(hybrid_id, sum(subset)/len(subset)) )
                    subset = [noisePerChip[chip] for chip in noisePerChip if hybrid_plus_opt in chip and "SSA" in chip ]
                    print("Hybrid%s - SSA: %f"%(hybrid_id, sum(subset)/len(subset)) )
                    hybrid_plus_opt = "H(%s)"%str(int(opticalGroup_id)*2 + int(hybrid_id)) ## H(1)
                    subset = [noisePerChip[chip] for chip in noisePerChip if hybrid_plus_opt in chip and "MPA" in chip ]
                    print("Hybrid%s - MPA: %f"%(hybrid_id, sum(subset)/len(subset)) )
                    subset = [noisePerChip[chip] for chip in noisePerChip if hybrid_plus_opt in chip and "SSA" in chip ]
                    print("Hybrid%s - SSA: %f"%(hybrid_id, sum(subset)/len(subset)) )
        
        "D_B(0)_O(0)_H(0)_NoiseDistribution_Chip(0)SSA"
#        IDs = getIDsFromROOT(rootFile, xmlConfig)
#        print("\nIDs:")
#        pprint(IDs)
