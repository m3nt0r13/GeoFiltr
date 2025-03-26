Usage


Install Dependencies

sudo apt update && sudo apt install -y python3 python3-pip tcpdump iptables

sudo python3 -m pip install flask requests geoip2

Configure GeoLite2

Place GeoLite2-City.mmdb in /etc/geoip/ (or adjust the path in app.py).

Enable Passwordless sudo for tcpdump and iptables (example):

bash

echo "pi ALL=(ALL) NOPASSWD: /usr/sbin/tcpdump, /usr/sbin/iptables" | sudo tee /etc/sudoers.d/geofilter


Run the application:

bash

python3 app.py


Open 

http://<YOUR_PI_IP>:5000 in your browser.
