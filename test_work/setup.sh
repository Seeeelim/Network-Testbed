#!/bin/bash
 
echo "*** Updating package list ***"
sleep 1
sudo apt-get update
 
echo "*** Installing system dependencies ***"
sleep 1
sudo apt-get install -y python3-pip
sudo apt-get install -y git

echo "*** Installing D-ITG and hping3 ***"
sleep 1
sudo apt-get install -y d-itg
sudo apt-get install -y hping3
sudo apt-get install -y dsniff
 
echo "*** Installing Qt xcb dependencies ***"
sleep 1
sudo apt-get install -y libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-xkb1 libxkbcommon-x11-0
 
echo "*** Installing Mininet from source ***"
sleep 1
git clone https://github.com/mininet/mininet
cd mininet
sudo ./util/install.sh -a
sudo python3 setup.py install
 
echo "*** Installing Python dependencies ***"
sleep 1
sudo pip3 install PyQt5==5.15.6
 
echo "*** Setup complete ***"