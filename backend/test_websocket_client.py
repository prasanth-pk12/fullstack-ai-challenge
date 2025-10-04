#!/usr/bin/env python3
"""
Simple WebSocket test client to debug the connection issues
"""
import asyncio
import websockets
import json
from datetime import datetime

# JWT token from the error message
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwcmFzYW50aCIsInVzZXJfaWQiOjEsInJvbGUiOiJhZG1pbiIsImV4cCI6MTc1OTU4MDczN30.1Vs1Gs56GbRTPCvBEyuyAiQpCjrufa73GU9fg8TI7Ik"

async def test_websocket():
    uri = f"ws://localhost:8000/ws/tasks?token={TOKEN}"
    
    try:
        print(f"Connecting to: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
            
            # Wait for welcome message
            try:
                welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📨 Received welcome: {welcome_msg}")
                
                # Send a ping
                ping_msg = json.dumps({"type": "ping", "timestamp": datetime.utcnow().isoformat()})
                await websocket.send(ping_msg)
                print(f"📤 Sent ping: {ping_msg}")
                
                # Wait for pong
                pong_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📨 Received pong: {pong_msg}")
                
                # Keep connection alive for a few seconds
                print("⏳ Keeping connection alive for 10 seconds...")
                await asyncio.sleep(10)
                
            except asyncio.TimeoutError:
                print("⏰ Timeout waiting for message")
            
            print("👋 Closing connection")
            
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"❌ Connection closed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())