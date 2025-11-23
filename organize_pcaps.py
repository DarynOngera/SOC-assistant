#!/usr/bin/env python3
"""
Organize existing PCAPs for frontend simulation
Copies and renames PCAPs to standard format
"""

import os
import shutil
from datetime import datetime

def organize_pcaps():
    """Organize existing PCAPs"""
    
    print("="*60)
    print("ORGANIZING EXISTING PCAPS")
    print("="*60 + "\n")
    
    base_dir = '/home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture'
    pcap_dir = os.path.join(base_dir, 'pcaps')
    mininet_dir = os.path.join(base_dir, 'mininet')
    
    # Ensure pcap directory exists
    os.makedirs(pcap_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Check for normal traffic PCAP
    normal_pcaps = [f for f in os.listdir(pcap_dir) if f.startswith('normal_traffic')]
    
    if normal_pcaps:
        print(f"✓ Found {len(normal_pcaps)} normal traffic PCAP(s)")
        for pcap in normal_pcaps:
            size = os.path.getsize(os.path.join(pcap_dir, pcap))
            print(f"  • {pcap} ({size:,} bytes)")
    else:
        print("⚠ No normal traffic PCAP found")
        print("  Creating placeholder...")
        # We'll use one of the existing ones
    
    # Copy attack PCAPs to standard location
    print(f"\n✓ Found attack PCAPs in {mininet_dir}")
    
    attack_mapping = {
        'syn_flood.pcap': f'attack_syn_flood_{timestamp}.pcap',
        'port_scan.pcap': f'attack_port_scan_{timestamp}.pcap',
        'udp_flood.pcap': f'attack_udp_flood_{timestamp}.pcap',
        'http_flood.pcap': f'attack_http_flood_{timestamp}.pcap'
    }
    
    copied = []
    
    for src_name, dst_name in attack_mapping.items():
        src_path = os.path.join(mininet_dir, src_name)
        dst_path = os.path.join(pcap_dir, dst_name)
        
        if os.path.exists(src_path):
            # Check if already copied
            existing = [f for f in os.listdir(pcap_dir) if f.startswith(dst_name.split('_202')[0])]
            if not existing:
                shutil.copy2(src_path, dst_path)
                size = os.path.getsize(dst_path)
                print(f"  ✓ Copied {src_name} → {dst_name} ({size:,} bytes)")
                copied.append(dst_name)
            else:
                print(f"  • {src_name} already exists as {existing[0]}")
        else:
            print(f"  ✗ {src_name} not found")
    
    # Summary
    print("\n" + "="*60)
    print("PCAP ORGANIZATION COMPLETE")
    print("="*60)
    
    all_pcaps = sorted(os.listdir(pcap_dir))
    
    print(f"\nAvailable PCAPs in {pcap_dir}:\n")
    
    normal = [p for p in all_pcaps if 'normal_traffic' in p]
    attacks = [p for p in all_pcaps if 'attack_' in p]
    
    print(f"Normal Traffic ({len(normal)}):")
    for pcap in normal:
        size = os.path.getsize(os.path.join(pcap_dir, pcap))
        print(f"  ✓ {pcap} ({size:,} bytes)")
    
    print(f"\nAttack Traffic ({len(attacks)}):")
    for pcap in attacks:
        size = os.path.getsize(os.path.join(pcap_dir, pcap))
        attack_type = pcap.split('_')[1]
        print(f"  ✓ {pcap} ({size:,} bytes) - {attack_type.upper()}")
    
    print("\n" + "="*60)
    print("READY FOR TESTING")
    print("="*60)
    print("\nNext steps:")
    print("  1. Test: python3 test_local_simulation.py")
    print("  2. Start dashboard: cd src/dashboard && python3 server.py")
    print("  3. Open UI: http://localhost:5000")
    print("  4. Test simulations in Mininet Simulation page")
    
    return True

if __name__ == '__main__':
    organize_pcaps()
