cernbox_folder_analysis = "/home/thermal/cernbox_shared/Uploads/"
cernbox_folder_run = "/home/thermal/cernbox_runshared/"
cernbox_computer = "cmslabburnin"

from datetime import datetime,timedelta

#from tools import getROOTfile, getNoisePerChip, getResultPerModule, getIDsFromROOT
from ROOT import TFile, TCanvas, gROOT, TH1F, TH2F, gStyle, TGraphErrors
import os
from databaseTools import getTestFromDB, getModuleTestFromDB, getRunFromDB, getModuleFromDB, makeModuleNameMapFromDB
import zipfile
from tools import getNoisePerChip, getIDsFromROOT, getResultPerModule
#from makeXml import readXmlConfig
# from webdavclient import WebDAVWrapper
from moduleTest import verbose,webdav_url, xmlPyConfigFile, hash_value_read, hash_value_write ## to be updated

verbose = 100000


useOnlyMergedPlots = True
version = "2025-10-22"
#version = "2025-04-29"

skipInfluxDb= False
#skipInfluxDb= True

allVariables = [
    "OccupancyAfterOffsetEqualization",
    "Occupancy",
    "OffsetValues",
    "VplusValue", 
    "ChannelPedestalDistribution",
    "ChannelNoiseDistribution",
    "2DChannelOffsetValues", 
    "2DChannelOccupancyAfterOffsetEqualization", 
    "SCurve", 
    "PedestalDistribution", 
    "ChannelPedestal", 
    "NoiseDistribution", 
    "ChannelNoise", 
    "2DChannelNoise", 
    "2DPixelNoise", 
    "2DChannelNoiseDistribution", 
    "2DPixelNoiseDistribution",
    "ChannelOffsetValues",
    "VREF_DACtoV",
    "ADC_Slope",
    "ThresholdVsDelayScan",
    "BestThresholdAndDelay",
    "ChannelOccupancy_Injection_0.000_MIP",
    "ChannelOccupancy_Injection_0.250_MIP",
    "ChannelOccupancy_Injection_0.500_MIP",
    "ChannelOccupancy_Injection_1.000_MIP",
    "ChannelOccupancy_Injection_2.000_MIP",
    "CommonNoiseHits_OccupancyDriven",
    "CommonNoiseHits_SigmaNoise_3.000",
]


