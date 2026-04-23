# Network Testbed Application

A visual network testbed for researchers to simulate healthcare network topologies, generate realistic background traffic, and observe the effects of network attacks using D-ITG and Scapy-based attack scripts.

---

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Using the GUI](#using-the-gui)
- [Developer Guide](#developer-guide)

---

## Overview

This application provides a graphical interface for loading and visualizing Mininet network topologies, configuring and launching attack simulations, and generating background traffic using D-ITG. It is designed around two healthcare network scenarios:

- **Rural to Hospital** — models a low-bandwidth rural clinic connecting over WAN to an urban hospital
- **Urban Hospital** — models a multi-segment hospital LAN connecting to a remote clinic over dual WAN paths

Supported attacks:
- TCP SYN Flood
- ARP Spoofing (man-in-the-middle)

---

## Installation

### Prerequisites

- Ubuntu 20.04 or 22.04 (recommended)
- Must be run on a machine or VM with Mininet support

VM Minimum Specs:
 - 2 cores
 - 4GB RAM
 - 20GB disk space

### Automated Setup

A setup script is provided that installs all dependencies:

```bash
chmod +x setup.sh
./setup.sh
```

This installs:
- Python 3 and pip
- Mininet (from source)
- D-ITG (traffic generator)
- hping3 and dsniff (required for attack scripts)
- PyQt5 5.15.6
- Qt xcb display dependencies

## Running the Application

From the project root:

```bash
sudo python3 main.py
```

> **Note:** Mininet requires root privileges. The application will launch a separate `gnome-terminal` running the topology as `sudo` when a simulation is started.

---

## Using the GUI

### Loading a Topology

1. Click **Load Topology** in the properties panel on the right
2. Select a JSON file from the `topo_jsons/` directory
3. The topology will render in the main view — scroll to zoom, click and drag to pan

### Inspecting Nodes and Links

Click any node or link in the topology view to see its properties in the right panel. Link parameters (bandwidth, delay, jitter, loss) can be edited and applied before launching.

### Launching a Simulation

1. Click **Open Attack GUI**
2. Configure the attack:
   - **Attack Script** — browse to a script in `attacks/`
   - **Attacker** — select the host that will run the attack
   - **Target** — for ARP spoofing, select a non-server host to intercept; for flood attacks, this is automatically set to the receiver
   - **Protocol, Packet Size, Rate** — D-ITG traffic parameters
   - **Baseline (sec)** — how long normal traffic runs before the attack starts
   - **Attack Duration (sec)** — how long the attack runs
   - **Runs** — number of simulation repetitions
3. Click **Launch Simulation** — a terminal window opens running the Mininet topology
4. Note: the first time launch will take longer than expected. Each launch after is almost immediate

### Viewing Results

Decoded D-ITG logs are saved to:

```
trafficGenerator/trafficLogs/<timestamp>/
```

Each run produces:
- `recv_<server>.txt` — receiver-side statistics
- `send_<host>.txt` — per-sender statistics

### Traffic GUI

Click **Open Traffic GUI** to open a standalone D-ITG test window. Select a topology, choose a destination host (receiver), configure traffic parameters, and click **Run D-ITG Test** to send traffic from all other hosts simultaneously.

---

## Developer Guide

### Project Structure

```
main.py                          # Entry point
setup.sh                         # Dependency installer
attackGUIConfigs.json            # Default values for attack dialog fields

GUIElements/
    main_window.py               # MainWindow — top-level application window
    topoProperties.py            # TopoWindow (canvas) and Properties (side panel)
    node.py                      # Node — graphical host/switch/router element
    link.py                      # Link — graphical connection between nodes
    attackGUI.py                 # AttackDialog — attack configuration dialog
    trafficGUI.py                # D-ITG standalone traffic test window

trafficGenerator/
    trafficGenerator.py          # TrafficGenerator — D-ITG orchestration and log decoding

topos/
    rural_urban.py               # Rural-to-hospital Mininet topology
    urban_urban.py               # Urban hospital-to-clinic Mininet topology

ditg_topos/
    rural_urban.py               # Alternate topology variants (used by Traffic GUI)
    urban_urban.py

topo_jsons/
    rural_urban.json             # Topology definitions loaded by the GUI
    urban_urban.json

attacks/
    tcp_syn_flood.py             # TCP SYN flood attack script
    one_way_arp_spoof.py         # ARP spoofing (MITM) attack script

assets/
    host.png
    switch.png
    router.png
```

### Architecture Overview

The GUI (`main.py` → `MainWindow`) loads a topology JSON and renders it using `Node` and `Link` objects on a `QGraphicsScene`. When a simulation is launched, `MainWindow.run_topo()` writes the attack config to `/tmp/attack_config.json` and spawns a `gnome-terminal` running the selected topology script as `sudo`.

The topology script (`topos/*.py`) starts Mininet, configures routing, and calls `trafficGenerator.start()`. The `TrafficGenerator` reads `/tmp/attack_config.json`, starts `ITGRecv` on the server, launches `ITGSend` on all non-attacker hosts, runs the attack script on the attacker, and decodes logs after completion.

### Adding a New Topology

1. Create a Mininet script in `topos/` following the pattern in `rural_urban.py`
2. Create a matching JSON file in `topo_jsons/` with `nodes`, `links`, and a `ditg_server` field
3. Add the topology entry to the `TOPOLOGIES` dict in `GUIElements/trafficGUI.py` if you want it available in the Traffic GUI

### Adding a New Attack Script

1. Create a Python script in `attacks/` that accepts `--target-ip`, `--receiver-ip`, and `--duration` arguments
2. To automatically determine the attack type in the GUI, include a generic attack identifier in the name of the script. `AttackDialog` within `attackGUI.py` uses the filename to determine whether to lock the target to the receiver or allow host selection. Make changes to `AttackDialog` if you want to include different attack types:
   - For ARP spoofing attacks, include `arp` in the filename (e.g., `arp_spoof.py`)
   - For flood attacks, include `flood` in the filename (e.g., `tcp_syn_flood.py`)
