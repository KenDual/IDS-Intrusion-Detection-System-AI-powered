"""
Test WebSocket connection to IDS API
Connects to /ws/alerts and listens for real-time alerts
"""
import asyncio
import websockets
import json
from datetime import datetime

WS_URL = "ws://localhost:8000/ws/alerts"


async def test_websocket():
    """Connect to WebSocket and listen for alerts"""
    print("=" * 60)
    print("WebSocket Alert Listener Test")
    print("=" * 60)
    print(f"Connecting to {WS_URL}...")

    try:
        async with websockets.connect(WS_URL) as websocket:
            print("✅ Connected successfully!")
            print("Listening for alerts... (Press Ctrl+C to stop)")
            print("-" * 60)

            # Listen for messages
            alert_count = 0
            while True:
                try:
                    # Receive message from server
                    message = await websocket.recv()

                    # Parse JSON
                    alert = json.loads(message)
                    alert_count += 1

                    # Display alert
                    print(f"\n🚨 ALERT #{alert_count}")
                    print(f"  Time: {alert.get('timestamp', 'N/A')}")
                    print(f"  Type: {alert.get('attack_type', 'Unknown')}")
                    print(f"  Source: {alert.get('source_ip', 'N/A')}")
                    print(f"  Destination: {alert.get('dest_ip', 'N/A')}")
                    print(f"  Confidence: {alert.get('confidence', 0):.2%}")
                    print(f"  Severity: {alert.get('severity', 'N/A').upper()}")
                    print("-" * 60)

                except websockets.exceptions.ConnectionClosed:
                    print("\n⚠️  Connection closed by server")
                    break
                except json.JSONDecodeError as e:
                    print(f"\n❌ Failed to parse message: {e}")
                except KeyboardInterrupt:
                    print("\n\n👋 Stopping listener...")
                    break

    except ConnectionRefusedError:
        print("❌ Connection refused. Is the server running?")
    except Exception as e:
        print(f"❌ Connection error: {e}")

    print("\n✅ Test completed")


if __name__ == "__main__":
    try:
        asyncio.run(test_websocket())
    except KeyboardInterrupt:
        print("\n\n👋 Bye!")