# -*- coding: utf-8 -*-
import re
import time
import subprocess
import threading

from flask import Flask, render_template, jsonify, request
import geoip2.database

app = Flask(__name__)

# Path to your GeoLite2-City database. Make sure you place it in /etc/geoip or adjust the path.
reader = geoip2.database.Reader('/etc/geoip/GeoLite2-City.mmdb')

# Global dictionary storing active connections. 
# Key: destination IP (dst_ip). Value: source IP (src_ip).
active_connections = {}

def monitor_connections():
    """
    Background thread function. Every 5 seconds, it runs tcpdump -i any -nn -c 100,
    parses the output, and stores IP pairs in active_connections.
    This is a simplified approach. 
    """
    global active_connections
    while True:
        # Capture up to 100 packets (no filter).
        cmd = "sudo tcpdump -i any -nn -c 100 2>/dev/null"
        output = subprocess.getoutput(cmd)

        # Temporary dictionary for new packets.
        new_connections = {}

        for line in output.splitlines():
            # Find the first two IPv4 addresses in each line.
            ips = re.findall(r'\d+\.\d+\.\d+\.\d+', line)
            if len(ips) >= 2:
                src_ip = ips[0]
                dst_ip = ips[1]
                new_connections[dst_ip] = src_ip

        # Overwrite the global dictionary with the latest set of connections.
        # If you want to keep older entries for longer, you can merge them instead.
        active_connections = new_connections

        # Sleep 5 seconds before the next capture.
        time.sleep(5)

@app.route('/')
def index():
    """ Serve the main map interface. """
    return render_template('map.html')

@app.route('/connections')
def get_connections():
    """
    Returns the current set of connections in JSON, along with geolocation
    if available in the GeoLite2-City database.
    """
    features = []
    for dst_ip, src_ip in active_connections.items():
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
            # If the IP is private or not in the database, skip it.
            continue

    return jsonify({'connections': features})

@app.route('/block', methods=['POST'])
def block_ip():
    """
    Blocks traffic to the specified IP by inserting a DROP rule in the FORWARD chain.
    """
    data = request.json
    if not data or 'ip' not in data:
        return jsonify({'status': 'error', 'message': 'No IP provided'}), 400

    ip = data['ip']
    # Insert a DROP rule for the destination IP in the FORWARD chain.
    subprocess.run(['sudo', 'iptables', '-I', 'FORWARD', '-d', ip, '-j', 'DROP'])

    return jsonify({'status': 'blocked', 'ip': ip})

if __name__ == '__main__':
    # Start the background thread that monitors connections via tcpdump.
    monitor_thread = threading.Thread(target=monitor_connections, daemon=True)
    monitor_thread.start()

    # Run the Flask app on port 5000.
    app.run(host='0.0.0.0', port=5000, debug=False)