hybridPlots = [
    "BitSlipValues", 
    "WordAlignmentRetryNumbers", 

    "HybridStripNoiseDistribution", 
    "HybridPixelNoiseDistribution", 
    "HybridNoiseDistribution",
    "PatternMatchingEfficiency", 
    "CICinputPhaseHistogram", 
    "BestCICinputPhases", 
    "LockingEfficiencyCICinput", 
    "CICwordAlignmentDelay", 
    "PatternMatchingEfficiencyCIC", 
    "PatternMatchingEfficiencyMPA_SSA",
    "StripHybridHits",
    "MPAringOscillatorInverterCounts", 
    "MPAringOscillatorDelayCounts", 
    "SSAringOscillatorInverterCounts", 
    "SSAringOscillatorDelayCounts", 
    "PixelHybridHits", 
    "SSA(0)toMPA(8)_correlation", 
    "SSA(1)toMPA(9)_correlation", 
    "SSA(2)toMPA(10)_correlation", 
    "SSA(3)toMPA(11)_correlation", 
    "SSA(4)toMPA(12)_correlation", 
    "SSA(5)toMPA(13)_correlation", 
    "SSA(6)toMPA(14)_correlation", 
    "SSA(7)toMPA(15)_correlation", 
    "StripPixelHybridHits", 
    "Efficiency_CIC_Clock_Polarity_0-CIC_Signal_Strength_1-Clock_Strength_1", 
    "Efficiency_CIC_Clock_Polarity_0-CIC_Signal_Strength_1-Clock_Strength_4", 
    "Efficiency_CIC_Clock_Polarity_0-CIC_Signal_Strength_1-Clock_Strength_7", 
    "Efficiency_CIC_Clock_Polarity_0-CIC_Signal_Strength_3-Clock_Strength_1", 
    "Efficiency_CIC_Clock_Polarity_0-CIC_Signal_Strength_3-Clock_Strength_4", 
    "Efficiency_CIC_Clock_Polarity_0-CIC_Signal_Strength_3-Clock_Strength_7", 
    "Efficiency_CIC_Clock_Polarity_0-CIC_Signal_Strength_5-Clock_Strength_1", 
    "Efficiency_CIC_Clock_Polarity_0-CIC_Signal_Strength_5-Clock_Strength_4", 
    "Efficiency_CIC_Clock_Polarity_0-CIC_Signal_Strength_5-Clock_Strength_7", 
    "Efficiency_CIC_Clock_Polarity_1-CIC_Signal_Strength_1-Clock_Strength_1", 
    "Efficiency_CIC_Clock_Polarity_1-CIC_Signal_Strength_1-Clock_Strength_4", 
    "Efficiency_CIC_Clock_Polarity_1-CIC_Signal_Strength_1-Clock_Strength_7", 
    "Efficiency_CIC_Clock_Polarity_1-CIC_Signal_Strength_3-Clock_Strength_1", 
    "Efficiency_CIC_Clock_Polarity_1-CIC_Signal_Strength_3-Clock_Strength_4", 
    "Efficiency_CIC_Clock_Polarity_1-CIC_Signal_Strength_3-Clock_Strength_7", 
    "Efficiency_CIC_Clock_Polarity_1-CIC_Signal_Strength_5-Clock_Strength_1", 
    "Efficiency_CIC_Clock_Polarity_1-CIC_Signal_Strength_5-Clock_Strength_4", 
    "Efficiency_CIC_Clock_Polarity_1-CIC_Signal_Strength_5-Clock_Strength_7", 
    "SSAtoMPAStubPhaseScan_SLVScurrent_1", 
    "SSAtoMPAL1PhaseScan_SLVScurrent_1", 
    "SSAtoMPAStubPhaseScan_SLVScurrent_4", 
    "SSAtoMPAL1PhaseScan_SLVScurrent_4", 
    "SSAtoMPAStubPhaseScan_SLVScurrent_7", 
    "SSAtoMPAL1PhaseScan_SLVScurrent_7", 
    "SSAtoSSAStubPhaseScan_SLVScurrent_1", 
    "SSAtoSSAStubPhaseScan_SLVScurrent_4", 
    "SSAtoSSAStubPhaseScan_SLVScurrent_7", 
    "LpGBTforCICbypassPhaseScan_phyPort0", 
    "LpGBTforCICbypassBestPhase_phyPort0", 
    "LpGBTforCICbypassPhaseScan_phyPort1", 
    "LpGBTforCICbypassBestPhase_phyPort1", 
    "LpGBTforCICbypassPhaseScan_phyPort2", 
    "LpGBTforCICbypassBestPhase_phyPort2", 
    "LpGBTforCICbypassPhaseScan_phyPort3", 
    "LpGBTforCICbypassBestPhase_phyPort3", 
    "LpGBTforCICbypassPhaseScan_phyPort4", 
    "LpGBTforCICbypassBestPhase_phyPort4", 
    "LpGBTforCICbypassPhaseScan_phyPort5", 
    "LpGBTforCICbypassBestPhase_phyPort5", 
    "LpGBTforCICbypassPhaseScan_phyPort6", 
    "LpGBTforCICbypassBestPhase_phyPort6", 
    "LpGBTforCICbypassPhaseScan_phyPort7", 
    "LpGBTforCICbypassBestPhase_phyPort7", 
    "LpGBTforCICbypassPhaseScan_phyPort8", 
    "LpGBTforCICbypassBestPhase_phyPort8", 
    "LpGBTforCICbypassPhaseScan_phyPort9", 
    "LpGBTforCICbypassBestPhase_phyPort9", 
    "LpGBTforCICbypassPhaseScan_phyPort10", 
    "LpGBTforCICbypassBestPhase_phyPort10", 
    "LpGBTforCICbypassPhaseScan_phyPort11", 
    "LpGBTforCICbypassBestPhase_phyPort11", 
    "MPAtoCICPhaseScan_SLVScurrent_1", 
    "MPAtoCICPhaseScan_SLVScurrent_4", 
    "MPAtoCICPhaseScan_SLVScurrent_7", 
    "RegisterMatchingEfficiency",

    "Board_WordAlignmentBitSlipValues",
    "Board_WordAlignmentRetryNumbers",
    "CICtoLpGBT_PatternMatchingErrorRate",
    "CICtoLpGBT_PatternMatchingTestedBits",

    "MPAtoCIC_InputPhaseDistribution",
    "MPAtoCIC_BestInputPhases",
    "MPAtoCIC_LockingEfficiency",
    "MPAtoCIC_WordAlignmentDelay",
    "MPAtoCIC_PatternMatchingTestedBits",
    "MPAtoCIC_PatternMatchingErrorRate",
    "SSAtoMPA_PatternMatchingTestedBits",
    "SSAtoMPA_PatternMatchingErrorRate",
    "MPA_RingOscillatorInverterCounts",
    "MPA_RingOscillatorDelayCounts",
    "SSA_RingOscillatorInverterCounts",
    "SSA_RingOscillatorDelayCounts",

    "StripChannelNoise",
    "PixelChannelNoise",
    "StripNoiseDistribution",
    "PixelNoiseDistribution",

    "CommonNoiseHitsStrip_OccupancyDriven",
    "CommonNoiseHitsPixel_OccupancyDriven",
    "SSA(0)toMPA(8)_CommonNoiseCorrelation_OccupancyDriven",
    "SSA(1)toMPA(9)_CommonNoiseCorrelation_OccupancyDriven",
    "SSA(2)toMPA(10)_CommonNoiseCorrelation_OccupancyDriven",
    "SSA(3)toMPA(11)_CommonNoiseCorrelation_OccupancyDriven",
    "SSA(4)toMPA(12)_CommonNoiseCorrelation_OccupancyDriven",
    "SSA(5)toMPA(13)_CommonNoiseCorrelation_OccupancyDriven",
    "SSA(6)toMPA(14)_CommonNoiseCorrelation_OccupancyDriven",
    "SSA(7)toMPA(15)_CommonNoiseCorrelation_OccupancyDriven",
    "CommonNoiseStripPixelCorrelation_OccupancyDriven",
    "CommonNoiseHitsStrip_SigmaNoise_3.000",
    "CommonNoiseHitsPixel_SigmaNoise_3.000",
    "SSA(0)toMPA(8)_CommonNoiseCorrelation_SigmaNoise_3.000",
    "SSA(1)toMPA(9)_CommonNoiseCorrelation_SigmaNoise_3.000",
    "SSA(2)toMPA(10)_CommonNoiseCorrelation_SigmaNoise_3.000",
    "SSA(3)toMPA(11)_CommonNoiseCorrelation_SigmaNoise_3.000",
    "SSA(4)toMPA(12)_CommonNoiseCorrelation_SigmaNoise_3.000",
    "SSA(5)toMPA(13)_CommonNoiseCorrelation_SigmaNoise_3.000",
    "SSA(6)toMPA(14)_CommonNoiseCorrelation_SigmaNoise_3.000",
    "SSA(7)toMPA(15)_CommonNoiseCorrelation_SigmaNoise_3.000",
    "CommonNoiseStripPixelCorrelation_SigmaNoise_3.000",
    "SSAtoMPA_SamplingEdgeErrorRate_SSA_SLVScurrent_1",
    "SSAtoMPA_SamplingEdgeTestedBits_SSA_SLVScurrent_1",
    "SSAtoMPA_SamplingEdgeErrorRate_SSA_SLVScurrent_4",
    "SSAtoMPA_SamplingEdgeTestedBits_SSA_SLVScurrent_4",
    "SSAtoMPA_SamplingEdgeErrorRate_SSA_SLVScurrent_7",
    "SSAtoMPA_SamplingEdgeTestedBits_SSA_SLVScurrent_7",
    "SSAtoSSA_SamplingEdgeErrorRate_SSA_SLVScurrent_1",
    "SSAtoSSA_SamplingEdgeTestedBits_SSA_SLVScurrent_1",
    "SSAtoSSA_SamplingEdgeErrorRate_SSA_SLVScurrent_4",
    "SSAtoSSA_SamplingEdgeTestedBits_SSA_SLVScurrent_4",
    "SSAtoSSA_SamplingEdgeErrorRate_SSA_SLVScurrent_7",
    "SSAtoSSA_SamplingEdgeTestedBits_SSA_SLVScurrent_7",
    "CICtoLpGBT_PatternMatchingTestedBits_CIC_SLVScurrent_1_LpGBT_Clock_Polarity_0_Clock_Strength_1",
    "CICtoLpGBT_PatternMatchingErrorRate_CIC_SLVScurrent_1_LpGBT_Clock_Polarity_0_Clock_Strength_1",
    "CICtoLpGBT_PatternMatchingTestedBits_CIC_SLVScurrent_1_LpGBT_Clock_Polarity_0_Clock_Strength_4",
    "CICtoLpGBT_PatternMatchingErrorRate_CIC_SLVScurrent_1_LpGBT_Clock_Polarity_0_Clock_Strength_4",
    "CICtoLpGBT_PatternMatchingTestedBits_CIC_SLVScurrent_1_LpGBT_Clock_Polarity_0_Clock_Strength_7",
    "CICtoLpGBT_PatternMatchingErrorRate_CIC_SLVScurrent_1_LpGBT_Clock_Polarity_0_Clock_Strength_7",
    "CICtoLpGBT_PatternMatchingTestedBits_CIC_SLVScurrent_3_LpGBT_Clock_Polarity_0_Clock_Strength_1",
    "CICtoLpGBT_PatternMatchingErrorRate_CIC_SLVScurrent_3_LpGBT_Clock_Polarity_0_Clock_Strength_1",
    "CICtoLpGBT_PatternMatchingTestedBits_CIC_SLVScurrent_3_LpGBT_Clock_Polarity_0_Clock_Strength_4",
    "CICtoLpGBT_PatternMatchingErrorRate_CIC_SLVScurrent_3_LpGBT_Clock_Polarity_0_Clock_Strength_4",
    "CICtoLpGBT_PatternMatchingTestedBits_CIC_SLVScurrent_3_LpGBT_Clock_Polarity_0_Clock_Strength_7",
    "CICtoLpGBT_PatternMatchingErrorRate_CIC_SLVScurrent_3_LpGBT_Clock_Polarity_0_Clock_Strength_7",
    "CICtoLpGBT_PatternMatchingTestedBits_CIC_SLVScurrent_5_LpGBT_Clock_Polarity_0_Clock_Strength_1",
    "CICtoLpGBT_PatternMatchingErrorRate_CIC_SLVScurrent_5_LpGBT_Clock_Polarity_0_Clock_Strength_1",
    "CICtoLpGBT_PatternMatchingTestedBits_CIC_SLVScurrent_5_LpGBT_Clock_Polarity_0_Clock_Strength_4",
    "CICtoLpGBT_PatternMatchingErrorRate_CIC_SLVScurrent_5_LpGBT_Clock_Polarity_0_Clock_Strength_4",
    "CICtoLpGBT_PatternMatchingTestedBits_CIC_SLVScurrent_5_LpGBT_Clock_Polarity_0_Clock_Strength_7",
    "CICtoLpGBT_PatternMatchingErrorRate_CIC_SLVScurrent_5_LpGBT_Clock_Polarity_0_Clock_Strength_7",
    "CICtoLpGBT_PatternMatchingTestedBits_CIC_SLVScurrent_1_LpGBT_Clock_Polarity_1_Clock_Strength_1",
    "CICtoLpGBT_PatternMatchingErrorRate_CIC_SLVScurrent_1_LpGBT_Clock_Polarity_1_Clock_Strength_1",
    "CICtoLpGBT_PatternMatchingTestedBits_CIC_SLVScurrent_1_LpGBT_Clock_Polarity_1_Clock_Strength_4",
    "CICtoLpGBT_PatternMatchingErrorRate_CIC_SLVScurrent_1_LpGBT_Clock_Polarity_1_Clock_Strength_4",
    "CICtoLpGBT_PatternMatchingTestedBits_CIC_SLVScurrent_1_LpGBT_Clock_Polarity_1_Clock_Strength_7",
    "CICtoLpGBT_PatternMatchingErrorRate_CIC_SLVScurrent_1_LpGBT_Clock_Polarity_1_Clock_Strength_7",
    "CICtoLpGBT_PatternMatchingTestedBits_CIC_SLVScurrent_3_LpGBT_Clock_Polarity_1_Clock_Strength_1",
    "CICtoLpGBT_PatternMatchingErrorRate_CIC_SLVScurrent_3_LpGBT_Clock_Polarity_1_Clock_Strength_1",
    "CICtoLpGBT_PatternMatchingTestedBits_CIC_SLVScurrent_3_LpGBT_Clock_Polarity_1_Clock_Strength_4",
    "CICtoLpGBT_PatternMatchingErrorRate_CIC_SLVScurrent_3_LpGBT_Clock_Polarity_1_Clock_Strength_4",
    "CICtoLpGBT_PatternMatchingTestedBits_CIC_SLVScurrent_3_LpGBT_Clock_Polarity_1_Clock_Strength_7",
    "CICtoLpGBT_PatternMatchingErrorRate_CIC_SLVScurrent_3_LpGBT_Clock_Polarity_1_Clock_Strength_7",
    "CICtoLpGBT_PatternMatchingTestedBits_CIC_SLVScurrent_5_LpGBT_Clock_Polarity_1_Clock_Strength_1",
    "CICtoLpGBT_PatternMatchingErrorRate_CIC_SLVScurrent_5_LpGBT_Clock_Polarity_1_Clock_Strength_1",
    "CICtoLpGBT_PatternMatchingTestedBits_CIC_SLVScurrent_5_LpGBT_Clock_Polarity_1_Clock_Strength_4",
    "CICtoLpGBT_PatternMatchingErrorRate_CIC_SLVScurrent_5_LpGBT_Clock_Polarity_1_Clock_Strength_4",
    "CICtoLpGBT_PatternMatchingTestedBits_CIC_SLVScurrent_5_LpGBT_Clock_Polarity_1_Clock_Strength_7",
    "CICtoLpGBT_PatternMatchingErrorRate_CIC_SLVScurrent_5_LpGBT_Clock_Polarity_1_Clock_Strength_7",
    "LpGBTforCICbypass_PhaseScanBitErrorRate_phyPort0",
    "LpGBTforCICbypass_PhaseScanTestedBits_phyPort0",
    "LpGBTforCICbypass_BestPhase_phyPort0",
    "LpGBTforCICbypass_PhaseScanBitErrorRate_phyPort1",
    "LpGBTforCICbypass_PhaseScanTestedBits_phyPort1",
    "LpGBTforCICbypass_BestPhase_phyPort1",
    "LpGBTforCICbypass_PhaseScanBitErrorRate_phyPort2",
    "LpGBTforCICbypass_PhaseScanTestedBits_phyPort2",
    "LpGBTforCICbypass_BestPhase_phyPort2",
    "LpGBTforCICbypass_PhaseScanBitErrorRate_phyPort3",
    "LpGBTforCICbypass_PhaseScanTestedBits_phyPort3",
    "LpGBTforCICbypass_BestPhase_phyPort3",
    "LpGBTforCICbypass_PhaseScanBitErrorRate_phyPort4",
    "LpGBTforCICbypass_PhaseScanTestedBits_phyPort4",
    "LpGBTforCICbypass_BestPhase_phyPort4",
    "LpGBTforCICbypass_PhaseScanBitErrorRate_phyPort5",
    "LpGBTforCICbypass_PhaseScanTestedBits_phyPort5",
    "LpGBTforCICbypass_BestPhase_phyPort5",
    "LpGBTforCICbypass_PhaseScanBitErrorRate_phyPort6",
    "LpGBTforCICbypass_PhaseScanTestedBits_phyPort6",
    "LpGBTforCICbypass_BestPhase_phyPort6",
    "LpGBTforCICbypass_PhaseScanBitErrorRate_phyPort7",
    "LpGBTforCICbypass_PhaseScanTestedBits_phyPort7",
    "LpGBTforCICbypass_BestPhase_phyPort7",
    "LpGBTforCICbypass_PhaseScanBitErrorRate_phyPort8",
    "LpGBTforCICbypass_PhaseScanTestedBits_phyPort8",
    "LpGBTforCICbypass_BestPhase_phyPort8",
    "LpGBTforCICbypass_PhaseScanBitErrorRate_phyPort9",
    "LpGBTforCICbypass_PhaseScanTestedBits_phyPort9",
    "LpGBTforCICbypass_BestPhase_phyPort9",
    "LpGBTforCICbypass_PhaseScanBitErrorRate_phyPort10",
    "LpGBTforCICbypass_PhaseScanTestedBits_phyPort10",
    "LpGBTforCICbypass_BestPhase_phyPort10",
    "LpGBTforCICbypass_PhaseScanBitErrorRate_phyPort11",
    "LpGBTforCICbypass_PhaseScanTestedBits_phyPort11",
    "LpGBTforCICbypass_BestPhase_phyPort11",
    "MPAtoCIC_PhaseScanErrorRate_MPA_SLVScurrent_1",
    "MPAtoCIC_PhaseScanTestedBits_MPA_SLVScurrent_1",
    "MPAtoCIC_PhaseScanErrorRate_MPA_SLVScurrent_4",
    "MPAtoCIC_PhaseScanTestedBits_MPA_SLVScurrent_4",
    "MPAtoCIC_PhaseScanErrorRate_MPA_SLVScurrent_7",
    "MPAtoCIC_PhaseScanTestedBits_MPA_SLVScurrent_7",
]


