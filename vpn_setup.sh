# vpn_setup.sh (Optional - A bash script to help with OpenVPN installation after SSHing into the instance)
#!/bin/bash

# Update the system
sudo apt update
sudo apt upgrade -y

# Install OpenVPN
sudo apt install openvpn -y

# Generate the server configuration files
sudo mkdir -p /etc/openvpn
sudo openvpn --genkey --secret /etc/openvpn/ta.key

# (Optional) Additional configuration steps
# Add your steps here for setting up and starting the OpenVPN server

# Print success message
echo "OpenVPN setup complete. Proceed with generating and using client profiles."
