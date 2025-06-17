
# resultsFile = POTATOFiles/PS_26_IPG-10014_2025-05-29_15h59m46s_+22C_PSquickTest_v1-01.root created from 
# rootTrackerFileName = /tmp/Run_500749_output_btdhg/Results.root
# monitorDQMFile = /tmp/Run_500749_output_btdhg/MonitorDQM.root
#
# iv_csv_path = POTATOFiles/HV0.6_PS_26_IPG-10014_after_encapsulation_2025-05-29 15:52:01_IVScan.csv
# runNumber = run500749
# moduleBurninName = Module4L
# moduleCarrierName = 01
# connectionMapFilePath = POTATOFiles/connectionMap_PS_26_IPG-10014_run500749.json
# module_name = PS_26_IPG-10014
# test_module_test = PS_26_IPG-10014__run500749
#

cd /home/thermal/potato/Express/
source ../setupPotato.sh
export POTATODIR=/home/thermal/potato/Express/
mkdir -p backup
mv data/LocalFiles/DropBox/* backup

cp /home/thermal/BurnIn_moduleTest/POTATOFiles/PS_26_IPG-10014_2025-05-29_15h59m46s_+22C_PSquickTest_v1-01.root data/LocalFiles/DropBox

## Compile POTATO express, if necessary
#./compile.py

## Run POTATO express
./PotatoExpress
            