opticalGroupPlots = [
    "LpGBTinputAlignmentSuccess", 
    "LpGBTinputBestPhase", 
    "LpGBTinputFoundPhasesDistribution",
    "PixelModuleHits", 
    "StripModuleHits",
    "VTRx_LightYieldScan", 
    "LpGBT_EyeOpeningScan_Power_0.333333", 
    "LpGBT_EyeOpeningScan_Power_0.666667", 
    "LpGBT_EyeOpeningScan_Power_1.000000", 
    "Board_BestStubPackageDelay", 
    "StripPixelModuleHits", 
    "CICtoLpGBT_PhaseAlignmentEfficiency", 
    "CICtoLpGBT_BestPhase", 
    "CICtoLpGBT_FoundPhaseDistribution", 
    "CommonNoiseHitsStrip_OccupancyDriven",
    "CommonNoiseHitsPixel_OccupancyDriven",
    "CommonNoiseStripPixelCorrelation_OccupancyDriven",
    "CommonNoiseHitsStrip_SigmaNoise_3.000",
    "CommonNoiseHitsPixel_SigmaNoise_3.000",
    "CommonNoiseStripPixelCorrelation_SigmaNoise_3.000",
    "BERTerrorRatePhaseScan",
    "BERTtestedBitCounterPhaseScan",
    "BERTerrorRate",
    "BERTtestedBitCounter",
    "BERTbestPhase",
    "FECerrorCounter",   
]



## Check for duplicates
for collection in [allVariables, hybridPlots, opticalGroupPlots]:
    all = set()
    for name in collection:
        if name in all:
            raise Exception("Duplicate %s found in all variables"%name)
        all.add(name)

logPlots = [
    "StripHybridHits", ## plots to be shown in log scale
    "CommonNoiseHits_OccupancyDriven",
    "CommonNoiseHits_SigmaNoise_3.000",
    "CommonNoiseHitsStrip_OccupancyDriven",
    "CommonNoiseHitsPixel_OccupancyDriven",
    "SSA(0)toMPA(8)_CommonNoiseCorrelation_OccupancyDriven",
    "SSA(1)toMPA(9)_CommonNoiseCorrelation_OccupancyDriven",
    "SSA(2)toMPA(10)_CommonNoiseCorrelation_OccupancyDriven",
    "SSA(3)toMPA(11)_CommonNoiseCorrelation_OccupancyDriven",
    "SSA(4)toMPA(12)_CommonNoiseCorrelation_OccupancyDriven",
    "SSA(5)toMPA(13)_CommonNoiseCorrelation_OccupancyDriven",
    "SSA(6)toMPA(14)_CommonNoiseCorrelation_OccupancyDriven",
    "SSA(7)toMPA(15)_CommonNoiseCorrelation_OccupancyDriven",
    "CommonNoiseStripPixelCorrelation_OccupancyDriven",
    "CommonNoiseHitsStrip_SigmaNoise_3.000",
    "CommonNoiseHitsPixel_SigmaNoise_3.000",
    "SSA(0)toMPA(8)_CommonNoiseCorrelation_SigmaNoise_3.000",
    "SSA(1)toMPA(9)_CommonNoiseCorrelation_SigmaNoise_3.000",
    "SSA(2)toMPA(10)_CommonNoiseCorrelation_SigmaNoise_3.000",  
    "SSA(3)toMPA(11)_CommonNoiseCorrelation_SigmaNoise_3.000",
    "SSA(4)toMPA(12)_CommonNoiseCorrelation_SigmaNoise_3.000",
    "SSA(5)toMPA(13)_CommonNoiseCorrelation_SigmaNoise_3.000",
    "SSA(6)toMPA(14)_CommonNoiseCorrelation_SigmaNoise_3.000",
    "SSA(7)toMPA(15)_CommonNoiseCorrelation_SigmaNoise_3.000",
    "CommonNoiseStripPixelCorrelation_SigmaNoise_3.000",
]

plotsToBeRenamed = { ##old name --> new name
    "/CommonNoiseHitsStrip_OccupancyDriven_": "/StripHybridHits_"
}

exstensiveVariables = ["NoiseDistribution", "PedestalDistribution"]


# allVariables = ["NoiseDistribution"]



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
    if verbose>2: print("makeMergedPlot")
    merged = None
    for plot in plots:
        if verbose>2: print(plot.GetName())
        if not merged: 
            chipN = "Chip(" + plot.GetName().split("Chip(")[1]
            chipN = chipN.split(")")[0] + ")"
            if verbose>2: print(chipN)
            newName = plot.GetName().replace(chipN, "Merged")+chip
            if verbose>2: print(newName)
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
    if verbose>2: print("makeMultiplePlot2D")
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
    if verbose>2: print(chipN)
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
    if verbose>10: print("Calling addHistoPlot(%d, %s, %s, %s)"%(len(plots), canvas, plot, fName))
    ## skip single chip plots if useOnlyMergedPlots is activated
    if (("SSA" in fName) or ("MPA" in fName) or ("Chip" in fName)) and (not ("Merged" in fName)) and (not ("Multiple" in fName)) and (useOnlyMergedPlots):
        isNum = "a"
        # if "/SSA_" in fName: isNum = fName.split("/SSA_")[1][0]
        # if "/MPA_" in fName: isNum = fName.split("/MPA_")[1][0]
        # if not isNum.isnumeric():
        if "SSA" in fName: isNum = fName.split("SSA")[1][0]
        if "MPA" in fName: isNum = fName.split("MPA")[1][0]
        if "Chip" in fName: isNum = fName.split("Chip")[1][0]
        if verbose>10:
            print("fName", fName, "isNum", isNum)
        if isNum.isnumeric():
            if verbose>20: print("Skipping %s"%fName)            
            return
    ## save histo plot, and add it to "plots"
    if plot:
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
        plotName = plot.GetName()
        isLog = False
        for logPlot in logPlots:
            if logPlot in plotName: isLog = True
        if verbose>10:
            print("Creating %s"%fName)
        if isLog: 
            print("Setting log scale")
            canvas.SetLogy()
        canvas.SaveAs(fName)
        if isLog: canvas.SetLogy(0)
    ## append fName, even if it does not exist to show the missing plot, except for the known missing plots
    if not("SSA" in fName and ("/2DPixelNoise_" in fName or "/2DChannelOffsetValues_" in fName or "/2DChannelOccupancyAfterOffsetEqualization_" in fName or "/2DChannelNoise_" in fName)) and not("MPA" in fName and ("/ChannelOffsetValues_" in fName)):
        if verbose>10: 
            if plot:
                print("Adding %s to plots (existing plot)"%fName)
            else:
                print("Adding %s to plots even if they are not produced, to show missing plots"%fName)
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

