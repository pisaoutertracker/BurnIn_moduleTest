#!/bin/env python3
"""
Module Test Script for Phase-2 PS Module Testing using Ph2_ACF

This script orchestrates the testing of Phase-2 PS modules, including:
- Configuration generation (XML files)
- Firmware management
- Test execution via Ph2_ACF
- Result processing and database upload
- Integration with CERNbox for result storage

More info: https://github.com/pisaoutertracker/BurnIn_moduleTest
"""

import os
import shutil
import logging
from typing import List, Dict, Tuple, Optional, Any
from pprint import pformat
from config import Config, set_verbose_level

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)


# ============================================================================
# ARGUMENT PARSING
# ============================================================================

def parse_arguments():
    """Parse command line arguments"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description=(
            'Script used to launch the test of the Phase-2 PS module, '
            'using Ph2_ACF. More info at '
            'https://github.com/pisaoutertracker/BurnIn_moduleTest'
        ),
        epilog=(
            'Example: python3 moduleTest.py --module PS_26_05-IBA_00102 '
            '--slot 0 --board fc7ot2 -c readOnlyID --session session1'
        )
    )
    
    required = parser.add_argument_group('required arguments')
    
    # Required arguments
    required.add_argument(
        '--module', type=str, required=True,
        help='Optical group number (eg. PS_26_05-IBA_00102). '
             '"auto" will select the expected module according to the connection database.'
    )
    
    # Session arguments
    required.add_argument(
        '--session', type=str, default='-1',
        help='Name of the existing session (eg. session1).'
    )
    required.add_argument(
        '-m', '--message', type=str, default='-1',
        help='Message used to create a new session. '
             'Requires "|" to separate author and message.'
    )
    
    # Module configuration
    required.add_argument(
        '--slot', type=str, default='-1',
        help='Module name (eg. 0,1,2).'
    )
    required.add_argument(
        '--slotBI', type=str, default='-1',
        help='Module name for burn-in (eg. 0,1,2).'
    )
    required.add_argument(
        '--board', type=str, default='-1',
        help='Board name (eg. fc7ot2).'
    )
    
    # Chip configuration
    parser.add_argument(
        '--strip', type=str, default='0,1,2,3,4,5,6,7',
        help='Strip number (eg. 0,1,2 default=all).'
    )
    parser.add_argument(
        '--pixel', type=str, default='8,9,10,11,12,13,14,15',
        help='Pixel number (eg. 8,9,15 default=all).'
    )
    parser.add_argument(
        '--hybrid', type=str, default='0,1',
        help='Hybrid number (default=0,1).'
    )
    parser.add_argument(
        '--lpGBT', type=str, default='auto',
        help='lpGBT file (default=lpGBT_v2_PS.txt).'
    )
    
    # Test configuration
    parser.add_argument(
        '-c', '--command', type=str, default=Config.DEFAULT_COMMAND,
        nargs='?', const='',
        help=f'Command to pass to runCalibration -c. Default: {Config.DEFAULT_COMMAND}'
    )
    parser.add_argument(
        '--edgeSelect', type=str, default='default',
        help='Select edgeSelect parameter (Default from PS_Module_template.xml).'
    )
    parser.add_argument(
        '--tempSensor', type=str, default="auto", nargs='?', const=True,
        help='Select which temperature sensor will be displayed in analysis page.'
    )
    
    # Logging configuration
    parser.add_argument(
        '--verbose', type=int, default=0,
        help='Verbosity level: -1=errors only, 0=info (default), 1=debug, 3+=detailed debug'
    )
    
    # Version and firmware
    parser.add_argument(
        '--version', type=str, default=Config.LAST_PH2ACF_VERSION,
        nargs='?', const=True,
        help=f'Ph2ACF version in Docker. Use "local" for locally installed. '
             f'Default: {Config.LAST_PH2ACF_VERSION}'
    )
    parser.add_argument(
        '--firmware', type=str, nargs='?', const='',
        help=f'Firmware used in fpgaconfig. Default={Config.FIRMWARE_5G}'
    )
    parser.add_argument(
        '--g10', type=bool, nargs='?', const=True,
        help=f'Force install 10g firmware ({Config.FIRMWARE_10G}).'
    )
    parser.add_argument(
        '--g5', type=bool, nargs='?', const=True,
        help=f'Force install 5g firmware ({Config.FIRMWARE_5G}).'
    )
    
    # FPGA configuration
    parser.add_argument(
        '--runFpgaConfig', type=bool, nargs='?', const=True,
        help='Force run runFpgaConfig.'
    )
    parser.add_argument(
        '--vetoFpgaConfig', type=bool, nargs='?', const=True,
        help='Veto on runFpgaConfig (useful for runCalibrationPisa).'
    )
    
    # File handling
    parser.add_argument(
        '--useExistingModuleTest', type=str, nargs='?', const='',
        help='Read results from existing module test. Skip ot_module_test run.'
    )
    parser.add_argument(
        '-f', '--useExistingXmlFile', type=str, nargs='?', const='',
        help='Specify existing xml file without generating new one.'
    )
    parser.add_argument(
        '--xmlPyConfigFile', type=str, nargs='?',
        const="PS_Module_settings.py", default="PS_Module_settings.py",
        help='Location of PS_Module_settings.py file with XML configuration.'
    )
    
    # Database and upload options
    parser.add_argument(
        '--skipUploadResults', type=bool, nargs='?', const=True, default=False,
        help='Skip running updateTestResults at end of test.'
    )
    parser.add_argument(
        '--skipMongo', type=bool, nargs='?', const=True,
        help='Skip upload to MongoDB (for testing).'
    )
    parser.add_argument(
        '--addNewModule', type=bool, default=False, nargs='?', const=True,
        help='Add new module to database without asking y/n.'
    )
    parser.add_argument(
        '--skipModuleCheck', type=bool, default=False, nargs='?', const=True,
        help='Do not throw exception if declared module does not correspond '
             'to module in slot.'
    )
    parser.add_argument(
        '--ignoreConnection', type=bool, default=False, nargs='?', const=True,
        help='Ignore database connection check.'
    )
    
    return parser.parse_args()


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_arguments(args):
    """
    Validate command line arguments
    
    Args:
        args: Parsed command line arguments
        
    Raises:
        Exception: If arguments are invalid or inconsistent
    """
    # Check required arguments
    if not args.useExistingModuleTest and not args.useExistingXmlFile and args.slotBI == "-1":
        if args.slot == "-1":
            raise Exception("Please provide a slot number. Eg. --slot 0")
        if args.board == "-1":
            raise Exception("Please provide a board name. Eg. --board fc7ot2")
    
    if not args.useExistingModuleTest and args.module == "-1":
        raise Exception("Please provide a module name. Eg. --module PS_26_05-IBA_00102 or auto")
    
    if args.session == "-1" and args.message == "-1" and args.command != "readOnlyID":
        raise Exception(
            "Please provide either a session name (eg. --session session1) "
            "or a message (eg. -m 'Mickey Mouse|Test of the burnin controller')"
        )
    
    if args.message != "-1" and "|" not in args.message:
        raise Exception(
            f"The message passed with -m must contain '|', eg. -m 'Silvio|Test', "
            f"while you used -m '{args.message}'."
        )
    
    # Check firmware options
    if args.firmware and args.g10:
        raise Exception("You cannot use --firmware and --g10 option at the same time.")


def validate_slot_module_mapping(optical_groups: List[int], 
                                 slots_bi: List[str], 
                                 modules: List[str],
                                 args) -> None:
    """
    Validate that slots and modules have consistent mapping
    
    Args:
        optical_groups: List of optical group IDs
        slots_bi: List of burn-in slot IDs
        modules: List of module names
        args: Parsed command line arguments
        
    Raises:
        Exception: If mapping is inconsistent
    """
    if args.slot != "-1":
        if len(optical_groups) != len(modules):
            raise Exception(
                f"--slots and --modules must have the same number of objects. "
                f"Check {optical_groups} and {modules}."
            )
    
    if args.slotBI != "-1":
        if args.slot != "-1":
            raise Exception("You cannot use both --slot and --slotBI at the same time.")
        if args.board != "-1":
            raise Exception("You cannot use both --board and --slotBI at the same time.")
        if len(slots_bi) != len(modules):
            raise Exception(
                f"--slotsBI and --modules must have the same number of objects. "
                f"Check {slots_bi} and {modules}."
            )
        if len(slots_bi) != len(set(slots_bi)):
            raise Exception(f"You cannot have the same slot in --slotsBI. Check {slots_bi}.")


def validate_chip_numbers(hybrids: List[int], pixels: List[int], strips: List[int]) -> None:
    """
    Validate chip numbers are in valid ranges
    
    Args:
        hybrids: List of hybrid numbers
        pixels: List of pixel chip numbers
        strips: List of strip chip numbers
        
    Raises:
        Exception: If chip numbers are out of range
    """
    if len(strips) > 0 and (max(strips) > 7 or min(strips) < 0):
        raise Exception(f"Strip numbers must be in [0,7] range. Strips: {strips}")
    
    if len(pixels) > 0 and (max(pixels) > 15 or min(pixels) < 0):
        raise Exception(f"Pixel numbers must be in [8,15] range. Pixels: {pixels}")


# ============================================================================
# FIRMWARE MANAGEMENT
# ============================================================================

def determine_firmware(args) -> str:
    """
    Determine which firmware to use based on arguments
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Firmware version string
    """
    if args.firmware:
        return args.firmware
    elif args.g10:
        return Config.FIRMWARE_10G
    else:
        if args.runFpgaConfig:
            args.g5 = True
        return Config.FIRMWARE_5G


def check_and_install_firmware(board: str, 
                               modules: List[str],
                               firmware_to_use: str,
                               args) -> None:
    """
    Check firmware requirements and install if needed
    
    Args:
        board: Board name (e.g., 'fc7ot2')
        modules: List of module names
        firmware_to_use: Firmware version to use
        args: Parsed command line arguments
    """
    from databaseTools import (
        getModuleBandwidthFromDB, 
        getFirmwareVersionInFC7OT
    )
    from shellCommands import fpgaconfigPisa
    
    # Check module bandwidth requirements
    module_bandwidth = None
    firmware_required = None
    
    for module in modules:
        bandwidth = getModuleBandwidthFromDB(module)
        
        if module_bandwidth is not None and bandwidth != module_bandwidth:
            raise Exception(
                f"Testing modules with different bandwidth ({module_bandwidth} and {bandwidth}). "
                "This is not allowed (different firmware required in FC7)."
            )
        
        module_bandwidth = bandwidth
        
        if bandwidth == "10Gbps":
            firmware_required = Config.FIRMWARE_10G
        elif bandwidth == "5Gbps":
            firmware_required = Config.FIRMWARE_5G
        else:
            raise Exception(
                f"Module {module} has unknown bandwidth {bandwidth} in database. "
                "Please fix the database."
            )
        
        # Validate firmware compatibility
        if bandwidth == "5Gbps" and args.g10:
            raise Exception(
                f"Module {module} is declared as 5Gbps, but you are trying to run "
                "test with 10Gbps firmware."
            )
        elif bandwidth == "10Gbps" and args.g5:
            raise Exception(
                f"Module {module} is declared as 10Gbps, but you are trying to run "
                "test with 5Gbps firmware."
            )
        
        if Config.VERBOSE > 1:
            logger.debug(f"Expected module {module}. According to Pisa db is {bandwidth}. "
                        f"Requires firmware {firmware_required}.")
    
    # Check installed firmware
    firmware_installed, firmware_timestamp = getFirmwareVersionInFC7OT(board)
    
    if Config.VERBOSE > -1:
        from datetime import datetime
        timestamp_str = str(datetime.fromtimestamp(float(firmware_timestamp)))
        logger.info(f"Firmware installed in board {board}: {firmware_installed} ({timestamp_str})")
    
    # Install firmware if needed
    if firmware_required:
        logger.info("-" * 80)
        if firmware_required == firmware_installed:
            logger.info(
                f"Firmware {firmware_required} is already installed in board {board}. "
                "No need to install again."
            )
        else:
            logger.info(
                f"Firmware {firmware_required} is not installed in board {board} "
                f"(it has {firmware_installed}). Installing using fpgaconfigPisa."
            )
            fpgaconfigPisa(board, firmware_required)
        logger.info("-" * 80)
    else:
        raise Exception("Cannot define which firmware to use.")
    
    # Check for quad firmware (deprecated)
    if "quad" in firmware_to_use.lower():
        raise Exception(
            f"WARNING: You are trying to use a module firmware 'quad' ({firmware_to_use}). "
            "This means that the optical group numbering is completely messed up. "
            "Once you fix the optical group numbering, remove this exception manually!"
        )


# ============================================================================
# MODULE VERIFICATION
# ============================================================================

def verify_module_connections(board: str,
                              optical_groups: List[int],
                              modules: List[str],
                              args) -> List[str]:
    """
    Verify that expected modules match database connections
    
    Args:
        board: Board name
        optical_groups: List of optical group IDs
        modules: List of module names (can contain 'auto')
        args: Parsed command line arguments
        
    Returns:
        List of verified module names
        
    Raises:
        Exception: If module connections don't match expectations
    """
    from databaseTools import getModuleConnectedToFC7, getFiberLink
    
    verified_modules = []
    
    for i, slot in enumerate(optical_groups):
        module_from_db = getModuleConnectedToFC7(board.upper(), f"OG{slot}")
        module_from_cli = modules[i]
        
        # Handle 'auto' module selection
        if module_from_cli == "auto":
            modules[i] = module_from_db
            logger.info(
                f"    You selected 'auto' for module in board {board} and slot {slot}. "
                f"Using module {module_from_db} from connection database."
            )
            module_from_cli = module_from_db
        
        logger.info(
            f"board {board}, slot {slot}, "
            f"moduleFromDB {module_from_db}, moduleFromCLI {module_from_cli}"
        )
        
        # Validate connection
        error = None
        if module_from_db is None:
            fc7, og = getFiberLink(module_from_cli)
            if fc7 is None:
                logger.info(f"No module declared in database for board {board.upper()} and slot OG{slot}.")
                if args.addNewModule:
                    logger.info("OK, as you are adding new modules to the database.")
                else:
                    error = (
                        f"No module declared in database for board {board.upper()} "
                        f"and slot OG{slot}. If you are not adding a new module, "
                        "something is wrong. Use --addNewModule option to add new module."
                    )
                    logger.error(error)
            else:
                error = (
                    f"Module {module_from_cli} is already in connection database "
                    f"and expected in board {fc7} and slot {og}, "
                    f"not in board {board.upper()} and slot OG{slot}. "
                    "You can avoid this error using --ignoreConnection option."
                )
                logger.error(error)
        elif module_from_db != module_from_cli:
            error = (
                f"Module {module_from_db} declared in database for board {board} "
                f"and slot {slot} does not match module declared in command line "
                f"({module_from_cli})."
            )
            logger.error(error)
        else:
            logger.info(
                f"Module {module_from_db} in database matches command line ({module_from_cli})."
            )
        
        # Handle errors
        if error:
            if args.ignoreConnection:
                logger.warning(f"WARNING: --ignoreConnection active. Ignoring: {error}")
            else:
                raise Exception(f"{error} You can skip this error using --ignoreConnection flag.")
        
        verified_modules.append(module_from_cli)
    
    return verified_modules


from typing import Union

def resolve_lpgbt_files(lpgbt_file: str, modules: List[str]) -> Union[List[str], str]:
    """
    Resolve lpGBT file names for modules
    
    Args:
        lpgbt_file: lpGBT file specification ('auto' or specific file)
        modules: List of module names
        
    Returns:
        List of lpGBT file names
    """
    if lpgbt_file != "auto":
        # Preserve original behavior: return the provided value as-is
        # (some downstream functions accept a single string or a list)
        return lpgbt_file
    
    from databaseTools import getLpGBTversionFromDB
    
    lpgbt_files = []
    for module in modules:
        version = getLpGBTversionFromDB(module).lower()
        filename = f"lpGBT_{version}_PS.txt"
        lpgbt_files.append(filename)
        logger.info(
            f"You selected 'auto' as lpGBT file. Module {module} will use "
            f"lpGBT file {filename} according to database."
        )
    
    logger.info(f"Final lpGBT files: {lpgbt_files}")
    return lpgbt_files


# ============================================================================
# XML CONFIGURATION
# ============================================================================

def create_xml_configuration(board: str,
                            optical_groups: List[int],
                            hybrids: List[int],
                            strips: List[int],
                            pixels: List[int],
                            lpgbt_file,
                            edge_select: str,
                            args,
                            xml_py_config_filename: Optional[str] = None) -> Tuple[Dict, str, str]:
    """
    Create XML configuration for module test
    
    Args:
        board: Board name
        optical_groups: List of optical group IDs
        hybrids: List of hybrid numbers
        strips: List of strip chip numbers
        pixels: List of pixel chip numbers
        lpgbt_file: lpGBT file name(s)
        edge_select: Edge select parameter
        args: Parsed command line arguments
        
    Returns:
        Tuple of (xml_config dict, xml_file path, xml_py_config_file path)
    """
    from makeXml import makeXml, readXmlConfig, makeXmlPyConfig
    from shellCommands import copyXml
    
    # Handle existing module test
    if args.useExistingModuleTest:
        matches = [
            folder for folder in os.listdir("Results")
            if args.useExistingModuleTest in folder
        ]
        if len(matches) != 1:
            raise Exception(
                f"{len(matches)} matches of {args.useExistingModuleTest} "
                f"in ./Results/. {matches}"
            )
        
        folder = matches[0]
        xml_py_config_path = f"Results/{folder}"
        xml_py_config_file = xml_py_config_filename or Config.XML_PY_CONFIG_FILE
        
        config_file_path = f"{xml_py_config_path}/{xml_py_config_file}"
        if os.path.exists(config_file_path):
            xml_config = readXmlConfig(xml_py_config_file, folder=xml_py_config_path)
            logger.info(f"Using existing xmlPyConfigFile: {xml_py_config_path}")
        else:
            from makeXml import makeConfigFromROOTfile
            logger.info(f"{config_file_path} not found. Creating from ROOT file.")
            xml_config = makeConfigFromROOTfile(f"Results/{folder}/Results.root")
        
        xml_file = f"Results/{folder}/{Config.XML_OUTPUT}"
        if os.path.exists(xml_file):
            logger.info(f"Using existing xml file: {xml_file}")
        else:
            xml_file = makeXml(Config.XML_OUTPUT, xml_config, Config.XML_TEMPLATE)
        
        return xml_config, xml_file, xml_py_config_file
    
    # Create new configuration
    out_file = "PS_Module_settings_autogenerated.py"
    xml_py_config_file = out_file
    
    if not args.useExistingXmlFile:
        # Preserve original behavior: pass version string as-is (including 'local')
        copyXml(args.version)
    
    xml_config = makeXmlPyConfig(
        board, optical_groups, hybrids, strips, pixels,
        lpgbt_file, edge_select, out_file, Nevents=1000
    )
    
    if args.useExistingXmlFile:
        xml_file = args.useExistingXmlFile
    else:
        xml_file = makeXml(Config.XML_OUTPUT, xml_config, Config.XML_TEMPLATE)
    
    return xml_config, xml_file, xml_py_config_file


# ============================================================================
# TEST EXECUTION
# ============================================================================

def run_module_test(xml_file: str,
                   firmware: str,
                   board: str,
                   args) -> Tuple[str, str]:
    """
    Execute the module test
    
    Args:
        xml_file: Path to XML configuration file
        firmware: Firmware version
        board: Board name
        args: Parsed command line arguments
        
    Returns:
        Tuple of (test_id, date)
    """
    from shellCommands import runModuleTest, fpgaconfigPisa
    
    # Run fpgaconfig if requested
    if args.runFpgaConfig or args.g10 or args.g5:
        fpgaconfigPisa(board, firmware)
    
    # Run module test
    # Preserve original behavior: pass version string as-is (including 'local')
    ph2acf_version = args.version
    out = runModuleTest(
        xml_file,
        args.useExistingModuleTest,
        ph2acf_version,
        args.command
    )
    
    # Handle fpgaconfig requirement
    if out == "Run fpgaconfigNew":
        if args.vetoFpgaConfig:
            raise Exception(
                "You forgot to run fpgaconfig. Please run it before running module test. "
                "Eg. remove --vetoFpgaConfig flag or use --runFpgaConfig flag."
            )
        else:
            logger.warning("\n\nWARNING: You forgot to run fpgaconfig. Launching it now.\n")
            fpgaconfigPisa(board, firmware)
            out = runModuleTest(
                xml_file,
                args.useExistingModuleTest,
                ph2acf_version,
                args.command
            )
            if out == "Run fpgaconfig":
                raise Exception("fpgaconfig failed. Please check the error above.")
    
    test_id, date, error_code = out
    return test_id, date, error_code


def process_test_results(root_file, xml_config: Dict) -> Tuple[Dict, Dict]:
    """
    Process test results from ROOT file
    
    Args:
        root_file: ROOT file object
        xml_config: XML configuration dictionary
        
    Returns:
        Tuple of (IDs dict, noise_per_chip dict)
    """
    from tools import getIDsFromROOT, getNoisePerChip
    
    # Get hardware IDs for each module
    ids = getIDsFromROOT(root_file, xml_config)
    
    # Get noise measurements per chip
    noise_per_chip = getNoisePerChip(root_file, xml_config)
    
    return ids, noise_per_chip


# ============================================================================
# MODULE DATABASE OPERATIONS
# ============================================================================

def verify_and_update_modules(ids: Dict,
                              modules: List[str],
                              optical_groups: List[int],
                              xml_config: Dict,
                              args) -> Tuple[Dict, Dict]:
    """
    Verify modules against database and update if necessary
    
    Args:
        ids: Dictionary mapping (board, optical_group) to hardware IDs
        modules: List of expected module names
        optical_groups: List of optical group IDs
        xml_config: XML configuration dictionary
        args: Parsed command line arguments
        
    Returns:
        Tuple of (hw_to_module_name dict, hw_to_mongo_id dict)
    """
    from databaseTools import makeModuleNameMapFromDB, updateNewModule
    
    # Create mapping from hardware ID to module name
    hw_to_module_name, hw_to_mongo_id = makeModuleNameMapFromDB()
    
    board = 0
    error = False
    all_modules = hw_to_module_name.values()
    
    for i, optical_group in enumerate(optical_groups):
        module_expected = modules[i]
        hw_id = ids.get((board, optical_group), -2)
        
        # Handle missing modules
        if int(hw_id) in [-1, -2]:
            try:
                ip = xml_config["boards"][str(board)]["ip"]
            except:
                ip = xml_config["boards"][board]["ip"]
            
            message = (
                f"+++ Board {ip} Optical {optical_group} Module {hw_id} "
                f"(NO MODULE FOUND). Expected {module_expected}. +++"
            )
            logger.warning(message)
            
            if not args.skipModuleCheck:
                raise Exception(
                    f"{message}. You can skip this error using --skipModuleCheck flag."
                )
            continue
        
        # Get module from database
        module_found = hw_to_module_name.get(hw_id, "unknown module")
        
        # Handle auto module selection
        if module_expected is None or module_expected == "auto":
            logger.info(
                f"Taking module name from module ID. Using {module_found} "
                f"instead of {module_expected}."
            )
            modules[i] = module_found
            module_expected = module_found
        
        try:
            ip = xml_config["boards"][board]["ip"]
        except:
            ip = xml_config["boards"][str(board)]["ip"]
        
        logger.info(
            f"+++ Board {ip} Optical {optical_group} Module {module_found} ({hw_id}). "
            f"Expected {module_expected}. +++"
        )
        
        # Verify module match
        if module_expected in all_modules:
            if module_found != module_expected:
                logger.error("DIFFERENT MODULE FOUND!!")
                error = True
        else:
            # Add new module to database
            logger.info("List of known modules:")
            for hwid in hw_to_module_name:
                logger.info(f"{hw_to_module_name[hwid]} ({int(hwid)})")
            
            logger.info(f"Module {module_expected} is not yet in database.")
            logger.info(f"HwId {int(hw_id)} found.")
            
            if hw_id in hw_to_module_name and int(hw_id) != -1:
                message = (
                    f"HwId {hw_id} is already associated to module "
                    f"{hw_to_module_name[hw_id]}.\nPlease fix the module name used."
                )
                logger.error(message)
                if not args.skipModuleCheck:
                    raise Exception(message)
            
            if int(hw_id) != -1 and not args.skipModuleCheck:
                if args.addNewModule:
                    answer = "y"
                else:
                    answer = input(
                        f"Do you want to add module with hwID {hw_id} "
                        f"as {module_expected} in database? (y/n): "
                    )
                
                if answer.lower() in ["y", "yes"]:
                    updateNewModule(module_expected, hw_id)
                    # Update mapping
                    hw_to_module_name, hw_to_mongo_id = makeModuleNameMapFromDB()
                    all_modules = hw_to_module_name.values()
                else:
                    raise Exception("Cannot work with unknown modules.")
    
    # Check for errors
    if error:
        message = (
            f"The modules declared in --modules ({modules}) do not correspond "
            f"to the module found in --opticalGroups ({optical_groups}) "
            f"of --board. See above for details."
        )
        logger.error(message)
        if not args.skipModuleCheck:
            raise Exception(message)
    
    return hw_to_module_name, hw_to_mongo_id


# ============================================================================
# RESULT UPLOAD
# ============================================================================

def prepare_result_files(test_id: str,
                        root_file_name,
                        xml_py_config_file: str,
                        xml_file: str,
                        modules: List[str],
                        args) -> str:
    """
    Prepare result files for upload
    
    Args:
        test_id: Test ID string
        root_file_name: Name of the ROOT file
        xml_py_config_file: Path to XML Python config file
        xml_file: Path to XML file
        modules: List of module names
        args: Parsed command line arguments
        
    Returns:
        Path to uploaded zip file
    """
    from tools import getMonitorDQMFileName
    from databaseTools import getConnectionMap, saveMapToFile
    
    # Get result folder
    result_folder = root_file_name[:root_file_name.rfind("/")]
    log_file = f"logs/{test_id}.log"
    
    # Get MonitorDQM file
    try:
        monitor_dqm_file = getMonitorDQMFileName(log_file)
        monitor_dqm_new = monitor_dqm_file.split("MonitorDQM_")[0] + "MonitorDQM.root"
        os.system(f"cp {monitor_dqm_file} {monitor_dqm_new}")
        logger.info(f"{monitor_dqm_file} found and copied to {monitor_dqm_new}")
        monitor_dqm_file = monitor_dqm_new
    except:
        logger.warning(f"WARNING: MonitorDQMFile not found in log file {log_file}")
        monitor_dqm_file = None
    
    # Copy files to result folder
    files_to_copy = [xml_py_config_file, xml_file, log_file, monitor_dqm_file]
    for file in files_to_copy:
        if not file or file == root_file_name:
            continue
        
        # Handle existing module test
        if args.useExistingModuleTest:
            if file in [xml_py_config_file, xml_file, log_file]:
                continue
            if file == log_file:
                folder = result_folder.split("Results/")[1]
                logs = [f for f in os.listdir(f"Results/{folder}") if ".log" in f]
                dest = log_file.replace("logs/", result_folder + "/")
                if logs and not os.path.exists(dest):
                    os.symlink(logs[-1], dest)
        
        if file:
            shutil.copy(file, result_folder)
            logger.debug(f"Copied {file} to {result_folder}")
    
    # Create connection map files
    for module in modules:
        conn_map_file = f"{result_folder}/{Config.CONNECTION_MAP_FILENAME % module}"
        
        if not args.useExistingModuleTest:
            connection_map = getConnectionMap(module)
            saveMapToFile(connection_map, conn_map_file)
        else:
            if os.path.exists(conn_map_file):
                logger.debug(f"Connection map {conn_map_file} found.")
            else:
                logger.warning(f"WARNING: No connection map in {result_folder}. Making new one.")
                connection_map = getConnectionMap(module)
                saveMapToFile(connection_map, conn_map_file)
    
    # Create and upload zip file
    os.makedirs(f"/tmp/{test_id}", exist_ok=True)
    zip_file = "output"
    shutil.make_archive(zip_file, 'zip', result_folder)
    os.system(f"cp {zip_file}.zip /tmp/{test_id}/output.zip")
    logger.debug(f"Copied {zip_file}.zip to /tmp/{test_id}/output.zip")
    
    # Upload to CERNbox
    cmd = (
        f"scp -r /tmp/{test_id} "
        f"{Config.CERNBOX_COMPUTER}:{Config.CERNBOX_FOLDER_RUN}/{test_id}"
    )
    logger.info(f"Uploading zip file to CERNbox with command: {cmd}")
    os.system(cmd)
    
    return f"/{test_id}/output.zip"


def upload_results_to_database(test_id: str,
                               date: str,
                               session: str,
                               xml_config: Dict,
                               board_map: Dict,
                               module_map: Dict,
                               noise_map: Dict,
                               uploaded_file: str,
                               command: str,
                               args,runStatus="done") -> str:
    """
    Upload test results to database
    
    Args:
        test_id: Test ID string
        date: Test date string
        session: Session name
        xml_config: XML configuration dictionary
        board_map: Board mapping dictionary
        module_map: Module mapping dictionary
        noise_map: Noise measurement dictionary
        uploaded_file: Path to uploaded file
        command: Command used for test
        args: Parsed command line arguments
        
    Returns:
        Test run name
    """
    from databaseTools import uploadRunToDB
    
    # Get webdav hash values
    hash_location = os.path.expanduser(Config.HASH_VALUE_LOCATION)
    hash_read, hash_write = open(hash_location).read().strip().split("\n")[0].split("|")
    
    # Prepare run data
    run_number = test_id.split("Run_")[1]
    new_run = {
        'runNumber': f"run{run_number}",
        'runDate': date,
        'runSession': session,
        'runStatus': runStatus,
        'runType': command,
        'runBoards': board_map,
        'runModules': module_map,
        'runNoise': noise_map,
        'runConfiguration': xml_config,
        'runFile': f"https://cernbox.cern.ch/files/link/public/{hash_read}/{uploaded_file}"
    }
    
    if Config.VERBOSE > 1:
        logger.debug(f"newRun: {pformat(new_run)}")
    logger.info(f"Output uploaded to {uploaded_file}")
    logger.info(f"CERNbox link (folder): https://cernbox.cern.ch/files/link/public/{hash_read}/{test_id}")
    logger.info(f"CERNbox link (zip file): https://cernbox.cern.ch/files/link/public/{hash_read}/{uploaded_file}")
    
    # Upload to database
    test_run_name = uploadRunToDB(new_run)
    logger.info(f"moduleTest.py completed. test_runName: {test_run_name}")
    
    return test_run_name


def run_analysis(test_run_name: str, args) -> None:
    """
    Run analysis on test results
    
    Args:
        test_run_name: Test run name
        args: Parsed command line arguments
    """
    from databaseTools import getRunFromDB
    from updateTestResult import updateTestResult
    
    run = getRunFromDB(test_run_name)
    
    logger.info("\nRUN:")
    logger.info(run)
    logger.info("\nSINGLE MODULE TEST:")
    
    for module_test_name in run['moduleTestName']:
        logger.info(f"\n######## Single Module Test: {module_test_name} ########")
        
        # Skip analysis if requested or test failed
        if args.skipUploadResults or module_test_name[0] == "-":
            continue
        
        logger.info("Running updateTestResult")
        logger.info(f"++++++++++++++++++  Run updateTestResult on {module_test_name} ++++++++++++++++++")
        updateTestResult(module_test_name, tempSensor=args.tempSensor)


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def setup_environment(args):
    """
    Setup the testing environment
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Tuple of (ph2acf_version, setting_folder)
    """
    from tools import checkAndFixRunNumbersDat
    from shellCommands import updateSettingsLink
    
    ph2acf_version = args.version
    
    if ph2acf_version == "local":
        logger.info("\nI will use local Ph2ACF instead of Docker!")
        if "PH2ACF_BASE_DIR" in os.environ:
            ph2acf = os.environ['PH2ACF_BASE_DIR']
        else:
            raise Exception(
                "No Ph2ACF available (eg. no runCalibration). "
                "Please do 'source setup.sh' from a Ph2ACF folder!"
            )
        setting_folder = f"{ph2acf}/settings"
        logger.info(f"Local Ph2ACF folder: {ph2acf}\n")
    else:
        setting_folder = Config.SETTING_FOLDER_DOCKER
    
    updateSettingsLink(setting_folder)
    checkAndFixRunNumbersDat(target_dir=Config.THERMAL_HOME)
    
    return ph2acf_version, setting_folder


def print_configuration(args, setting_folder: str, ph2acf_version: str) -> None:
    """Print configuration summary"""
    logger.info("")
    logger.info("moduleTest configuration:")
    logger.info("")
    logger.info(f"Copying settings folder from: {setting_folder}")
    logger.info(f"Ph2ACF version: {ph2acf_version}")
    logger.info(f"Verbose: {Config.VERBOSE}")
    logger.info(f"Command: {args.command}")
    logger.info(f"Session: {args.session}")
    logger.info(f"Module: {args.module}")
    logger.info(f"Slot: {args.slot}")
    logger.info(f"SlotBI: {args.slotBI}")
    logger.info(f"Board: {args.board}")
    logger.info(f"EdgeSelect: {args.edgeSelect}")
    logger.info(f"Firmware: {args.firmware}")
    logger.info(f"xmlPyConfigFile: {args.xmlPyConfigFile}")
    logger.info(f"ignoreConnection: {args.ignoreConnection}")
    logger.info(f"skipMongo: {args.skipMongo}")
    logger.info(f"skipModuleCheck: {args.skipModuleCheck}")
    logger.info(f"runFpgaConfig: {args.runFpgaConfig}")
    logger.info(f"useExistingModuleTest: {args.useExistingModuleTest}")
    logger.info(f"useExistingXmlFile: {args.useExistingXmlFile}")
    logger.info(f"addNewModule: {args.addNewModule}")
    logger.info(f"g10: {args.g10}")
    logger.info(f"g5: {args.g5}")
    logger.info(f"skipUploadResults: {args.skipUploadResults}")
    logger.info(f"lpGBT: {args.lpGBT}")
    logger.info(f"strip: {args.strip}")
    logger.info(f"pixel: {args.pixel}")
    logger.info(f"hybrid: {args.hybrid}")
    logger.info(f"xmlTemplate: {Config.XML_TEMPLATE}")
    logger.info(f"xmlOutput: {Config.XML_OUTPUT}")
    logger.info(f"connectionMapFileName: {Config.CONNECTION_MAP_FILENAME}")
    logger.info("")


def main():
    """Main execution function"""
    # Parse arguments
    args = parse_arguments()
    
    # Set logging level based on verbose argument
    set_verbose_level(args.verbose)
    
    # Print examples
    logger.info("")
    logger.info("Example: python3 moduleTest.py --module PS_26_05-IBA_00102 --slot 0 "
          "--board fc7ot2 -c readOnlyID --session session1")
    logger.info("")
    logger.info("Example: python3 moduleTest.py --module auto --slotBI 3 -c readOnlyID "
          "--session session1 --runFpgaConfig --g10")
    logger.info("")
    
    # Validate arguments
    validate_arguments(args)
    
    # Setup environment
    ph2acf_version, setting_folder = setup_environment(args)
    
    # Print configuration
    print_configuration(args, setting_folder, ph2acf_version)
    
    # Parse slot and module information
    board = args.board
    lpgbt_file = args.lpGBT
    optical_groups = args.slot.split(",")
    slots_bi = args.slotBI.split(",")
    modules = args.module.split(",")
    
    # Validate slot/module mapping
    validate_slot_module_mapping(optical_groups, slots_bi, modules, args)
    
    # Handle burn-in slots
    if args.slotBI != "-1":
        from databaseTools import getOpticaGroupAndBoardFromSlots
        logger.info(f"Using --slotBI {slots_bi} to get optical groups and board name:")
        board, optical_groups = getOpticaGroupAndBoardFromSlots(slots_bi)
        logger.info(f"Optical Groups: {optical_groups}, Board: {board} found.")
    
    # Parse chip configuration
    edge_select = args.edgeSelect
    hybrids = [int(h) for h in args.hybrid.split(",") if h]
    pixels = [int(h) for h in args.pixel.split(",") if h]
    strips = [int(h) for h in args.strip.split(",") if h]
    
    validate_chip_numbers(hybrids, pixels, strips)
    
    # Handle existing XML file
    if args.useExistingXmlFile:
        from tools import parse_module_settings
        logger.info("Using existing module test - overwriting configuration from file.")
        board, optical_groups, hybrids, strips, pixels = parse_module_settings(
            args.useExistingXmlFile
        )
        modules = ["auto" for _ in optical_groups]
        optical_groups = [int(s) for s in optical_groups]
        logger.info(f"New values: board={board}, OGs={optical_groups}, hybrids={hybrids}, "
              f"strips={strips}, pixels={pixels}, modules={modules}")
    
    # Handle readOnlyID mode
    read_only_id = (args.command == "readOnlyID")
    if read_only_id:
        hybrids = [hybrids[0]]
        pixels = []
        strips = [0]
    
    # Determine firmware
    firmware = determine_firmware(args)
    optical_groups = [int(s) for s in optical_groups]
    
    # Preliminary checks
    logger.info("")
    logger.info("++++++++++++++++++ Preliminary checks ++++++++++++++++++")
    logger.info("")
    
    if not args.useExistingXmlFile and not args.useExistingModuleTest:
        # Verify module connections
        logger.info("")
        logger.info("++++++++++++++++++ Check modules match DB, resolve 'auto', check 10G/5G ++++++++++++++++++")
        logger.info("")
        
        modules = verify_module_connections(board, optical_groups, modules, args)
        
        # Check and install firmware
        check_and_install_firmware(board, modules, firmware, args)
        
        # Resolve lpGBT files
        lpgbt_file = resolve_lpgbt_files(lpgbt_file, modules)
    
    # Create XML configuration
    logger.info("")
    logger.info("++++++++++++++++++ Creation of the XML file ++++++++++++++++++")
    logger.info("")
    
    xml_config, xml_file, xml_py_config_file = create_xml_configuration(
        board, optical_groups, hybrids, strips, pixels,
        lpgbt_file, edge_select, args, xml_py_config_filename=args.xmlPyConfigFile
    )
    
    if Config.VERBOSE > 1:
        logger.debug("xmlConfig:")
        logger.debug(pformat(xml_config))
    
    # Run module test
    logger.info("")
    logger.info("#### Launch the test ###")
    test_id, date, error_code = run_module_test(xml_file, firmware, board, args)
    

#          test_id, date, session, xml_config, board_map, module_map,
#            noise_map, uploaded_file, args.command, args
    date = date.replace(" ", "T").split(".")[0]

    board_map = {}
    module_map = {}
    noise_map = {}
    uploaded_file = ""
    try:
            
        logger.info("++++++++++++++++++ Test completed. Parse ROOT file ++++++++++++++++++")
        
        # Get ROOT file
        from tools import getROOTfile
        root_file_name = f"Results/{test_id}/Results.root"
        uploaded_file = prepare_result_files(
                test_id, root_file_name, xml_py_config_file, xml_file, modules, args
        )

        root_file = (
            getROOTfile(test_id) if not args.useExistingModuleTest
            else getROOTfile(args.useExistingModuleTest)
        )       

        # Process results
        ids, noise_per_chip = process_test_results(root_file, xml_config)
        
        # Handle existing XML file - remove missing IDs
        if args.useExistingXmlFile:
            for key in list(ids.keys()):
                if ids[key] == "-1":
                    logger.debug(f"Deleting {key}")
                    del ids[key]
                    del xml_config["boards"][str(key[0])]["opticalGroups"][str(key[1])]
        
        if Config.VERBOSE > 5:
            logger.debug(pformat(ids))
        
        # Handle readOnlyID mode
        if read_only_id and args.skipMongo:
            logger.info(pformat(ids))
            logger.info("")
            logger.info("readOnlyID finished successfully.")
            logger.info("")
            return
        
        # Get results per module
        from tools import getResultsPerModule
        logger.info("++++++++++++++++++ Get noise and evaluate module: pass/failed ++++++++++++++++++")
        if Config.VERBOSE > 5:
            logger.debug(pformat(noise_per_chip))
        result = getResultsPerModule(noise_per_chip, xml_config)
        
        # Verify and update modules in database
        if not args.skipMongo:
            logger.info("")
            logger.info("++++++++++++++++++  Check module name vs hardware ID ++++++++++++++++++")
            hw_to_module_name, hw_to_mongo_id = verify_and_update_modules(
                ids, modules, optical_groups, xml_config, args
            )
            
            # Skip analysis for certain commands
            if args.command in Config.COMMANDS_TO_SKIP_ANALYSIS:
                logger.info("")
                logger.info(f"Skipping updateTestResult for {args.command} test. "
                    f"(commandToSkipAnalysis={Config.COMMANDS_TO_SKIP_ANALYSIS})")
                logger.info(f"{args.command} test finished successfully.")
                logger.info("")
                return
            
                logger.info("++++++++++++++++++  Make folder on CERNbox, create zip, upload ++++++++++++++++++")
            
            # Prepare and upload results

            logger.info("++++++++++++++++++  Create session and run and upload to DB ++++++++++++++++++")
            
            # Create noise map
            from makeXml import makeNoiseMap
            board_map, module_map, noise_map = makeNoiseMap(
                xml_config, noise_per_chip, ids, hw_to_module_name
            )
            
            # Format date
            if args.useExistingModuleTest:
                timestamp = str(root_file.Get("Detector/CalibrationStartTimestamp_Detector"))
                date = timestamp.replace(" ", "T")
            runStatus="done" if error_code is None else "failed nicely"

    except Exception as e:
        #build module map from configuration
        if args.command in Config.COMMANDS_TO_SKIP_ANALYSIS:
                return
                
        from databaseTools import getModuleConnectedToFC7, getFiberLink   
        for board_id, board in xml_config["boards"].items():
            board_id = int(board_id)
            fc7 = board["ip"] ##get fc7ot3:50001
            fc7 = fc7.split(":")[0] #keep fc7ot3
            board_map[board_id] = fc7
            for opticalGroup_id, opticalGroup in board["opticalGroups"].items():
                opticalGroup_id = int(opticalGroup_id)
                module_from_db = getModuleConnectedToFC7(fc7.upper(), f"OG{opticalGroup_id}")
                module_map[f"{fc7}_optical{opticalGroup_id}"] = (module_from_db, -1)


        runStatus=error_code 
        logger.error(f"Error during processing of test results: {e}")
        
    if not args.skipMongo:
        # Get or create session
        if args.session != "-1":
            session = args.session
        else:
            from databaseTools import createSession
            session = createSession(args.message, modules)
        # Upload results to database
        test_run_name = upload_results_to_database(
            test_id, date, session, xml_config, board_map, module_map,
            noise_map, uploaded_file, args.command, args,runStatus=runStatus
        )
    if not error_code:
        # Run analysis
        run_analysis(test_run_name, args)
    else:
        raise Exception(f"Module test failed with error code {error_code}.")

 
# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    main()
