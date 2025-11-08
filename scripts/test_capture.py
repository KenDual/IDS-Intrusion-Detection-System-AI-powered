"""
Test Script for Phase 4 - Packet Capture & Feature Extraction

Usage:
1. Run as Administrator
2. Generate some network traffic (ping, browse web, etc.)
3. Script will capture packets and extract features
4. Press Ctrl+C to stop

Test scenarios:
- Capture real packets from network
- Group packets into flows
- Extract 25 features from flows
- Verify feature extraction works correctly
"""
import asyncio
import sys
import os
import signal

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.capture import (
    get_capture_service,
    FEATURE_NAMES,
    N_FEATURES
)


class CaptureTest:
    """Test class for packet capture and feature extraction"""

    def __init__(self):
        self.service = get_capture_service()
        self.flows_received = 0
        self.running = True

    async def run_test(self, duration: int = 30):
        """
        Run capture test

        Args:
            duration: Test duration in seconds (0 = run until Ctrl+C)
        """
        print("=" * 70)
        print("PHASE 4 - PACKET CAPTURE & FEATURE EXTRACTION TEST")
        print("=" * 70)
        print()

        # Start monitoring
        print("[1] Starting packet capture...")
        success = await self.service.start_monitoring()

        if not success:
            print(f"❌ Failed to start monitoring: {self.service.sniffer.error_message}")
            print("\nTroubleshooting:")
            print("  1. Run as Administrator")
            print("  2. Check interface name in app/capture/config.py")
            print("  3. Ensure Scapy is installed: pip install scapy")
            return

        print("✅ Packet capture started successfully!")
        print()
        print("[2] Waiting for network flows...")
        print(
            f"    - Interface: {self.service.sniffer.sniffer_status['interface'] if hasattr(self.service.sniffer, 'sniffer_status') else 'Ethernet'}")
        print(f"    - Flow timeout: 5 seconds")
        print(f"    - Features to extract: {N_FEATURES}")
        print()
        print("💡 Generate some traffic:")
        print("   - Open browser and visit websites")
        print("   - Run: ping google.com")
        print("   - Run: ping localhost")
        print()
        print("Press Ctrl+C to stop...")
        print("-" * 70)
        print()

        # Setup signal handler for Ctrl+C
        def signal_handler(sig, frame):
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)

        # Monitor flows
        start_time = asyncio.get_event_loop().time()

        try:
            while self.running:
                # Get next flow features (with timeout)
                flow_info = await self.service.get_next_features(timeout=1.0)

                if flow_info:
                    self.flows_received += 1
                    self._print_flow_info(flow_info)

                # Check duration
                if duration > 0:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed >= duration:
                        print(f"\n⏱️  Test duration {duration}s reached")
                        break

                # Show periodic stats
                if self.flows_received > 0 and self.flows_received % 5 == 0:
                    self._print_statistics()

        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")

        # Stop monitoring
        print("\n[3] Stopping packet capture...")
        final_stats = await self.service.stop_monitoring()

        # Print final results
        print()
        print("=" * 70)
        print("TEST RESULTS")
        print("=" * 70)
        self._print_final_results(final_stats)

    def _print_flow_info(self, flow_info: dict):
        """Print flow information and features"""
        print(f"📦 Flow #{self.flows_received}: {flow_info['flow_id']}")
        print(f"   └─ {flow_info['src_ip']}:{flow_info['src_port']} → "
              f"{flow_info['dst_ip']}:{flow_info['dst_port']} ({flow_info['protocol']})")
        print(f"   └─ Duration: {flow_info['duration']:.3f}s | "
              f"Packets: {flow_info['total_packets']} "
              f"(Fwd: {flow_info['fwd_packets']}, Bwd: {flow_info['bwd_packets']})")

        if flow_info['features']:
            features = flow_info['features']

            # Verify feature count
            if len(features) == N_FEATURES:
                print(f"   └─ ✅ Features extracted: {len(features)}/{N_FEATURES}")
            else:
                print(f"   └─ ⚠️  Features extracted: {len(features)}/{N_FEATURES} (MISMATCH!)")

            # Show sample features
            print(f"   └─ Sample features:")
            sample_features = [
                ' Flow Duration',
                ' Total Fwd Packets',
                ' Destination Port',
                ' Packet Length Mean',
                'Flow Bytes/s'
            ]

            for feature_name in sample_features:
                if feature_name in features:
                    value = features[feature_name]
                    print(f"      • {feature_name}: {value:.2f}")
        else:
            print(f"   └─ ❌ No features extracted")

        print()

    def _print_statistics(self):
        """Print current statistics"""
        stats = self.service.get_statistics()
        print("-" * 70)
        print(f"📊 Statistics:")
        print(f"   • Packets captured: {stats['packets_captured']}")
        print(f"   • Active flows: {stats['active_flows']}")
        print(f"   • Flows processed: {stats['flows_processed']}")
        print(f"   • Features extracted: {stats['features_extracted']}")
        print(f"   • Queue size: {stats['queue_size']}")
        print("-" * 70)
        print()

    def _print_final_results(self, stats: dict):
        """Print final test results"""
        print(f"Total Packets Captured:  {stats['packets_captured']}")
        print(f"Total Flows Created:     {stats['total_flows_created']}")
        print(f"Total Flows Expired:     {stats['total_flows_expired']}")
        print(f"Features Extracted:      {stats['features_extracted']}")
        print(f"Flows Received in Test:  {self.flows_received}")
        print()

        # Verify results
        print("=" * 70)
        print("VERIFICATION")
        print("=" * 70)

        success = True

        if stats['packets_captured'] == 0:
            print("❌ No packets captured - check network interface")
            success = False
        else:
            print(f"✅ Packets captured: {stats['packets_captured']}")

        if stats['features_extracted'] == 0:
            print("⚠️  No features extracted - flows might not have expired yet")
            print("   (flows expire after 5 seconds of inactivity)")
        else:
            print(f"✅ Features extracted from {stats['features_extracted']} flows")

        if self.flows_received == 0:
            print("⚠️  No flows received in test - try generating more traffic")
        else:
            print(f"✅ Received {self.flows_received} flows with features")

        print()
        if success and self.flows_received > 0:
            print("🎉 Phase 4 test PASSED!")
            print("✅ Packet capture working")
            print("✅ Flow management working")
            print("✅ Feature extraction working")
        elif success:
            print("⚠️  Phase 4 components working, but need more traffic for full test")
            print("💡 Try: ping google.com -n 20")
        else:
            print("❌ Phase 4 test FAILED - check errors above")

        print("=" * 70)


async def main():
    """Main test function"""
    # Parse arguments
    duration = 30  # Default 30 seconds

    if len(sys.argv) > 1:
        try:
            duration = int(sys.argv[1])
        except ValueError:
            print(f"Invalid duration: {sys.argv[1]}")
            print("Usage: python test_capture.py [duration_in_seconds]")
            print("       python test_capture.py 0  # Run until Ctrl+C")
            return

    # Run test
    test = CaptureTest()
    await test.run_test(duration=duration)


if __name__ == "__main__":
    print()
    print("🧪 Starting Phase 4 Test...")
    print()

    # Check if running as admin (Windows)
    try:
        import ctypes

        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        if not is_admin:
            print("⚠️  WARNING: Not running as Administrator")
            print("   Packet capture may fail without admin privileges")
            print("   Run as Administrator for best results")
            print()
    except:
        pass

    # Run asyncio event loop
    asyncio.run(main())