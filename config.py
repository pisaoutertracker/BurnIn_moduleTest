import os
import logging

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)


# ============================================================================
# CONFIGURATION CONSTANTS
# ============================================================================

class Config:
    """Central configuration for module testing"""
    
    # CERNbox settings
    CERNBOX_FOLDER_RUN = "/home/thermal/cernbox_runshared/"
    CERNBOX_COMPUTER = "cmslabburnin"
    
    # Default values
    VERBOSE = 0  # -1: errors only, 0: info, 1: debug, 3+: detailed debug
    LAST_PH2ACF_VERSION = "ph2_acf_v6-18"
    XML_PY_CONFIG_FILE = "PS_Module_settings.py"
    IP = "192.168.0.45"
    PORT = 5000
    XML_OUTPUT = "ModuleTest_settings.xml"
    DEFAULT_COMMAND = "PSquickTest"
    XML_TEMPLATE = "PS_Module_v2p1.xml"
    
    # Firmware versions
    FIRMWARE_5G = "ps8m5gcic2l12octal8dio5v303A"
    FIRMWARE_10G = "ps6m10gcic2l12octal8dio5v303A"
    RUN_FPGA_CONFIG = False
    
    # Docker/Podman configuration
    THERMAL_HOME = os.environ['HOME']
    PODMAN_COMMAND = (
        'podman run --rm -ti '
        '-v $PWD/Results:/home/cmsTkUser/Ph2_ACF/Results/:z '
        '-v $PWD/logs:/home/cmsTkUser/Ph2_ACF/logs/:z '
        f'-v {THERMAL_HOME}/RunNumbers.dat:{THERMAL_HOME}/RunNumbers.dat:z '
        '-v $PWD:$PWD:z '
        '-v /etc/hosts:/etc/hosts '
        '-v $HOME/RunNumbers.dat:/root/RunNumbers.dat:z '
        '--net host '
        '--entrypoint bash '
        'gitlab-registry.cern.ch/cms-pisa/pisatracker/pisa_module_test:%s -c "%s"'
    )
    PREFIX_COMMAND = (
        '\\cp /usr/share/zoneinfo/Europe/Rome /etc/localtime && '
        'cd /home/cmsTkUser/Ph2_ACF && source setup.sh && '
        f'cd {os.getcwd()}'
    )
    SETTING_FOLDER_DOCKER = "/home/cmsTkUser/Ph2_ACF/settings"
    CONNECTION_MAP_FILENAME = "connectionMap_%s.json"
    
    # Commands that skip analysis
    COMMANDS_TO_SKIP_ANALYSIS = ["readOnlyID", "vtrxoff"]
    
    # lpGBT hardware IDs (for testing)
    LPGBT_IDS = []
    
    # WebDAV configuration
    HASH_VALUE_LOCATION = "~/private/webdav.sct"
    WEBDAV_URL = "https://cernbox.cern.ch/remote.php/dav/public-files"


def set_verbose_level(verbose: int) -> None:
    """
    Set logging level based on verbose parameter
    
    Args:
        verbose: Verbosity level (-1: errors, 0: info, 1+: debug, 10+: detailed debug)
    """
    if verbose == -1:
        level = logging.ERROR
    elif verbose == 0:
        level = logging.INFO
    else:
        level = logging.DEBUG

    # Set both module logger and root logger to ensure handlers emit desired levels
    logger.setLevel(level)
    logging.getLogger().setLevel(level)
    
    Config.VERBOSE = verbose
