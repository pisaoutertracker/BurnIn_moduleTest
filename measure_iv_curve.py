#!/usr/bin/env python3
import sys
import time
import socket
import json
from datetime import datetime
import os
import numpy as np
import argparse
from readout_test import TCPUtil

# Define scan types
SCAN_CONFIGS = {
    'before_encapsulation': {'max_voltage': 350, 'step': 10},
    'after_encapsulation': {'max_voltage': 800, 'step': 10}
}

class IVCurveMeasurement:
    def __init__(self, channel, voltage_steps, delay=5.0, voltage_threshold=0.5, settling_time=0.5):
        self.channel = channel
        self.voltage_steps = voltage_steps
        self.delay = delay
        self.voltage_threshold = voltage_threshold
        self.voltage_settiling_time = 3
        self.settling_time = settling_time
        self.measurements = []
        self.max_data_retries = 3  # Add max retries for incomplete data
        
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
        max_attempts = 10
        attempt = 0
        
        while attempt < max_attempts:
            try:
                parsed_data = self.get_caen_data()
                current_voltage = parsed_data[f'caen_{self.channel}_Voltage']
                # print(f"Current voltage: {current_voltage}V")
                if abs(current_voltage - target_voltage) <= self.voltage_threshold:
                    print(f"Voltage reached target value {target_voltage} V within threshold, settling...")
                    time.sleep(self.settling_time)  # Wait for settling time
                    return True
                
                time.sleep(self.voltage_settiling_time)
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
                        'Voltage': parsed_data[f'caen_{self.channel}_Voltage'],
                        'Current': parsed_data[f'caen_{self.channel}_Current'] * 1e9,
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
            final_conn.socket.close()

    def save_to_csv(self, output_path, run_info):
        """Save measurements to CSV file in the required format"""
        target_file = output_path
        
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

def main():
    parser = argparse.ArgumentParser(description='IV Curve Measurement Script')
    parser.add_argument('--channel', type=str, required=True, help='Channel ID (e.g., HV005)')
    parser.add_argument('--scan-type', type=str, choices=SCAN_CONFIGS.keys(), required=True,
                      help='Type of scan to perform')
    parser.add_argument('--delay', type=float, default=5.0,
                      help='Delay between measurements (default: 5.0s)')
    parser.add_argument('--voltage-threshold', type=float, default=0.5,
                      help='Voltage verification threshold (default: 0.5V)')
    parser.add_argument('--settling-time', type=float, default=0.5,
                      help='Settling time after reaching target voltage (default: 0.5s)')
    parser.add_argument('--output-file', type=str,
                      help='Output file path (default: auto-generated)')
    parser.add_argument('--output-dir', type=str, default='./data',
                      help='Output directory (default: current directory)')
    parser.add_argument('--module-name', type=str, default='TEST',
                      help='Module name (default: TEST)')
    
    args = parser.parse_args()
    
    # Generate voltage steps based on scan type
    scan_config = SCAN_CONFIGS[args.scan_type]
    voltage_steps = np.arange(0, scan_config['max_voltage'] + scan_config['step'], scan_config['step'])
    
    # Configure measurement
    iv_curve = IVCurveMeasurement(
        channel=args.channel,
        voltage_steps=voltage_steps,
        delay=args.delay,
        voltage_threshold=args.voltage_threshold,
        settling_time=args.settling_time
    )
    
    # Perform measurement
    iv_curve.measure_curve()
    
    # Prepare output filename
    output_file = args.output_file if args.output_file else get_default_filename(args.channel, args.scan_type)
    output_path = os.path.join(args.output_dir, output_file)
    
    # Save results
    run_info = {
        "Module_ID": args.module_name, # this must be the module serial number in the central database
        "Comment": f"{args.scan_type} measurement",
        "Location": "Pisa", # this must be a known location in the central database
        "Operator": os.getenv('USER', 'TEST_USER'),
        "Run_type": "IV_TEST",
        "Station_Name": "cleanroom"
    }
    
    saved_file = iv_curve.save_to_csv(output_path, run_info)
    print(f"Measurements saved to: {saved_file}")

if __name__ == "__main__":
    main()