#!/usr/bin/env python3
# NOTE: upload will not work on prototype modules because of strict validation form py4dbupload; for thermal user on pccmslab1 I have fixed it locally by changing py4dbupload/modules/Utils.py line 42 to: r = re.compile('PS_(?:16|26|40)_(?:05_)?(?:IBA|IPG|BRN|FNL|DSY)-[0-9]{5}')

import sys
import select
import time
import socket
import json
from datetime import datetime
import os
import numpy as np
import argparse
import shlex
import subprocess
import tempfile

# Define scan types
SCAN_CONFIGS = {
    'before_encapsulation': {'max_voltage': 350, 'step': 10},
    'after_encapsulation': {'max_voltage': 800, 'step': 10}
}

def handle_interactive_process(command, timeout=60):
    # Force unbuffered output in subprocess
    # env = os.environ.copy()
    # env['PYTHONUNBUFFERED'] = '1'
    
    process = subprocess.Popen(
        command,
        shell=True,
        executable='/bin/bash',
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        # bufsize=1,  # Line buffering
        # env=env
    )
    
    start_time = time.time()
    output_buffer = ""
    
    while True:
        if process.poll() is not None:
            print("Process ended with code:", process.returncode)
            break
            
        if time.time() - start_time > timeout:
            process.kill()
            print("Process timed out")
            return -1
            
        reads = [process.stdout, process.stderr]
        ret = select.select(reads, [], [], 0.1)[0]
        
        for pipe in ret:
            char = pipe.read(1)
            if char:
                output_buffer += char
                print(char, end='', flush=True)  # Debug: show real-time output
                
                # if char == '\n':
                #     # Process complete line
                #     print(output_buffer)  # Debug
                #     output_buffer = ""
                    
                # Check for auth prompt at end of buffer 
                # NOTE: Not working as expected, we rely on .session.cache 
                # if output_buffer.rstrip().endswith(('Username: ', 'Password: ', 'login:')):
                #     print("\nDEBUG: Auth prompt detected:", output_buffer)  # Debug
                #     response = input("") + "\n"
                #     process.stdin.write(response)
                #     process.stdin.flush()
                #     output_buffer = ""
    
    return process.returncode

class TCPUtil():
    """Utility class for tcp communication management."""
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.headerBytes = 4
        self.connectSocket()

    def connectSocket(self):
        self.socket.connect((self.ip, self.port))

    def sendMessage(self, message):
        encodedMessage = self.encodeMessage(message)
        self.socket.send(encodedMessage)

    def encodeMessage(self, message):
        messageLength = len(message) + self.headerBytes + 4
        N = 0
        return (messageLength).to_bytes(4, byteorder='big') + N.to_bytes(4, byteorder='big') + message.encode('utf-8')

