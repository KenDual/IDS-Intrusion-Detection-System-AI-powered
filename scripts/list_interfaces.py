"""
List all network interfaces available for packet capture
"""
from scapy.all import get_if_list, conf

print("=" * 80)
print("AVAILABLE NETWORK INTERFACES")
print("=" * 80)
print()

# Method 1: Simple list
print("[1] Simple Interface List:")
interfaces = get_if_list()
for i, iface in enumerate(interfaces, 1):
    print(f"  {i}. {iface}")

print()
print("-" * 80)
print()

# Method 2: Detailed with descriptions
print("[2] Detailed Interface Information:")
try:
    for iface_name, iface_obj in conf.ifaces.items():
        print(f"\nInterface: {iface_name}")
        print(f"  Description: {iface_obj.description if hasattr(iface_obj, 'description') else 'N/A'}")
        print(f"  Network Name: {iface_obj.network_name if hasattr(iface_obj, 'network_name') else 'N/A'}")
        print(f"  IP: {iface_obj.ip if hasattr(iface_obj, 'ip') else 'N/A'}")
except Exception as e:
    print(f"Could not get detailed info: {e}")

print()
print("=" * 80)
print("INSTRUCTIONS:")
print("=" * 80)
print("Copy the interface name (GUID format) of your active network connection")
print("and update it in: app/capture/config.py")
print()
print("Example:")
print("  INTERFACE = '{F698E47B-E6A7-49EA-B116-E965EF9F3A64}'")
print()