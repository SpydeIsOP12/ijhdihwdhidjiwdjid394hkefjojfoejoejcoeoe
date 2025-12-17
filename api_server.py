#!/usr/bin/env python3
"""
Flask API Server for Stripe Checkout Auto Hitter
Endpoints:
  - POST /grab_details: Extract PK, SK, CS, amount, product, email from checkout URL
  - POST /check: Check a card using pre-captured checkout data
  - GET /health: Health check
"""

from flask import Flask, request, jsonify
import subprocess
import json
import tempfile
import os
import sys

app = Flask(__name__)

# Path to test.py and Python executable
PYTHON_EXE = sys.executable  # Use same Python running this server
TEST_PY_PATH = os.path.join(os.path.dirname(__file__), 'test.py')

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'stripe-checkout-api'}), 200


@app.route('/grab_details', methods=['POST'])
def grab_details():
    """
    Extract PK, SK, CS, amount, product, email from checkout URL
    
    Request JSON:
    {
        "checkout_url": "https://checkout.stripe.com/...",
        "proxy": "http://user:pass@host:port"  // optional
    }
    
    Response JSON:
    {
        "pk_key": "pk_live_...",
        "sk_key": "sk_live_...",  // may be null
        "cs_token": "cs_live_...",
        "amount": "$30.00",
        "product": "SuperGrok",
        "email": "test@example.com"
    }
    """
    print("\n" + "="*60)
    print("[GRAB DETAILS] New request received")
    print("="*60)
    
    try:
        data = request.get_json()
        print(f"[GRAB DETAILS] Request data: {data}")
        
        checkout_url = data.get('checkout_url')
        proxy = data.get('proxy', '')
        
        print(f"[GRAB DETAILS] Checkout URL: {checkout_url}")
        print(f"[GRAB DETAILS] Proxy: {proxy if proxy else 'None'}")
        
        if not checkout_url:
            print("[GRAB DETAILS] ERROR: checkout_url is required")
            return jsonify({'error': 'checkout_url is required'}), 400
        
        # Create temp file for proxy if provided
        proxy_file = None
        if proxy:
            print(f"[GRAB DETAILS] Creating proxy temp file...")
            proxy_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
            proxy_file.write(proxy)
            proxy_file.close()
            print(f"[GRAB DETAILS] Proxy file: {proxy_file.name}")
        
        try:
            # Execute test.py in GRAB mode (new mode we'll add)
            # We'll modify test.py to accept --grab-details flag
            cmd = [PYTHON_EXE, TEST_PY_PATH, '--grab-details', checkout_url]
            
            if proxy_file:
                cmd.append(proxy_file.name)
            
            print(f"[GRAB DETAILS] Executing command: {' '.join(cmd)}")
            print(f"[GRAB DETAILS] Starting test.py execution...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            print(f"[GRAB DETAILS] test.py completed with return code: {result.returncode}")
            
            # Parse output - looking for JSON on last line
            output = result.stdout.strip()
            print(f"[GRAB DETAILS] STDOUT ({len(output)} chars):")
            print(output[:500] if len(output) > 500 else output)
            
            if result.stderr:
                print(f"[GRAB DETAILS] STDERR:")
                print(result.stderr[:500])
            
            # Look for JSON output (we'll make test.py output JSON in grab mode)
            try:
                # Try to find JSON in output
                lines = output.split('\n')
                for line in reversed(lines):
                    if line.strip().startswith('{'):
                        print(f"[GRAB DETAILS] Found JSON line: {line.strip()[:100]}...")
                        response_data = json.loads(line.strip())
                        print(f"[GRAB DETAILS] Parsed JSON successfully")
                        print(f"[GRAB DETAILS] Response: {response_data}")
                        return jsonify(response_data), 200
            except Exception as e:
                print(f"[GRAB DETAILS] JSON parse error: {str(e)}")
            
            # If no JSON found, return error
            print(f"[GRAB DETAILS] ERROR: No JSON found in output")
            return jsonify({
                'error': 'Failed to grab details',
                'output': output[:500]
            }), 500
            
        finally:
            # Clean up proxy file
            if proxy_file and os.path.exists(proxy_file.name):
                os.unlink(proxy_file.name)
                print(f"[GRAB DETAILS] Cleaned up proxy file")
        
    except Exception as e:
        print(f"[GRAB DETAILS] EXCEPTION: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/check', methods=['POST'])
def check_card():
    """
    Check a card using pre-captured checkout data
    
    Request JSON:
    {
        "card": "4111111111111111|01|2028|123",
        "captured_data": {
            "pk_key": "pk_live_...",
            "sk_key": "sk_live_...",
            "cs_token": "cs_live_...",
            "amount": "$30.00",
            "product": "SuperGrok",
            "email": "test@example.com"
        },
        "proxy": "http://user:pass@host:port"  // optional
    }
    
    Response JSON:
    {
        "status": "CHARGED|LIVE|DEAD",
        "message": "Payment Successful",
        "bin_info": "VISA CREDIT"
    }
    """
    print("\n" + "="*60)
    print("[CHECK CARD] New request received")
    print("="*60)
    
    try:
        data = request.get_json()
        card = data.get('card')
        captured_data = data.get('captured_data', {})
        proxy = data.get('proxy', '')
        
        print(f"[CHECK CARD] Card: {card[:19] if card else 'None'}...")
        print(f"[CHECK CARD] Captured data keys: {list(captured_data.keys())}")
        print(f"[CHECK CARD] Proxy: {proxy if proxy else 'None'}")
        
        if not card:
            print("[CHECK CARD] ERROR: card is required")
            return jsonify({'error': 'card is required'}), 400
        
        if not captured_data.get('pk_key') or not captured_data.get('cs_token'):
            print("[CHECK CARD] ERROR: pk_key and cs_token required")
            return jsonify({'error': 'captured_data must include pk_key and cs_token'}), 400
        
        # Create temp files for card and proxy
        card_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        card_file.write(card)
        card_file.close()
        
        proxy_file = None
        if proxy:
            proxy_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
            proxy_file.write(proxy)
            proxy_file.close()
        
        # Create temp file for captured data
        captured_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        json.dump(captured_data, captured_file)
        captured_file.close()
        
        try:
            # Execute test.py in CHECK mode (new mode we'll add)
            cmd = [PYTHON_EXE, TEST_PY_PATH, '--check-card', card_file.name, captured_file.name]
            
            if proxy_file:
                cmd.append(proxy_file.name)
            
            print(f"[CHECK CARD] Executing command: {' '.join(cmd)}")
            print(f"[CHECK CARD] Starting test.py execution...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            print(f"[CHECK CARD] test.py completed with return code: {result.returncode}")
            
            # Parse output - looking for JSON on last line
            output = result.stdout.strip()
            print(f"[CHECK CARD] STDOUT ({len(output)} chars):")
            print(output[:500] if len(output) > 500 else output)
            
            if result.stderr:
                print(f"[CHECK CARD] STDERR:")
                print(result.stderr[:500])
            
            # Look for JSON output
            try:
                lines = output.split('\n')
                for line in reversed(lines):
                    if line.strip().startswith('{'):
                        print(f"[CHECK CARD] Found JSON line: {line.strip()[:100]}...")
                        response_data = json.loads(line.strip())
                        print(f"[CHECK CARD] Parsed JSON successfully")
                        print(f"[CHECK CARD] Response: {response_data}")
                        return jsonify(response_data), 200
            except Exception as e:
                print(f"[CHECK CARD] JSON parse error: {str(e)}")
            
            # If no JSON found, return error
            print(f"[CHECK CARD] ERROR: No JSON found in output")
            return jsonify({
                'error': 'Failed to check card',
                'output': output[:500]
            }), 500
            
        finally:
            # Clean up temp files
            if os.path.exists(card_file.name):
                os.unlink(card_file.name)
            if proxy_file and os.path.exists(proxy_file.name):
                os.unlink(proxy_file.name)
            if os.path.exists(captured_file.name):
                os.unlink(captured_file.name)
            print(f"[CHECK CARD] Cleaned up temp files")
        
    except Exception as e:
        print(f"[CHECK CARD] EXCEPTION: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("Starting Stripe Checkout API Server...")
    print(f"Python: {PYTHON_EXE}")
    print(f"test.py: {TEST_PY_PATH}")
    print("\nEndpoints:")
    print("  POST /grab_details - Extract checkout details")
    print("  POST /check - Check a card")
    print("  GET /health - Health check")
    print("\nListening on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