class IVCurveMeasurement:
    def __init__(self, channel, voltage_steps, delay=5.0, voltage_threshold=0.5, voltage_threshold_time=0.5, voltage_threshold_retries=20, settling_time=0.5, final_voltage=300):
        self.channel = channel
        self.voltage_steps = voltage_steps
        self.delay = delay
        self.voltage_threshold = voltage_threshold
        self.voltage_threshold_time = voltage_threshold_time
        self.voltage_threshold_retries = voltage_threshold_retries
        self.settling_time = settling_time
        self.measurements = []
        self.max_data_retries = 3  # Add max retries for incomplete data
        self.final_voltage = final_voltage
        
    def get_caen_data(self):
        """Get data from CAEN with retry logic for incomplete data"""
        for attempt in range(self.max_data_retries):
            measure_conn = TCPUtil(ip='192.168.0.45', port=7000)
            measure_conn.sendMessage('GetStatus,PowerSupplyId:caen')
            data = measure_conn.socket.recv(100000)[8:].decode("utf-8")
            measure_conn.socket.close()
            
            # Verify data integrity
            parsed_data = {}
            valid_data = True
            
            for token in data.split(','):
                if token.startswith('caen'):
                    if ":" not in token:
                        print(f"Invalid token in attempt {attempt + 1}: {token}")
                        valid_data = False
                        break
                    key, value = token.split(":")
                    try:
                        parsed_data[key] = float(value)
                    except ValueError:
                        valid_data = False
                        break
            
            if valid_data and len(parsed_data) > 0:
                return parsed_data
            
            print(f"Attempt {attempt + 1}: Received incomplete data, retrying...")
            time.sleep(1)  # Wait before retry
            
        raise RuntimeError("Failed to get valid data from CAEN after maximum retries")
        
    def verify_voltage(self, target_voltage):
        attempt = 0
        
        while attempt < self.voltage_threshold_retries:
            try:
                parsed_data = self.get_caen_data()
                current_voltage = parsed_data[f'caen_{self.channel}_Voltage']
                # print(f"Current voltage: {current_voltage}V")
                if abs(current_voltage - target_voltage) <= self.voltage_threshold:
                    print(f"Voltage reached target value {target_voltage} V within threshold, settling...")
                    time.sleep(self.settling_time)  # Wait for settling time
                    return True
                
                time.sleep(self.voltage_threshold_time)
                attempt += 1
            except Exception as e:
                print(f"Error reading voltage: {e}")
                attempt += 1
                continue
            
        return False

    def measure_curve(self):
        
        # turn on channel
        on_conn = TCPUtil(ip='192.168.0.45', port=7000)
        on_conn.sendMessage(f'TurnOn,PowerSupplyId:caen,ChannelId:{self.channel}')
        ack = on_conn.socket.recv(100000)[8:].decode("utf-8")
        on_conn.socket.close()
        print(f"Received acknowledgment: {ack}")
        
        # try:
        try:
            for voltage in self.voltage_steps:
                print(f"Setting voltage to {voltage} V")
                # Create new connection for voltage setting
                voltage_conn = TCPUtil(ip='192.168.0.45', port=7000)
                voltage_conn.sendMessage(f'SetVoltage,PowerSupplyId:caen,ChannelId:{self.channel},Voltage:{voltage}')
                ack = voltage_conn.socket.recv(100000)[8:].decode("utf-8")
                voltage_conn.socket.close()
                print(f"Received acknowledgment: {ack}")
                
                time.sleep(self.delay)  # Wait for voltage to stabilize
                
                # Verify voltage is within threshold
                if not self.verify_voltage(voltage):
                    print(f"Warning: Could not reach target voltage {voltage}V within threshold")
                    continue
                
                try:
                    parsed_data = self.get_caen_data()
                    measurement = {
                        'Voltage': -parsed_data[f'caen_{self.channel}_Voltage'], # NOTE: Negative voltage for IV curve
                        'Current': parsed_data[f'caen_{self.channel}_Current'] * 1e3, # NOTE: Convert to nA assuming the readout is in uA
                        'Temperature': 25.0,
                        'Relative Humidity': 50.0,
                        'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    self.measurements.append(measurement)
                except Exception as e:
                    print(f"Error during measurement at {voltage}V: {e}")
                    continue
                
        finally:
            # Turn off channel with new connection
            final_conn = TCPUtil(ip='192.168.0.45', port=7000)
            final_conn.sendMessage(f'TurnOff,PowerSupplyId:caen,ChannelId:{self.channel}')
            ack = final_conn.socket.recv(100000)[8:].decode("utf-8")
            final_conn.socket.close()
            
            print(f"After TurnOff, setting final voltage to {self.final_voltage} V")
            voltage_conn = TCPUtil(ip='192.168.0.45', port=7000)
            voltage_conn.sendMessage(f'SetVoltage,PowerSupplyId:caen,ChannelId:{self.channel},Voltage:{self.final_voltage}')
            ack = voltage_conn.socket.recv(100000)[8:].decode("utf-8")
            voltage_conn.socket.close()
            print(f"Received acknowledgment: {ack}")

    def save_to_csv(self, output_path, run_info):
        """Save measurements to CSV file in the required format"""
        target_file = output_path
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(target_file), exist_ok=True)
        
        with open(target_file, 'w') as f:
            # Write header information
            f.write('#NameLabel,' + run_info.get('Module_ID', 'TEST_MODULE') + "\n")
            f.write('#Date,' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
            f.write("#Comment," + run_info.get('Comment', 'IV curve measurement') + "\n")
            f.write("#Location," + run_info.get('Location', 'TEST_LOCATION') + "\n")
            f.write("#Inserter," + run_info.get('Operator', 'TEST_OPERATOR') + "\n")
            f.write("#RunType," + run_info.get('Run_type', 'IV_CURVE') + "\n")
            f.write("\n")
            
            # Write temperature summary
            f.write("STATION, AV_TEMP_DEGC, AV_RH_PRCNT\n")
            mean_temp = sum(m['Temperature'] for m in self.measurements) / len(self.measurements)
            mean_rh = sum(m['Relative Humidity'] for m in self.measurements) / len(self.measurements)
            f.write(f"{run_info.get('Station_Name', 'TEST_STATION')},{mean_temp},{mean_rh}\n\n")
            
            # Write measurement data
            f.write("VOLTS, CURRNT_NAMP, TEMP_DEGC, RH_PRCNT, TIME\n")
            for point in self.measurements:
                f.write(f"{point['Voltage']},{point['Current']},{point['Temperature']},"
                       f"{point['Relative Humidity']},{point['Timestamp']}\n")
        
        return target_file

def get_default_filename(channel, module_name, scan_type):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"IV_curve_{channel}_{module_name}_{scan_type}_{timestamp}.csv"

def measure_and_upload(
    channel,
    scan_type,
    delay=5.0,
    voltage_threshold=0.5,
    voltage_threshold_time=0.5,
    voltage_threshold_retries=20,
    settling_time=0.5,
    output_file=None,
    output_dir='./IVdata',
    module_name='TEST',
    upload=False,
    store_locally=False,
    final_voltage=300
):
    """
    Measure IV curve and optionally upload to database
    Returns: (exit_code, file_path) tuple where file_path is None if not stored locally
    """
    # Generate voltage steps based on scan type
    scan_config = SCAN_CONFIGS[scan_type]
    voltage_steps = np.arange(0, scan_config['max_voltage'] + scan_config['step'], scan_config['step'])
    
    # Configure measurement
    iv_curve = IVCurveMeasurement(
        channel=channel,
        voltage_steps=voltage_steps,
        delay=delay,
        voltage_threshold=voltage_threshold,
        voltage_threshold_time=voltage_threshold_time,
        voltage_threshold_retries=voltage_threshold_retries,
        settling_time=settling_time,
        final_voltage=final_voltage
    )
    
    # Perform measurement
    iv_curve.measure_curve()
    
    # Prepare output filename and path
    final_output_file = None
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=not store_locally) as tmp_file:
        output_path = tmp_file.name
        if store_locally:
            if output_file:
                final_output_file = output_file
            else:
                final_output_file = get_default_filename(channel, module_name, scan_type)
            final_output_path = os.path.join(output_dir, final_output_file)
        
        # Save results
        run_info = {
            "Module_ID": module_name,
            "Comment": f"{scan_type} measurement",
            "Location": "Pisa",
            "Operator": os.getenv('USER', 'TEST_USER'),
            "Run_type": "IV_TEST",
            "Station_Name": "cleanroom"
        }
        
        saved_file = iv_curve.save_to_csv(output_path, run_info)
        
        if upload:
            print("Uploading to central database...")
            upload_command = f"source py4dbupload/bin/setup.sh && python3 ./py4dbupload/run/uploadOTModuleIV.py --upload --store --data={saved_file}"
            returncode = handle_interactive_process(upload_command)
            if returncode != 0:
                print("Upload failed")
                return 1
        
        if store_locally:
            os.makedirs(os.path.dirname(final_output_path), exist_ok=True)
            with open(saved_file, 'r') as src, open(final_output_path, 'w') as dst:
                dst.write(src.read())
            print(f"Measurements saved to: {final_output_path}")
    
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='IV Curve Measurement Script')
    parser.add_argument('--channel', type=str, required=True, help='Channel ID (e.g., HV005)')
    parser.add_argument('--scan-type', type=str, choices=SCAN_CONFIGS.keys(), required=True,
                      help='Type of scan to perform')
    parser.add_argument('--delay', type=float, default=5.0,
                      help='Delay between measurements (default: 5.0s)')
    parser.add_argument('--voltage-threshold', type=float, default=0.5,
                      help='Voltage verification threshold (default: 0.5V)')
    parser.add_argument('--voltage-threshold-time', type=float, default=0.5,
                        help='Time between voltage threshold checks (default: 0.5s)')
    parser.add_argument('--voltage-threshold-retries', type=int, default=20,
                        help='Number of retries for voltage threshold check (default: 20)')
    parser.add_argument('--settling-time', type=float, default=0.5,
                      help='Settling time after reaching target voltage (default: 0.5s)')
    parser.add_argument('--output-file', type=str,
                      help='Output file path (default: auto-generated)')
    parser.add_argument('--output-dir', type=str, default='./IVdata',
                      help='Output directory (default: /IVdata in current directory)')
    parser.add_argument('--module-name', type=str, default='TEST',
                      help='Module name (default: TEST)')
    parser.add_argument('--upload', action='store_true', help='Upload to central database')
    parser.add_argument('--store-locally', action='store_true', help='Store the CSV file locally')
    parser.add_argument('--final-voltage', type=float, default=300,
                      help='Final voltage to set before turning off (default: 300V)')
    
    args = parser.parse_args()
    
    exit_code = measure_and_upload(
        channel=args.channel,
        scan_type=args.scan_type,
        delay=args.delay,
        voltage_threshold=args.voltage_threshold,
        voltage_threshold_time=args.voltage_threshold_time,
        voltage_threshold_retries=args.voltage_threshold_retries,
        settling_time=args.settling_time,
        output_file=args.output_file,
        output_dir=args.output_dir,
        module_name=args.module_name,
        upload=args.upload,
        store_locally=args.store_locally,
        final_voltage=args.final_voltage
    )
    
    print(f"Script finished with exit code: {exit_code}")
    sys.exit(exit_code)