def makePlots(rootFile, xmlConfig, board_id, opticalGroup_id, tmpFolder, dateTimeRun, hv_channel, lv_channel, tempSensor):
    if verbose>2:
        print("Calling makePlots")
        print("board_id: ", board_id)
        print("opticalGroup_id: ", opticalGroup_id)
        print("tmpFolder: ", tmpFolder)
        print("dateTimeRun: ", dateTimeRun)
        print("hv_channel: ", hv_channel)
        print("lv_channel: ", lv_channel)
        print("tempSensor: ", tempSensor)
        print("xmlConfig: ", xmlConfig)
        print("rootFile: ", rootFile)
        print("rootFile.GetName(): ", rootFile.GetName())

        print("allVariables: ", allVariables)
        print("hybridPlots: ", hybridPlots)
        print("opticalGroupPlots: ", opticalGroupPlots)
        print("exstensiveVariables: ", exstensiveVariables)

    plots = []
    startTime_local = str(rootFile.Get("Detector/CalibrationStartTimestamp_Detector")).replace(" ","T")
    stopTime_local = str(rootFile.Get("Detector/CalibrationStopTimestamp_Detector")).replace(" ","T")
    if stopTime_local == "<cppyy.gbl.TObjectTobjectTatT0x(nil)>":
        stopTime_local = startTime_local
        print("WARNING: stopTime_local is empty, setting it to startTime_local")
    if verbose>10:
        print("startTime_local: ", startTime_local)
        print("stopTime_local: ", stopTime_local)
    if not "202" in startTime_local:
        raise Exception("startTime_local (Detector/CalibrationStartTimestamp_Detector) is not valid date: %s"%startTime_local)
    if not "202" in stopTime_local:
        raise Exception("stopTime_local (Detector/CalibrationStopTimestamp_Detector) is not valid date: %s"%stopTime_local)
    ## add Influxdb plot
    
    if not skipInfluxDb: 
        plots.append(  makePlotInfluxdb(startTime_local, stopTime_local, tempSensor, tmpFolder) )
        hv_current = "caen_%s_Current"%(hv_channel) ## eg. caen_HV001_Current
        hv_voltage = "caen_%s_Voltage"%(hv_channel) ## eg. caen_HV001_Voltage
        lv_current = "caen_%s_Current"%(lv_channel) ## eg. caen_BLV01_Current
        lv_voltage = "caen_%s_Voltage"%(lv_channel) ## eg. caen_BLV01_Voltage

#        "caen_BLV{:0>2}_Voltage".format(lv_channel),"caen_BLV{:0>2}_Current".format(lv_channel),"caen_HV{:0>3}_Voltage".format(hv_channel),"caen_HV{:0>3}_Current".format(hv_channel)]
        plots.append(  makePlotInfluxdbVoltageAndCurrent(startTime_local, stopTime_local, tmpFolder, sensors=[hv_current, hv_voltage, lv_current, lv_voltage]) )
        

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

    if verbose>1000: print("H")
    addHistoPlot(plots, c1, noiseGraph, fName = tmpFolder+"/CombinedNoisePlot.png")
    histograms = get_histograms(rootFile)
    histogramPaths = [hist_path for hist_path, hist_obj in histograms]
    if verbose>1000:
        print("List of histograms in the ROOT file:")
        for hist_path, hist_obj in histograms:
            if "Col" in hist_path: continue ## exclude single strip plots
            print(hist_path)
            hist_obj.Print()

    ## Check if the variables are in the root file#
    for collection in [allVariables, hybridPlots, opticalGroupPlots, exstensiveVariables]:
        if verbose>2: print("Checking %s"%collection)
        for name in collection[:]:
            if verbose>2: print("Checking %s"%name)
            found = False
            for hist_path, hist_obj in histograms:
                if "_%s_"%name in hist_path:
                    found = True
                    break
            if verbose>2: print("found", found)
            if histograms:
                print(hist_path)
            if not found:
                if verbose>2: print("#####################################################################################")
                print("WARNING: %s not found in the root file. It will be excluded from the webpage."%(name))
                if verbose>2: print("#####################################################################################")
                collection.remove(name)

    ## if the plot is not found, it is removed from the list
    for hist_path, hist_obj in histograms:
        if "NoiseDistribution" in hist_path:
            if verbose>2: print(hist_path.split("/")[-1])
            addHistoPlot(plots, c1, hist_obj, fName = tmpFolder+"/%s.png"%hist_path.split("/")[-1])
    missingPlots = []
    if verbose>2:
        print("allVariables: ", allVariables)
        print("hybridPlots: ", hybridPlots)
        print("opticalGroupPlots: ", opticalGroupPlots)
        print("exstensiveVariables: ", exstensiveVariables)
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
                    if verbose>2: print("chipId",str(chipId))
                    plot = None
                    count = 0
                    histoName = "Detector/Board_%s/OpticalGroup_%s/Hybrid_%s/%s_%s/D_B(%s)_O(%s)_H(%s)_%s_Chip(%s)"%(board_id, opticalGroup_id, hybridMod_id, chip, chipId, board_id, opticalGroup_id, hybridMod_id, name, chipId)
                    folderName = "/".join(histoName.split("/")[:-1])
                    folder = rootFile.Get(folderName)
                    if verbose>5: print("Folder",folder)
                    if folder == None:
                        print("############# WARNING: Folder %s not found in ROOT file %s. Skipping."%(folderName, rootFile.GetName())) 
                        continue
                    while(plot==None and count<3):
                        plot = rootFile.Get(histoName)
                        if histoName in histogramPaths:
                            plot = histograms[histogramPaths.index(histoName)][1]
                        else:
                            print("WARNING: %s not found in ROOT file %s. Skipping."%(histoName, rootFile.GetName()))
                            if verbose>100000: 
                                print("List of histograms in the ROOT file:")
                                for histo in histograms:
                                    if "_Col" in histo[0]: continue ## exclude single strip plots
                                    print("histo", histo)
                            missingPlots.append(histoName)
                            break
                        count+=1
                    print("T",str(plot))
                    ## selct 2DPixelNoise plots to make the combined 2D histogram
                    if plot: plotsToBeMerged[hybrid_id].append(plot)
                    counter += 1
                    if verbose>1000: print("A")
                    addHistoPlot(plots, c1, plot, fName = tmpFolder+"/%s_Hybrid%s_%s%s.png"%(name, hybrid_id, chip, chipId))
                ## re-normalize all non-extensive variable
                if verbose>1: 
                        print("Plots to be merged (hybrid %s)"%hybrid_id)
                        for plot in plotsToBeMerged[hybrid_id]:
                            print(plot.GetName())
                merged = makeMergedPlot(plotsToBeMerged[hybrid_id], chip)
                if merged and not name in exstensiveVariables:
                    merged.Scale(1./ counter)
                print(merged)
                if verbose>1000: print("B")
                addHistoPlot(plots, c1, merged, fName = tmpFolder+"/%s_Hybrid%s_%s%s.png"%(name, hybrid_id, chip, "Merged"+chip))
                
                ## add 1D projection 
                if merged and "2DPixelNoise" in name:
                    prx = merged.ProjectionX()
                    prx.SetTitle(merged.GetTitle() + " - X projection")
                    prx.Scale(1./merged.GetNbinsY())
                    if verbose>1000: print("C")
                    addHistoPlot(plots, c1, prx, fName = tmpFolder+"/%s_Hybrid%s_%s%s.png"%(name+"projX", hybrid_id, chip, "Merged"+chip))
                    pry = merged.ProjectionY()
                    pry.SetTitle(merged.GetTitle() + " - Y projection")
                    pry.Scale(1./merged.GetNbinsX())
                    if verbose>1000: print("D")
                    addHistoPlot(plots, c1, pry, fName = tmpFolder+"/%s_Hybrid%s_%s%s.png"%(name+"projY", hybrid_id, chip, "Merged"+chip))
            
#            if "2DPixelNoise" in name:
            if type(plot)==ROOT.TH2F and not "SCurve" in name: ## too many bins, very slow!
#            if type(plot)==ROOT.TH2F:
                multiple = makeMultiplePlot2D(plotsToBeMerged, chip)
                if verbose>1000: print("E")
                addHistoPlot(plots, c1, multiple, fName = tmpFolder+"/%s_%s%s.png"%(name, chip, "Multiple"+chip))
