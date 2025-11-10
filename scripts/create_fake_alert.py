"""
Create fake alert for WebSocket testing
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from datetime import datetime
from app.detection.websocket_manager import get_connection_manager


async def send_fake_alert():
    """Send a fake alert through WebSocket"""
    connection_manager = get_connection_manager()

    # Fake alert data
    alert = {
        "id": 999,
        "timestamp": datetime.now().isoformat(),
        "source_ip": "192.168.1.100",
        "dest_ip": "10.0.0.1",
        "attack_type": "DDoS",
        "confidence": 0.98,
        "severity": "critical"
    }

    print(f"Sending fake alert: {alert}")

    # Push to WebSocket queue
    await connection_manager.push_alert_to_queue(alert)

    print("✅ Fake alert sent!")


if __name__ == "__main__":
    asyncio.run(send_fake_alert())