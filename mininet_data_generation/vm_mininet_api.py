#!/usr/bin/env python3
"""
VM Mininet API Server
Exposes Mininet functionality via REST API for remote control
Runs on CentOS VM - handles network simulation and PCAP generation only
"""

import os
import sys
import json
import logging
import threading
import subprocess
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for remote access

# Configuration
PCAP_DIR = Path("data_capture/pcaps")
TOPOLOGY_DIR = Path("topology")
PCAP_DIR.mkdir(parents=True, exist_ok=True)

# Global state
simulation_state = {
    'active': False,
    'mode': None,
    'attack_type': None,
    'start_time': None,
    'duration': 0,
    'pcap_file': None,
    'process': None
}

simulation_lock = threading.Lock()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'VM Mininet API',
        'timestamp': datetime.now().isoformat(),
        'mininet_available': check_mininet_available()
    })


@app.route('/api/mininet/status', methods=['GET'])
def get_status():
    """Get current simulation status"""
    with simulation_lock:
        return jsonify({
            'active': simulation_state['active'],
            'mode': simulation_state['mode'],
            'attack_type': simulation_state['attack_type'],
            'start_time': simulation_state['start_time'],
            'duration': simulation_state['duration'],
            'pcap_file': str(simulation_state['pcap_file']) if simulation_state['pcap_file'] else None
        })


@app.route('/api/mininet/attacks', methods=['GET'])
def get_available_attacks():
    """Get list of available attack types"""
    attacks = [
        'syn_flood',
        'port_scan',
        'udp_flood',
        'icmp_flood',
        'http_flood',
        'dns_amplification',
        'brute_force',
        'slowloris'
    ]
    
    return jsonify({
        'attacks': attacks,
        'count': len(attacks)
    })


@app.route('/api/mininet/start', methods=['POST'])
def start_simulation():
    """Start Mininet simulation"""
    with simulation_lock:
        if simulation_state['active']:
            return jsonify({
                'success': False,
                'message': 'Simulation already running'
            }), 400
        
        data = request.get_json()
        mode = data.get('mode', 'normal')
        attack_type = data.get('attack_type')
        duration = data.get('duration', 60)
        samples = data.get('samples', 10000)
        
        # Validate parameters
        if mode not in ['normal', 'attack']:
            return jsonify({
                'success': False,
                'message': 'Invalid mode. Must be "normal" or "attack"'
            }), 400
        
        if mode == 'attack' and not attack_type:
            return jsonify({
                'success': False,
                'message': 'Attack type required for attack mode'
            }), 400
        
        # Check if Mininet is available
        if not check_mininet_available():
            return jsonify({
                'success': False,
                'message': 'Mininet not available. Ensure it is installed and you have root privileges.'
            }), 500
        
        try:
            # Update state
            simulation_state['active'] = True
            simulation_state['mode'] = mode
            simulation_state['attack_type'] = attack_type
            simulation_state['start_time'] = datetime.now().isoformat()
            simulation_state['duration'] = duration
            
            # Start simulation in background thread
            thread = threading.Thread(
                target=run_simulation_thread,
                args=(mode, attack_type, duration, samples)
            )
            thread.daemon = True
            thread.start()
            
            logger.info(f"Started {mode} simulation (attack: {attack_type}, duration: {duration}s)")
            
            return jsonify({
                'success': True,
                'message': f'Simulation started: {mode}',
                'mode': mode,
                'attack_type': attack_type,
                'duration': duration
            })
            
        except Exception as e:
            simulation_state['active'] = False
            logger.error(f"Error starting simulation: {e}")
            return jsonify({
                'success': False,
                'message': f'Failed to start simulation: {str(e)}'
            }), 500


@app.route('/api/mininet/stop', methods=['POST'])
def stop_simulation():
    """Stop current simulation"""
    with simulation_lock:
        if not simulation_state['active']:
            return jsonify({
                'success': False,
                'message': 'No active simulation'
            }), 400
        
        try:
            # Kill simulation process if exists
            if simulation_state['process']:
                simulation_state['process'].terminate()
                simulation_state['process'].wait(timeout=5)
            
            # Clean up Mininet
            subprocess.run(['sudo', 'mn', '-c'], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE)
            
            simulation_state['active'] = False
            simulation_state['process'] = None
            
            logger.info("Simulation stopped")
            
            return jsonify({
                'success': True,
                'message': 'Simulation stopped'
            })
            
        except Exception as e:
            logger.error(f"Error stopping simulation: {e}")
            return jsonify({
                'success': False,
                'message': f'Failed to stop simulation: {str(e)}'
            }), 500