#            elif "NoiseDistribution" in name:
            elif type(plot)==ROOT.TH1F:
                if verbose>1000: print("F")
                addMultipleHistoPlot(plots, c1, plotsToBeMerged, fName = tmpFolder+"/%s_%s%s.png"%(name, chip, "Multiple"+chip))

                
            merged = None
    for name in hybridPlots:
        for hybrid_id in opticalGroup['hybrids']:
            hybrid = opticalGroup['hybrids'][str(hybrid_id)]
            hybridMod_id = opticalGroup_id*2 + int(hybrid_id)
            plot2 = rootFile.Get("Detector/Board_%s/OpticalGroup_%s/Hybrid_%s/D_B(%s)_O(%s)_%s_Hybrid(%s)"%(board_id, opticalGroup_id, hybridMod_id, board_id, opticalGroup_id, name, hybridMod_id))
            if verbose>1000: print("F")
            addHistoPlot(plots, c1, plot2, fName = tmpFolder+"/%s_Hybrid%s.png"%(name, hybrid_id))
    
    for name in opticalGroupPlots:
        path = "Detector/Board_%s/OpticalGroup_%s/D_B(%s)_%s_OpticalGroup(%s)"%(board_id, opticalGroup_id, board_id, name, opticalGroup_id)
        plot2 = rootFile.Get(path)
        if verbose>1000: print("Doing %s %s"%(name, path), plot2)
        if plot2 == None:
            print("WARNING: %s not found in ROOT file %s. Skipping."%(path, rootFile.GetName()))
            continue
        if verbose>1000: print("G")
        addHistoPlot(plots, c1, plot2, fName = tmpFolder+"/%s_OpticalGroup%s.png"%(name, hybrid_id))
    
    print()
    print("################################################")
    print("List of missing plots:")
    for missingPlot in missingPlots:
        print("WARNING: %s not found in ROOT file %s. Skipping."%(missingPlot, rootFile.GetName()))
    print("################################################")
    print()
    for plot in plots:
        for plotToBeRenamed in plotsToBeRenamed:
            if plotToBeRenamed in plot:
                plotRenamed = plot.replace(plotToBeRenamed, plotsToBeRenamed[plotToBeRenamed])
                if os.path.isfile(plotRenamed):
                    print("WARNING: %s already exists. Skipping."%plotRenamed)
                elif os.path.isfile(plot):
                    os.system("mv %s %s"%(plot, plotRenamed))
                    plots[plots.index(plot)] = plotRenamed
                    print("Renaming and moving %s to %s"%(plot, plotRenamed))
                else:
                    print("WARNING: %s not found. Skipping."%plot)
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
        histoNameSSA = "ChannelNoiseDistribution"
        histoNameMPA = "2DPixelNoise"
        if not histoNameSSA in list(noisePerChip.keys())[0] and not histoNameMPA in list(noisePerChip.keys())[0]:
            histoNameMPA = "2DChannelNoise"
            histoNameSSA = "ChannelNoise"
        print("Use %s %s in noise table ratio"%(histoNameSSA,histoNameMPA))

        for lineN in range(0,8):
            html_table += "<tr><th>SSA%d</th><th>%.3f</th><th>%.3f</th><th>MPA%d</th><th>%.3f</th><th>%.3f</th></tr>\n"%(lineN, noisePerChip.get("D_B(%s)_O(%s)_H(%s)_%s_Chip(%s)SSA"%(board_id, optical_id, 2*int(optical_id)+0, histoNameSSA, lineN),0), noisePerChip.get("D_B(%s)_O(%s)_H(%s)_%s_Chip(%s)SSA"%(board_id, optical_id, 2*int(optical_id)+1, histoNameSSA, lineN),0), lineN+8, noisePerChip.get("D_B(%s)_O(%s)_H(%s)_%s_Chip(%s)MPA"%(board_id, optical_id, 2*int(optical_id)+0, histoNameMPA, lineN+8),0), noisePerChip.get("D_B(%s)_O(%s)_H(%s)_%s_Chip(%s)MPA"%(board_id, optical_id, 2*int(optical_id)+1, histoNameMPA, lineN+8),0)) #<th>Board</th><th>Optical</th>
        
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

def makeWebpage(rootFile, testID, moduleName, runName, module, run, test, noisePerChip, noiseRatioPerChip, xmlConfig, board_id, opticalGroup_id, result, plots, xmlFileLink, tmpFolder, slotBI, tempSensor):
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
        if verbose>10: print(plot)
        if "_SSA" in plot or "_MPA" in plot: 
#            if "Merged" in plot or not useOnlyMergedPlots:
                plotsPerChip.append(plot)
        else: plotsInclusive.append(plot)
    if verbose>2: print(plotsInclusive)
    if verbose>2: print(plotsPerChip)
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

    ### Session
    from databaseTools import getSessionFromDB
    session = getSessionFromDB(run["runSession"])
    body += "<h1> %s %s  </h1>"%(grayText("Session: "), session['sessionName']) + "\n"
#    body += grayText("Session: ") + session['sessionName']
    body += grayText("Operator: ") + session['operator']
    body += ". " + grayText("Start [local time]: ") + session['timestamp'].replace("T", " ") + "<br>" +"\n"
    body += grayText("Description: ") + session['description'] + "<br>" +"\n"

    ### Run
    body += "<h1> %s %s  </h1>"%(grayText("Run: "), runName) + "\n"
    date, time =  run['runDate'].split("T")
 #   body += grayText("Run: ") + runName 
    body += grayText("Date: ") +date + ". " + grayText("Time [local time]: ") + time + "<br>" +"\n" 
    body += grayText("Type: ") + run["runType"] 
    body += ". " + grayText("Status: ") + run["runStatus"] + "<br>" +"\n"
#    body += grayText("Run boards: ") + str(run["runBoards"]) + "<br>" +"\n"
    startTime = str(rootFile.Get("Detector/CalibrationStartTimestamp_Detector"))
    startTime_rome, startTime_utc = getTimeFromRomeToUTC(startTime, timeFormat = "%Y-%m-%d %H:%M:%S")
    body += "<br>" +"\n"
    body += grayText("CalibrationStartTimestamp [local time]: ") + startTime
    body += ". " + grayText(f"Temperature ({tempSensor}):") + "%.2f &deg;C <br>\n"%getTemperatureAt(startTime_utc.isoformat("T").split("+")[0])
    stopTime = str(rootFile.Get("Detector/CalibrationStopTimestamp_Detector"))
    if stopTime == "<cppyy.gbl.TObject object at 0x(nil)>":
        stopTime = startTime
        print("WARNING: stopTime_local is empty, setting it to startTime_local")
    stopTime_rome, stopTime_utc = getTimeFromRomeToUTC(stopTime, timeFormat = "%Y-%m-%d %H:%M:%S")
    body += grayText("CalibrationStopTimestamp_Detector [local time]: ") + stopTime
    body += ". " + grayText(f"Temperature ({tempSensor}):") + "%.2f &deg;C <br>\n"%getTemperatureAt(stopTime_utc.isoformat("T").split("+")[0])
    gitHash = str(rootFile.Get("Detector/GitCommitHash_Detector"))
    from shellCommands import getGitTagFromHash
    gitTag = getGitTagFromHash(gitHash)
    linkGit = "https://gitlab.cern.ch/cms_tk_ph2/Ph2_ACF/-/tree/%s"%gitHash
    linkGitTag = "https://gitlab.cern.ch/cms_tk_ph2/Ph2_ACF/-/tags/%s"%gitTag
    body += grayText(f"Ph2ACF Tag: <a href= {linkGitTag}> {gitTag}  </a>") + "<br>" +"\n"
    body += grayText(f"GitCommitHash: <a href= {linkGit}> {gitHash}  </a>") + "<br>" +"\n"
    body += grayText("HostName: ") + str(rootFile.Get("Detector/HostName_Detector")) + "<br>" +"\n"
    body += grayText("Username: ") + str(rootFile.Get("Detector/Username_Detector")) + "<br>" +"\n"
#    body += grayText("InitialDetectorConfiguration: ") + str(rootFile.Get("Detector/InitialDetectorConfiguration_Detector")) + "<br>" +"\n"
#    body += grayText("FinalDetectorConfiguration: ") + str(rootFile.Get("Detector/FinalDetectorConfiguration_Detector")) + "<br>" +"\n"
    body += grayText("CalibrationName: ") + str(rootFile.Get("Detector/CalibrationName_Detector")) + "<br>" +"\n"
    body += grayText("NameId_Board: ") + str(rootFile.Get("Detector/Board_0/D_NameId_Board_(0)")) + "<br>" +"\n"
    directLinkToZip = run['runFile'].replace("files/link/public", "remote.php/dav/public-files")
    testId,zipFile = directLinkToZip.split("/")[-2:]
    directLinkToROOTFile = "https://cmstkita.web.cern.ch/Pisa/TBPS/root.html?file=https://cmstkita.web.cern.ch/Pisa/TBPS/navigator_eos.php/%s/%s/Results.root"%(testId,zipFile)
    directLinkToMonitorDQMFile = "https://cmstkita.web.cern.ch/Pisa/TBPS/root.html?file=https://cmstkita.web.cern.ch/Pisa/TBPS/navigator_eos.php/%s/%s/MonitorDQM.root"%(testId,zipFile)
    directLinkToXmlFile = "https://cmstkita.web.cern.ch/Pisa/TBPS/navigator_eos.php/%s/%s/ModuleTest_settings.xml"%(testId,zipFile)
    directLinkToLogFile = "https://cmstkita.web.cern.ch/Pisa/TBPS/log.html?logfile=https://cmstkita.web.cern.ch/Pisa/TBPS/navigator_eos.php/%s/%s/%s.log"%(testId,zipFile,testId)
    directLinkToConnectionMapFile = "https://cmstkita.web.cern.ch/Pisa/TBPS/navigator_eos.php/%s/%s/connectionMap_%s.json"%(testId,zipFile,moduleName)
    folderLink =  '/'.join(run['runFile'].split("/")[:-1])
    body += "<br>" + "\n"
    body += grayText("Browse: ") + '<a href="%s">ROOT file</a>, <a href="%s">MonitorDQM file</a>, <a href="%s">log file</a>, <a href="%s"> Xml file</a>, <a href="%s"> Connection map</a> <br>'%(directLinkToROOTFile, directLinkToMonitorDQMFile, directLinkToLogFile, directLinkToXmlFile, directLinkToConnectionMapFile) + "\n"
    body += grayText("Link to: ") + '<a href="%s">Zip file</a>, <a href="%s">CERN box folder</a> <br>'%(directLinkToZip, folderLink) + "\n"
    utc, myTime_grafana = getTimeFromRomeToUTC(run["runDate"], timeFormat = "%Y-%m-%dT%H:%M:%S")
    start_time_grafana = (myTime_grafana - timedelta(hours=2))
    stop_time_grafana = (myTime_grafana + timedelta(hours=2))
    GrafanaLink = "http://pccmslab1.pi.infn.it:3000/d/ff666241-736f-4d30-b490-dc8655d469a9/burn-in?orgId=1&%%20from={__from}\&to=%d&from=%d"%((int(stop_time_grafana.timestamp())*1000), (int(start_time_grafana.timestamp())*1000))
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
    body += grayText("Burn-in slot: ") + str(slotBI) + "<br>" +"\n"
    body += "<br>" + "\n"
