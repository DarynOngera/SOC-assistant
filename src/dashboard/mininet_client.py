#!/usr/bin/env python3
"""
Mininet Client for Local System
Communicates with VM Mininet API to control remote simulations
"""

import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MininetClient:
    """Client for remote Mininet VM API"""
    
    def __init__(self, vm_host: str, vm_port: int = 5001, timeout: int = 30):
        """
        Initialize Mininet client
        
        Args:
            vm_host: VM hostname or IP address
            vm_port: VM API port (default: 5001)
            timeout: Request timeout in seconds
        """
        self.vm_host = vm_host
        self.vm_port = vm_port
        self.timeout = timeout
        self.base_url = f"http://{vm_host}:{vm_port}"
        
        logger.info(f"Initialized Mininet client for VM: {self.base_url}")
    
    def health_check(self) -> Dict:
        """Check if VM Mininet API is healthy"""
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=5
            )
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json()
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Health check failed: {e}")
            return {
                'success': False,
                'message': f'VM not reachable: {str(e)}'
            }
    
    def get_status(self) -> Dict:
        """Get current simulation status"""
        try:
            response = requests.get(
                f"{self.base_url}/api/mininet/status",
                timeout=self.timeout
            )
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json()
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get status: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def get_available_attacks(self) -> Dict:
        """Get list of available attack types"""
        try:
            response = requests.get(
                f"{self.base_url}/api/mininet/attacks",
                timeout=self.timeout
            )
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json()
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get attacks: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def start_simulation(
        self,
        mode: str = 'normal',
        attack_type: Optional[str] = None,
        duration: int = 60,
        samples: int = 10000
    ) -> Dict:
        """
        Start Mininet simulation on VM
        
        Args:
            mode: 'normal' or 'attack'
            attack_type: Type of attack (required if mode='attack')
            duration: Simulation duration in seconds
            samples: Number of samples to generate
        
        Returns:
            Dict with success status and message
        """
        try:
            payload = {
                'mode': mode,
                'attack_type': attack_type,
                'duration': duration,
                'samples': samples
            }
            
            logger.info(f"Starting {mode} simulation on VM (attack: {attack_type}, duration: {duration}s)")
            
            response = requests.post(
                f"{self.base_url}/api/mininet/start",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Simulation started: {result}")
            
            return {
                'success': True,
                'data': result
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to start simulation: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def stop_simulation(self) -> Dict:
        """Stop current simulation"""
        try:
            response = requests.post(
                f"{self.base_url}/api/mininet/stop",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info("Simulation stopped")
            
            return {
                'success': True,
                'data': result
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to stop simulation: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def list_pcaps(self) -> Dict:
        """List available PCAP files on VM"""
        try:
            response = requests.get(
                f"{self.base_url}/api/mininet/pcaps",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            return {
                'success': True,
                'data': response.json()
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list PCAPs: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def download_pcap(self, filename: str, local_path: str) -> Dict:
        """
        Download PCAP file from VM to local system
        
        Args:
            filename: PCAP filename on VM
            local_path: Local path to save file
        
        Returns:
            Dict with success status
        """
        try:
            logger.info(f"Downloading PCAP: {filename} -> {local_path}")
            
            response = requests.get(
                f"{self.base_url}/api/mininet/pcap/{filename}",
                timeout=self.timeout,
                stream=True
            )
            response.raise_for_status()
            
            # Save to local file
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"PCAP downloaded successfully: {local_path}")
            
            return {
                'success': True,
                'message': f'Downloaded to {local_path}'
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download PCAP: {e}")
            return {
                'success': False,
                'message': str(e)
        }
    
    def delete_pcap(self, filename: str) -> Dict:
        """Delete PCAP file from VM"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/mininet/pcap/{filename}",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            logger.info(f"PCAP deleted: {filename}")
            
            return {
                'success': True,
                'data': response.json()
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to delete PCAP: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def cleanup_mininet(self) -> Dict:
        """Clean up Mininet processes on VM"""
        try:
            response = requests.post(
                f"{self.base_url}/api/mininet/cleanup",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            logger.info("Mininet cleanup completed")
            
            return {
                'success': True,
                'data': response.json()
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to cleanup: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def is_available(self) -> bool:
        """Check if VM is available"""
        result = self.health_check()
        return result['success']


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize client (replace with your VM IP)
    client = MininetClient(vm_host='192.168.1.100', vm_port=5001)
    
    # Health check
    print("Checking VM health...")
    health = client.health_check()
    print(f"Health: {health}")
    
    if health['success']:
        # Get available attacks
        print("\nGetting available attacks...")
        attacks = client.get_available_attacks()
        print(f"Attacks: {attacks}")
        
        # Start normal traffic simulation
        print("\nStarting normal traffic simulation...")
        result = client.start_simulation(
            mode='normal',
            duration=30,
            samples=5000
        )
        print(f"Start result: {result}")
        
        # Check status
        import time
        time.sleep(5)
        
        print("\nChecking simulation status...")
        status = client.get_status()
        print(f"Status: {status}")
        
        # List PCAPs
        print("\nListing PCAPs...")
        pcaps = client.list_pcaps()
        print(f"PCAPs: {pcaps}")
