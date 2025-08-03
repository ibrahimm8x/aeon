#!/usr/bin/env python3
"""
Debug curl request
"""

import subprocess
import json

def test_curl():
    """Test curl request"""
    cmd = ["curl", "-s", "-w", "%{http_code}", "-X", "POST", "http://localhost:8000/api/v1/users/login", "-H", "Content-Type: application/json", "-d", '{"username":"test_phase2_user","password":"test_phase2_password123"}']
    
    print(f"Running command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    print(f"Return code: {result.returncode}")
    print(f"Stdout: {repr(result.stdout)}")
    print(f"Stderr: {repr(result.stderr)}")
    
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        print(f"Lines: {lines}")
        if len(lines) >= 2:
            status_code = int(lines[-1])
            response_body = '\n'.join(lines[:-1])
            print(f"Status code: {status_code}")
            print(f"Response body: {repr(response_body)}")
            
            try:
                data = json.loads(response_body)
                print(f"Parsed JSON: {data}")
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")

if __name__ == "__main__":
    test_curl() 