#    body += grayText("NameId: ") + str(rootFile.Get("Detector/Board_%s/OpticalGroup_%s/D_B(%s)_NameId_OpticalGroup(%s)"%(board_id, optical_id, board_id, optical_id))) + "<br>" +"\n"
    body += grayText("LpGBTFuseId: ") + str(rootFile.Get("Detector/Board_%s/OpticalGroup_%s/D_B(%s)_LpGBTFuseId_OpticalGroup(%s)"%(board_id, optical_id, board_id, optical_id))) + "<br>" +"\n"
    body += grayText("VTRxFuseId: ") + str(rootFile.Get("Detector/Board_%s/OpticalGroup_%s/D_B(%s)_VTRxFuseId_OpticalGroup(%s)"%(board_id, optical_id, board_id, optical_id))) + "<br>" +"\n"
    body += grayText("Date:") + date + grayText("Time [local time]:") + time + "<br>" +"\n"
    
    body += "<h1> %s  </h1>"%("SSA and MPA noise table") + "\n"
    body += makeNoiseTable(noisePerChip, board_id, optical_id)

    body += "<h1> %s  </h1>"%("SSA and MPA noise edge ratio table") + "\n"
    body += makeNoiseTable(noiseRatioPerChip, board_id, optical_id, ratio = True)
    
    html = html.replace("[ADD BODY]", body)

    print("noiseRatioPerChip:", noiseRatioPerChip)
    
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

# def  uploadToWebDav(folder, files):
#     if verbose>2: print(folder, files)
#     newfiles = {}
#     for file in files:
#         fileName = file.split("/")[-1]
#         target = "%s/%s"%(folder, fileName)
#         print("Uploading %s %s"%(file, target))
#         if webdav_website: 
#             newfile = webdav_website.write_file(file, target)
#             newfiles[file] = newfile
#         else:
#             newfiles[file] = file
#     return newfiles

def getTimeFromUTCToRome(time_str, timeFormat="%Y-%m-%dT%H:%M:%S"):
    from datetime import datetime
    import pytz
    utc_tz = pytz.utc
    rome_tz = pytz.timezone('Europe/Rome')
    # Parse the naive datetime string
    naive_dt = datetime.strptime(time_str, timeFormat)
    # Localize to UTC
    utc_dt = utc_tz.localize(naive_dt)
    # Convert to Rome time
    rome_dt = utc_dt.astimezone(rome_tz)
    return rome_dt, utc_dt 

def getTimeFromRomeToUTC(time_str, timeFormat="%Y-%m-%dT%H:%M:%S"):
    from datetime import datetime
    import pytz
    utc_tz = pytz.utc
    rome_tz = pytz.timezone('Europe/Rome')
    # Parse the naive datetime string
    naive_dt = datetime.strptime(time_str, timeFormat)
    # Localize to Rome time
    rome_dt = rome_tz.localize(naive_dt)
    # Convert to UTC
    utc_dt = rome_dt.astimezone(utc_tz)
    return rome_dt, utc_dt


def getInfluxQueryAPI(token_location = "~/private/influx.sct"):
    import os
    token = open(os.path.expanduser(token_location)).read().strip()
    from influxdb_client import InfluxDBClient
    client = InfluxDBClient(url="http://cmslabserver:8086/", token=token)
    return client.query_api()

def getTemperatureAt(timestamp, sensorName="Temp0", org="pisaoutertracker"):
    # Define a small window around the timestamp (±30 seconds)
    if verbose>2: print('Calling getTemperatureAt(timestamp=%s, sensorName=%s, org=%s)'%(timestamp, sensorName, org))
    window = timedelta(seconds=30)
    timestamp = datetime.fromisoformat(timestamp)
    start_window = (timestamp - window).isoformat("T") + "Z"
    end_window = (timestamp + window).isoformat("T") + "Z"
    query = f'''
    from(bucket: "sensor_data")
        |> range(start: {start_window}, stop: {end_window})
        |> filter(fn: (r) => r["_measurement"] == "mqtt_consumer")
        |> filter(fn: (r) => r["_field"] == "{sensorName}")
        |> aggregateWindow(every: 1s, fn: mean, createEmpty: false)
        |> yield(name: "mean")
    '''
    tables = getInfluxQueryAPI().query(query, org=org)
    # Gather the temperature values found within the time window.
    temps = [record.get_value() for table in tables for record in table.records]
    if temps:
        # Average values if more than one record is returned.
        return sum(temps) / len(temps)
    else:
        print('WARNING: Something wrong calling getTemperatureAt(timestamp=%s, sensorName=%s, org=%s)'%(timestamp, sensorName, org))
        return -999

def makePlotInfluxdbVoltageAndCurrent(startTime_rome, stopTime_rome, folder, 
    sensors=["caen_ASLOT0_Voltage", "caen_XSLOT0_Voltage", "caen_ASLOT0_Current", "caen_XSLOT0_Current"], org="pisaoutertracker"):
    print("makePlotInfluxdb")
    
    import os
    token_location = "~/private/influx.sct" 
    token = open(os.path.expanduser(token_location)).read().strip()
    
    import matplotlib.pyplot as plt
    from datetime import timedelta
    
    if verbose>2: print('Calling makePlotInfluxdbVoltageAndCurrent(startTime_rome=%s, stopTime_rome=%s, folder=%s, sensors=%s, org=%s)'%(startTime_rome, stopTime_rome, folder, sensors, org))
#    startTime_utc, startTime_rome = getTimeFromUTCToRome(startTime_utc, timeFormat = "%Y-%m-%dT%H:%M:%S")
    startTime_rome, startTime_utc = getTimeFromRomeToUTC(startTime_rome, timeFormat = "%Y-%m-%dT%H:%M:%S")
    stopTime_rome, stopTime_utc = getTimeFromRomeToUTC(stopTime_rome, timeFormat = "%Y-%m-%dT%H:%M:%S")
    
    start_time = (startTime_utc - timedelta(hours=1)).isoformat("T").split("+")[0] + "Z"
    stop_time = (stopTime_utc + timedelta(hours=1)).isoformat("T").split("+")[0] + "Z"

    # Create the base axis for Voltage HV (left side).
    fig, axHV_voltage = plt.subplots(figsize=(10, 5))

    # Create twin axes. By default, these will be on the right.
    axLV_voltage = axHV_voltage.twinx()   # Voltage LV (right, blue)
    axHV_current  = axHV_voltage.twinx()   # Current HV (right, orange)
    axLV_current  = axHV_voltage.twinx()   # Current LV (to be moved to left, red)

    # Adjust spine positions.
    axLV_voltage.spines["right"].set_position(("outward", 0))      # Voltage LV on right at 0 points.
    axHV_current.spines["right"].set_position(("outward", 35))       # Current HV on right at 30 points.

    # Move axLV_current to the left.
    axLV_current.yaxis.set_label_position("left")
    axLV_current.yaxis.tick_left()
    axLV_current.spines["left"].set_position(("outward", 45))
    axLV_current.spines["right"].set_visible(False)  # Hide the unused right spine.

    # Optional: Hide background patches for the additional axes.
    axHV_current.set_frame_on(True)
    axLV_current.set_frame_on(True)
    axHV_current.patch.set_visible(False)
    axLV_current.patch.set_visible(False)

    # Set the spine and tick colors to match the plot colors.
    axHV_voltage.spines['left'].set_color('green')
    axHV_voltage.tick_params(axis='y', colors='green')

    axLV_voltage.spines['right'].set_color('blue')
    axLV_voltage.tick_params(axis='y', colors='blue')

    axHV_current.spines['right'].set_color('orange')
    axHV_current.tick_params(axis='y', colors='orange')

    axLV_current.spines['left'].set_color('red')
    axLV_current.tick_params(axis='y', colors='red')

    # Set y-axis limits.
    HV_voltage_min, HV_voltage_max = 0, 500
    LV_voltage_min, LV_voltage_max = 0, 25
    HV_current_min, HV_current_max     = 0, 6
    LV_current_min, LV_current_max     = 0, 1.5

    if verbose>30: print(stop_time)
    # Loop over sensors and query data.
    if verbose>3: print(sensors)
    for sensorName in sensors:
        query = f'''
        from(bucket: "sensor_data")
        |> range(start: {start_time}, stop: {stop_time})
        |> filter(fn: (r) => r["_measurement"] == "mqtt_consumer")
        |> filter(fn: (r) => r["_field"] == "{sensorName}" )
        |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
        |> yield(name: "mean")
        '''
        
        times = []
        values = []

        if verbose>3: print(query)
        tables = getInfluxQueryAPI().query(query, org=org)
        
        for table in tables:
            if verbose>3: print(table)
            for record in table.records:
                times.append(record.get_time())
                values.append(record.get_value())

        sensorNameNoCaen = sensorName.replace("caen_", "")
        # Choose the correct axis and color based on the sensor name.
        if "Voltage" in sensorName:
            if "HV" in sensorName:
                axHV_voltage.plot(times, values, label=sensorNameNoCaen, color='green')
            elif "LV" in sensorName:
                axLV_voltage.plot(times, values, label=sensorNameNoCaen, color='blue')
            else:
                print(f"Unknown voltage sensor: {sensorName}")      
        elif "Current" in sensorName:
            if "HV" in sensorName:
                axHV_current.plot(times, values, label=sensorNameNoCaen, color='orange')
            elif "LV" in sensorName:
                axLV_current.plot(times, values, label=sensorNameNoCaen, color='red')
            else:
                print(f"Unknown current sensor: {sensorName}")
        else:
            print(f"Unknown sensor type: {sensorName}")

    # Set individual axis labels with matching colors and reduced labelpad.
    axHV_voltage.set_ylabel("Voltage HV (V)", color='green', labelpad=2)
    axLV_voltage.set_ylabel("Voltage LV (V)", color='blue', labelpad=2)
    axHV_current.set_ylabel("Current HV (mA)", color='orange', labelpad=2)
    axLV_current.set_ylabel("Current LV (mA)", color='red', labelpad=2)

    # Set the y-axis limits.
