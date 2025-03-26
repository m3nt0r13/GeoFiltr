# -*- coding: utf-8 -*-
import re
import time
import subprocess
import threading

from flask import Flask, render_template, jsonify, request
import geoip2.database

app = Flask(__name__)

# Path to your GeoLite2-City database
reader = geoip2.database.Reader('/etc/geoip/GeoLite2-City.mmdb')

# Global dictionary to store active connections, each with a last_seen timestamp.
# Key: destination IP, Value: {'src_ip': ..., 'last_seen': ...}
active_connections = {}

# Default expiration time in seconds
EXPIRE_TIME = 60  # For example, 60 seconds

def monitor_connections():
    """
    Background thread function. Every 5 seconds, runs tcpdump -i any -nn -c 100,
    parses the output, updates the global dictionary with a last_seen timestamp,
    and removes entries older than EXPIRE_TIME.
    """
    global active_connections
    while True:
        cmd = "sudo tcpdump -i any -nn -c 100 2>/dev/null"
        output = subprocess.getoutput(cmd)

        now = time.time()
        new_entries = {}

        # Parse up to 100 lines from tcpdump
        for line in output.splitlines():
            ips = re.findall(r'\d+\.\d+\.\d+\.\d+', line)
            if len(ips) >= 2:
                src_ip = ips[0]
                dst_ip = ips[1]
                new_entries[dst_ip] = src_ip

        # Update the global dictionary, setting 'last_seen' for each IP
        for dst_ip, src_ip in new_entries.items():
            active_connections[dst_ip] = {
                'src_ip': src_ip,
                'last_seen': now
            }

        # Remove entries older than EXPIRE_TIME
        for ip_key in list(active_connections.keys()):
            if now - active_connections[ip_key]['last_seen'] > EXPIRE_TIME:
                del active_connections[ip_key]

        time.sleep(5)

@app.route('/')
def index():
    """Serve the main map interface (HTML) - adjust as needed."""
    return render_template('map.html')

@app.route('/connections')
def get_connections():
    """
    Returns a JSON list of active connections with geolocation,
    skipping those that are expired or not in the GeoIP database.
    """
    features = []
    for dst_ip, info in active_connections.items():
        src_ip = info['src_ip']
        try:
            resp = reader.city(dst_ip)
            lat = resp.location.latitude
            lon = resp.location.longitude
            city = resp.city.name if resp.city.name else 'Unknown'
            features.append({
                'src_ip': src_ip,
                'dst_ip': dst_ip,
                'city': city,
                'lat': lat,
                'lon': lon
            })
        except:
            # If IP not in database or private range, skip it
            continue

    return jsonify({'connections': features})

@app.route('/block', methods=['POST'])
def block_ip():
    """Blocks traffic to the specified IP by inserting a DROP rule in the FORWARD chain."""
    data = request.json
    if not data or 'ip' not in data:
        return jsonify({'status': 'error', 'message': 'No IP provided'}), 400

    ip = data['ip']
    subprocess.run(['sudo', 'iptables', '-I', 'FORWARD', '-d', ip, '-j', 'DROP'])
    return jsonify({'status': 'blocked', 'ip': ip})

@app.route('/expire_time/<int:seconds>', methods=['GET'])
def set_expire_time(seconds):
    """
    Allows changing the expiration time (in seconds) via a GET request.
    Example: http://<YOUR_PI_IP>:5000/expire_time/120
    """
    global EXPIRE_TIME
    EXPIRE_TIME = seconds
    return f"EXPIRE_TIME set to {seconds} seconds."

if __name__ == '__main__':
    # Start the background thread to monitor connections
    monitor_thread = threading.Thread(target=monitor_connections, daemon=True)
    monitor_thread.start()

    # Run the Flask app on port 5000
    app.run(host='0.0.0.0', port=5000, debug=False)
