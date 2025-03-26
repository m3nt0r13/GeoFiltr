# GeoFiltr

Overview

The GeoFilter script is a Python (Flask) application designed to monitor and block network traffic based on the geolocation of IP addresses. It runs on a Raspberry Pi (or other Linux-based devices), where:

IP Collection

The script launches a mechanism (such as tcpdump or conntrack) to capture network connections to/from hosts.

It stores the (source or destination) IP addresses in a data structure within the Python application.

Geolocation

For each captured IP address, the script uses the geoip2 library (with the MaxMind GeoLite2-City database) to obtain geographic coordinates (country, city, latitude/longitude).

Private IP addresses (e.g., 192.168.x.x) are skipped since they have no entry in the GeoIP database.

Web Interface

A Flask web server listens on port 5000.

The frontend (HTML/JavaScript + Leaflet.js) displays an interactive map, where markers for IP addresses are refreshed every few seconds.

Each marker shows the IP address, city, and a “Block” button.