#    axHV_voltage.set_ylim(HV_voltage_min, HV_voltage_max)
#    axLV_voltage.set_ylim(LV_voltage_min, LV_voltage_max)
#    axHV_current.set_ylim(HV_current_min, HV_current_max)
#    axLV_current.set_ylim(LV_current_min, LV_current_max)

    # Combine legend entries from all axes.
    lines = []
    labels = []
    # Draw a vertical reference line on the left-most axis.
    plt.axvline(x=startTime_utc, color='r', linestyle='--', label=startTime_utc.strftime('%H:%M:%S'))
    plt.axvline(x=stopTime_utc, color='b', linestyle='--', label=stopTime_utc.strftime('%H:%M:%S'))
    for ax in [axHV_voltage, axLV_voltage, axHV_current, axLV_current]:
        l, lab = ax.get_legend_handles_labels()
        lines.extend(l)
        labels.extend(lab)
    axHV_voltage.legend(lines, labels, loc='upper left')

    # Set the x-axis label using the main axis.
    timezone_h = "%+.1f" % (-startTime_rome.utcoffset().seconds/3600)
    axHV_voltage.set_xlabel('UTC Time (CET + %s h)'% timezone_h)

    axHV_voltage.grid(True)
    plt.title('Sensor Data Over Time')

    fName = os.path.join(folder, "sensor_data_plot_test.png")
    plt.savefig(fName)
    print("InfluxDb: saved ", fName)

    return fName



def makePlotInfluxdb(startTime_rome, stopTime_rome, tempSensor, folder, org="pisaoutertracker"):
    print("makePlotInfluxdb")

    token_location = "~/private/influx.sct" 
    token = open(os.path.expanduser(token_location)).read()[:-1]
    
    from datetime import datetime, timedelta
    
    if verbose>2: print('Calling makePlotInfluxdb(startTime_rome=%s, stopTime_rome=%s, tempSensor=%s, folder=%s, org=%s)'%(startTime_rome, stopTime_rome, tempSensor, folder, org))
#    startTime_utc, startTime_rome = getTimeFromUTCToRome(startTime_utc, timeFormat = "%Y-%m-%dT%H:%M:%S")
    startTime_rome, startTime_utc = getTimeFromRomeToUTC(startTime_rome, timeFormat = "%Y-%m-%dT%H:%M:%S")
    stopTime_rome, stopTime_utc = getTimeFromRomeToUTC(stopTime_rome, timeFormat = "%Y-%m-%dT%H:%M:%S")
    
    start_time = (startTime_utc - timedelta(hours=1)).isoformat("T").split("+")[0] + "Z"
    stop_time = (stopTime_utc + timedelta(hours=1)).isoformat("T").split("+")[0] + "Z"
    

    sensorName = tempSensor
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
    
    tables = getInfluxQueryAPI().query(query, org=org)
    
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
    plt.axvline(x=startTime_utc, color='r', linestyle='--', label=startTime_utc.strftime('%H:%M:%S'))
    plt.axvline(x=stopTime_utc, color='b', linestyle='--', label=stopTime_utc.strftime('%H:%M:%S'))
    ## Set the x and y axis labels
    timezone_h = "%+.1f"%(-startTime_rome.utcoffset().seconds/3600)
    plt.xlabel('UTC Time (CET + %s h'% timezone_h)
    plt.ylabel('Temperature')
    plt.title('Sensor Data Over Time')
    plt.legend()
    plt.grid(True)
    fName = folder+"/sensor_data_plot.png"
    
    ## Orario UTC
    plt.savefig(fName)
    print("InfluxDb: saved ", fName)
       
    return fName

'''
def getConnectionMap(run, xmlConfig, folder):
    testId,zipFile  = run['runFile'].split("/")[-2:]
    print(run)
    moduleName = run['moduleTestName'][0].split("__")[0]
    directLinkToConnectionMapFile = "https://cmstkita.web.cern.ch/Pisa/TBPS/navigator_eos.php/%s/%s/connectionMap_%s.json"%(testId,zipFile,moduleName)
    ## download the file
    import requests
    response = requests.get(directLinkToConnectionMapFile)
    response.raise_for_status()  # Raise an error if the request failed
    # Parse the JSON content into a Python dictionary
    print(directLinkToConnectionMapFile)
    print(response)
    connectionMap = response.json()

    print(connectionMap)
    return connectionMap
'''


def updateTestResult(module_test, tempSensor="auto"):#, skipWebdav = False):
    if verbose>2:
        print("Calling updateTestResult")
        print("module_test:", module_test)
        print("tempSensor:", tempSensor)
        # print("skipWebdav:", skipWebdav)

    global plots
    tmpFolder = "/tmp/"

    #allVariables = []
    gROOT.SetBatch()
    gStyle.SetOptStat(0)
    tmpFolder = tmpFolder+module_test+"__%s/"%version
    base = "/test3/"

    import shutil
    try:
        shutil.rmtree(tmpFolder[:-1]+"_bak")
        shutil.move(tmpFolder, tmpFolder[:-1]+"_bak")
    except:
        pass
    import pathlib
    pathlib.Path(tmpFolder).mkdir(parents=True, exist_ok=True)
    print("Temporary folder:", tmpFolder)

    hwToModuleID, hwToMongoID = makeModuleNameMapFromDB()

    # ### Initialize webdav, if necessary
    # hash_value_location = "~/private/webdav.sct" #echo "xxxxxxxxxxxxxxx|xxxxxxxxxxxxxxx\nxxxxxxxxxxxxxxx|xxxxxxxxxxxxxxx" > ~/private/webdav.sct
    # webdav_website = None
    # webdav_wrapper = None
    # if not skipWebdav:
    #     hash_value_read, hash_value_write = open(os.path.expanduser(hash_value_location)).read()[:-1].split("\n")[1].split("|")
    #     from moduleTest import webdav_wrapper
    #     webdav_website = WebDAVWrapper(webdav_url, hash_value_read, hash_value_write)
    
    
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
    # if webdav_wrapper: 
    #     print("Downloading %s to %s"%(run['runFile'].split("//")[-1], "/tmp/%s"%fName))
    #     zip_file_path = webdav_wrapper.download_file(remote_path=run['runFile'].split("//")[-1] , local_path="/tmp/%s"%fName) ## drop
    # else: zip_file_path = "/tmp/%s"%fName
    zip_file_path=cernbox_folder_run+"/"+run['runFile'].split("//")[-1]
    print(f"Reading zip file {zip_file_path} from {cernbox_computer}.")
    os.system(f"scp {cernbox_computer}:{zip_file_path} /tmp/{fName}")
    zip_file_path = "/tmp/%s"%fName
    print(f"Copied to local {zip_file_path}")


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
    print("Opened ROOT file:", rootFile)