@app.route('/api/mininet/pcaps', methods=['GET'])
def list_pcaps():
    """List available PCAP files"""
    try:
        pcap_files = []
        
        for pcap_file in PCAP_DIR.glob('*.pcap'):
            stat = pcap_file.stat()
            pcap_files.append({
                'filename': pcap_file.name,
                'path': str(pcap_file),
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        # Sort by creation time (newest first)
        pcap_files.sort(key=lambda x: x['created'], reverse=True)
        
        return jsonify({
            'pcaps': pcap_files,
            'count': len(pcap_files),
            'directory': str(PCAP_DIR)
        })
        
    except Exception as e:
        logger.error(f"Error listing PCAPs: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to list PCAPs: {str(e)}'
        }), 500


@app.route('/api/mininet/pcap/<filename>', methods=['GET'])
def download_pcap(filename):
    """Download a specific PCAP file"""
    try:
        pcap_file = PCAP_DIR / filename
        
        if not pcap_file.exists():
            return jsonify({
                'success': False,
                'message': 'PCAP file not found'
            }), 404
        
        return send_file(
            pcap_file,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.tcpdump.pcap'
        )
        
    except Exception as e:
        logger.error(f"Error downloading PCAP: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to download PCAP: {str(e)}'
        }), 500


@app.route('/api/mininet/pcap/<filename>', methods=['DELETE'])
def delete_pcap(filename):
    """Delete a specific PCAP file"""
    try:
        pcap_file = PCAP_DIR / filename
        
        if not pcap_file.exists():
            return jsonify({
                'success': False,
                'message': 'PCAP file not found'
            }), 404
        
        pcap_file.unlink()
        
        logger.info(f"Deleted PCAP: {filename}")
        
        return jsonify({
            'success': True,
            'message': f'PCAP deleted: {filename}'
        })
        
    except Exception as e:
        logger.error(f"Error deleting PCAP: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to delete PCAP: {str(e)}'
        }), 500


@app.route('/api/mininet/cleanup', methods=['POST'])
def cleanup_mininet():
    """Clean up Mininet processes and state"""
    try:
        result = subprocess.run(
            ['sudo', 'mn', '-c'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        logger.info("Mininet cleanup completed")
        
        return jsonify({
            'success': True,
            'message': 'Mininet cleanup completed',
            'output': result.stdout
        })
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return jsonify({
            'success': False,
            'message': f'Cleanup failed: {str(e)}'
        }), 500


def check_mininet_available():
    """Check if Mininet is available"""
    try:
        result = subprocess.run(
            ['which', 'mn'],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False


def run_simulation_thread(mode, attack_type, duration, samples):
    """Run simulation in background thread"""
    try:
        logger.info(f"Starting {mode} simulation thread")
        
        if mode == 'normal':
            script_path = TOPOLOGY_DIR / 'generate_normal_traffic.py'
            cmd = [
                'sudo', 'python3', str(script_path),
                '--samples', str(samples),
                '--duration', str(duration)
            ]
        else:
            script_path = TOPOLOGY_DIR / 'generate_attack_traffic.py'
            cmd = [
                'sudo', 'python3', str(script_path),
                '--attack', attack_type,
                '--samples', str(samples),
                '--duration', str(duration)
            ]
        
        # Run simulation
        logger.info(f"Executing: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        with simulation_lock:
            simulation_state['process'] = process
        
        # Wait for completion
        stdout, stderr = process.communicate(timeout=duration + 60)
        
        if process.returncode == 0:
            logger.info(f"Simulation completed successfully")
            
            # Find the generated PCAP file
            pcap_files = list(PCAP_DIR.glob('*.pcap'))
            if pcap_files:
                latest_pcap = max(pcap_files, key=lambda p: p.stat().st_ctime)
                with simulation_lock:
                    simulation_state['pcap_file'] = latest_pcap
                logger.info(f"Generated PCAP: {latest_pcap}")
        else:
            logger.error(f"Simulation failed: {stderr}")
        
    except subprocess.TimeoutExpired:
        logger.error("Simulation timed out")
        if simulation_state['process']:
            simulation_state['process'].kill()
    except Exception as e:
        logger.error(f"Error in simulation thread: {e}")
    finally:
        with simulation_lock:
            simulation_state['active'] = False
            simulation_state['process'] = None
        
        # Cleanup Mininet
        try:
            subprocess.run(['sudo', 'mn', '-c'], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE,
                         timeout=10)
        except:
            pass


if __name__ == '__main__':
    logger.info("="*60)
    logger.info("VM MININET API SERVER")
    logger.info("="*60)
    logger.info("Starting Mininet API server on VM...")
    logger.info("This server exposes Mininet functionality via REST API")
    logger.info("="*60)
    
    # Check Mininet availability
    if check_mininet_available():
        logger.info("✅ Mininet is available")
    else:
        logger.warning("⚠️  Mininet not found. Install it first!")
    
    # Start Flask server
    # Bind to 0.0.0.0 to accept connections from host
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=False,
        threaded=True
    )
