#!/bin/bash

### It requires a ModuleTest_settings.xml with the FC7OT IP, which can be produced with:
# python3 moduleTest.py --module PS_26_05-IBA_00102 --slot 0 --board fc7ot2 --readOnlyID  --session session1

# Define variables

FIRMWARE="ps8m5gcic2l12octal8dio5tluv301.bin" ## downloaded from https://udtc-ot-firmware.web.cern.ch/?dir=v3-01/ps_8m_5g_cic2_l12octa_l8dio5_tlu
#FIRMWARE="ps8m10gcic2l12octal8dio5tluv301.bin" ## downloaded from https://udtc-ot-firmware.web.cern.ch/?dir=v3-01/ps_8m_10g_cic2_l12octa_l8dio5_tlu
IMAGE="gitlab-registry.cern.ch/cms-pisa/pisatracker/pisa_module_test:ph2_acf_v6-02"
WORKDIR="/home/cmsTkUser/Ph2_ACF"
TESTDIR="/home/thermal/BurnIn_moduleTest"
VOLUME_MOUNTS="-v $PWD/Results:$WORKDIR/Results/:z \
               -v $PWD/logs:$WORKDIR/logs/:z \
               -v $PWD:$PWD:z \
               -v /etc/hosts:/etc/hosts \
               -v /home/thermal/private/webdav.sct:/root/private/webdav.sct:z"
NETWORK="--net host"

# Function to run a containerized command
run_Ph2ACF() {
    local CMD=$1
    echo podman run --rm -ti $VOLUME_MOUNTS $NETWORK --entrypoint bash $IMAGE \
        -c "cd $WORKDIR && source setup.sh && cd $TESTDIR && $CMD"
    podman run --rm -ti $VOLUME_MOUNTS $NETWORK --entrypoint bash $IMAGE \
        -c "cd $WORKDIR && source setup.sh && cd $TESTDIR && $CMD"
}

# Run the tests
echo run_Ph2ACF "fpgaconfig -l -c ModuleTest_settings.xml" ## show current firmware installed
run_Ph2ACF "fpgaconfig -l -c ModuleTest_settings.xml" ## show current firmware installed
CLEAN_FIRMWARE="${FIRMWARE%%.bin}"
CLEAN_FIRMWARE=$(echo "$CLEAN_FIRMWARE" | tr -d '_.')
echo $CLEAN_FIRMWARE
run_Ph2ACF "fpgaconfig  -c ModuleTest_settings.xml  -f  $FIRMWARE  -i $CLEAN_FIRMWARE" ## install firmware
echo run_Ph2ACF "fpgaconfig  -c ModuleTest_settings.xml  -f  $FIRMWARE  -i $CLEAN_FIRMWARE" ## install firmware
run_Ph2ACF "fpgaconfig -l -c ModuleTest_settings.xml" ## show current firmware installed

echo "All tests completed."