#    xmlConfig = readXmlConfig(xmlPyConfigFile=xmlPyConfigFile, folder=extracted_dir)
    xmlConfig = run["runConfiguration"] ## take configuration from db instead of python file

    ## Get Connection map , see https://cmstkita.web.cern.ch/Pisa/TBPS/navigator_eos.php/Run_206/output_dggbl.zip/connectionMap_PS_26_IBA-10006.json
    connectionMapFileName = extracted_dir+"/connectionMap_%s.json"%moduleName
    if os.path.exists(connectionMapFileName):
        with open(connectionMapFileName) as json_file:
            txt = str(json_file.read())
            if verbose>10: print("ConnectionMap: ", txt)
            connectionMap = eval(txt)
    else:
        print("WARNING: connectionMap not found in ",connectionMapFileName)
        connectionMap = {}

    ### Get slotBI from connection map
    from databaseTools import getSlotBIFromModuleConnectionMap
    slotBI = getSlotBIFromModuleConnectionMap(connectionMap)
    if tempSensor == "auto":
        tempSensor = "OW0%s"%(slotBI)
        print("Auto tempSensor:", tempSensor)

    ### Add plot with voltage and currents
    hv_channel = -1
    lv_channel = -1
    ## check if the last connection of each cable is either ASLOT or LV
    for con in connectionMap.values():
        lastConn = con['connections'][-1]
        ### see https://github.com/pisaoutertracker/integration_tools/blob/625aaca54ddd45893fe118b1f0e6d7ce7f69facc/ui/main.py#L1600-L1603
        if "ASLOT" in lastConn['cable']:
            hv_channel = "HV"+lastConn['cable'][5:]+f".{lastConn['line']}"
        elif "XSLOT" in lastConn['cable']:
            lv_channel = "LV"+lastConn['cable'][5:]+f".{lastConn['line']}"
    if hv_channel == -1 or lv_channel == -1:
        print("HV/LV found: ", hv_channel, lv_channel)
        #raise Exception("No HV or LV found in connectionMap")
    if verbose>0:
        print("HV/LV found: ", hv_channel, lv_channel)
    #            connectionMap = json.load(json_file)
    print("Connection map:", connectionMap, "Connection map filename:",connectionMapFileName)
    print("Run:", run)
    ## download the file
    if verbose>5: print(xmlConfig)
    global noisePerChip
    noisePerChip = getNoisePerChip(rootFile , xmlConfig )
    noiseRatioPerChip = getNoisePerChip(rootFile , xmlConfig, ratio = True)
    if verbose>10:
        print("noisePerChip:", noisePerChip)
        print("noiseRatioPerChip:", noiseRatioPerChip)
    moduleHwIDs = getIDsFromROOT(rootFile, xmlConfig)
    
#    for board_optical in moduleHwIDs:
#    board_id, opticalGroup_id = board_optical
    result = getResultPerModule(noisePerChip, xmlConfig, str(board_id), str(opticalGroup_id))
    plots = makePlots(rootFile, xmlConfig, board_id, opticalGroup_id, tmpFolder, run['runDate'], hv_channel, lv_channel, tempSensor)
    fff = plots+[xmlPyConfigFile]
    folder = "Module_%s_Run_%s_Result_%s"%(moduleName, runName, version)
    # nfolder = base+folder
    nfolder = base+folder
    if verbose>1: print(f"mkDir {tmpFolder}/{folder}")
#     if webdav_website: 
#         response = webdav_website.mkDir(nfolder)
#         if verbose>2: print("mkDir response:", response, response.status_code, response.reason)
# ##        print(webdav_website.list_files(nfolder))
    command=f"mkDir {tmpFolder}/{folder}" 
    os.system(command)
    print(command)
    fff = [f for f in fff if os.path.exists(f)]
#        newNames = uploadToWebDav(nfolder, fff)
    webpage = makeWebpage(rootFile, module_test, moduleName, runName, module, run, test, noisePerChip, noiseRatioPerChip, xmlConfig, board_id, opticalGroup_id, result, plots, xmlPyConfigFile, tmpFolder, slotBI, tempSensor)
    zipFile = "results"  
    import shutil
    tmpUpFolder = tmpFolder.replace("//","/").replace("//","/")
    tmpUpFolder = '/'.join(tmpUpFolder.split("/")[:-1])
    name = tmpUpFolder.split("/")[-1]
    tmpUpFolder = '/'.join(tmpUpFolder.split("/")[:-1])+"/"
    if verbose>30: print(tmpUpFolder, name, tmpFolder, zipFile, nfolder)
    if verbose>20: print("shutil.make_archive(zipFile, 'zip', resultFolder)", tmpUpFolder+name, tmpFolder)
    shutil.make_archive(tmpUpFolder+name, 'zip', tmpFolder)
    if verbose>20: print("Done")
    # if webdav_website: 
    #     newFile = webdav_website.write_file(tmpUpFolder+name+".zip", "%s/results.zip"%(nfolder))
    #     if verbose>0: print("Uploaded %s"%newFile)
    cmd = f"mkdir -p {tmpFolder}/{folder} && cp {tmpUpFolder}{name}.zip {tmpFolder}/{folder}/results.zip"
    print(cmd)
    os.system(cmd)
    cmd = f"scp -r {tmpFolder}/{folder} {cernbox_computer}:{cernbox_folder_analysis}/{nfolder}"
    print(cmd)
    os.system(cmd)
    
    if verbose>0: print("Plots:") 
    for p in plots:
        if verbose>0: print(p)
    print("Extracted folder:", extracted_dir)
    print("Webpage:", webpage)
    if verbose>0: print("file:///run/user/1000/gvfs/sftp:host=pccmslab1.tn,user=thermal%s"%webpage)
    # if webdav_website:
    #     print("CERN box link (folder): https://cernbox.cern.ch/files/link/public/%s/%s"%(hash_value_read,nfolder))
    #     if verbose>1: print("TBPS Pisa page: https://cmstkita.web.cern.ch/Pisa/TBPS/")
    #     download = "https://cmstkita.web.cern.ch/Pisa/TBPS/Uploads/%s"%(newFile)
    #     if verbose>1: print("Download link:", download)
    #     navigator = "https://cmstkita.web.cern.ch/Pisa/TBPS/navigator.php/Uploads/%s/"%(newFile)
    #     print("##################################################################################################################")
    #     print("### Link to the new webpage:", navigator)
    #     print("##################################################################################################################")
    # else:
    #     download = "dummy"
    #     navigator = "dummy"

    print("CERN box link (folder): https://cernbox.cern.ch/files/link/public/%s/%s"%(hash_value_read,nfolder))
    print(f"Local folder: {cernbox_folder_analysis}/{nfolder}")
    if verbose>1: print("TBPS Pisa page: https://cmstkita.web.cern.ch/Pisa/TBPS/")
    download = "https://cmstkita.web.cern.ch/Pisa/TBPS/Uploads/%s"%(newFile)
    if verbose>1: print("Download link:", download)
    navigator = "https://cmstkita.web.cern.ch/Pisa/TBPS/navigator.php/Uploads/%s/"%(newFile)
    print("##################################################################################################################")
    print("### Link to the new webpage:", navigator)
    print("##################################################################################################################")

    from databaseTools import createAnalysis
    startTime_rome, startTime_utc = getTimeFromRomeToUTC(str(rootFile.Get("Detector/CalibrationStartTimestamp_Detector")), timeFormat = "%Y-%m-%d %H:%M:%S")
    try:
        stopTime_rome, stopTime_utc = getTimeFromRomeToUTC(str(rootFile.Get("Detector/CalibrationStopTimestamp_Detector")), timeFormat = "%Y-%m-%d %H:%M:%S")
    except:
        print("WARNING: CalibrationStopTimestamp_Detector not found, using start time instead.")
        stopTime_rome, stopTime_utc = startTime_rome, startTime_utc
    json = {
        "moduleTestAnalysisName": folder, #"PS_26_05-IBA_00004__run79__Test", 
        "moduleTestName": module_test, #"PS_26_05-IBA_00004__run79", 
        "moduleTempStart": getTemperatureAt(startTime_utc.isoformat("T").split("+")[0], tempSensor),
        "moduleTempStop": getTemperatureAt(stopTime_utc.isoformat("T").split("+")[0], tempSensor),
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
    os.system("cp -r %s /tmp/latest_ana"%tmpFolder)

def printAllSensors(org="pisaoutertracker"):
    query = f'''
    from(bucket: "sensor_data")
    |> range(start: -1h)
    |> filter(fn: (r) => r["_measurement"] == "mqtt_consumer")
    |> group(columns: ["_field"])
    |> distinct(column: "_field")
    |> yield(name: "distinct")
    '''
    tables = getInfluxQueryAPI().query(query, org=org)
    for table in tables:
        for record in table.records:
            print(record.get_value())


if __name__ == '__main__':
    import argparse
    print()
    print("Example: python3  updateTestResult.py PS_26_IPG-10010__run500939 ")
    print()
    #makePlotInfluxdb("2025-02-24T12:32:38", "2025-02-24T14:32:38", "/tmp/influxdb/")
    print(getTemperatureAt("2025-02-24T12:32:38", sensorName="Temp0"))
    #makePlotInfluxdbVoltageAndCurrent("2025-02-24T12:32:38","2025-02-24T13:32:38", "/tmp/influxdb/")
    #printAllSensors
    parser = argparse.ArgumentParser(description='Script used to elaborate the results of the Phase-2 PS module test. More info at https://github.com/pisaoutertracker/BurnIn_moduleTest. \n Example: python3  updateTestResult.py PS_26_05-IBA_00102__run418 . ')
    parser.add_argument('module_test', type=str, help='Single-module test name')
    # parser.add_argument('--skipWebdav', type=bool, nargs='?', const=True, default=False, help='Skip upload to webdav (for testing).')
#    parser.add_argument('--tempSensor', type=str, const=True, default="-1", help='Skip upload to webdav (for testing).')
    args = parser.parse_args()
    updateTestResult(module_test = args.module_test , tempSensor="auto") #, skipWebdav = args.skipWebdav)
