# Server Rack E-Ink Display
This repository is a program for displaying stats for multiple Raspberry Pis on an E-Ink display. 

## Overview
The program takes a list of hosts/IP addresses, SSHs into them, grabs a few stats, and then displays it on the E-Ink display.
![image3-1](https://github.com/user-attachments/assets/4410230b-073f-4152-b040-63249349984d)


I have a mini rack with 3 Pi 5s, one Pi 3, 4 Pi Zero 2 Ws, and 1 Pi Zero W. The E-Ink display is wired into one of Pi Zero 2 Ws.
![image1-1](https://github.com/user-attachments/assets/9923833e-7cda-4030-9661-2f5db71e9e79)

The mounting of the E-Ink display is temporary, I need to 3D print a proper mount for it.

## Resources
- Code for operating the E-Ink Display: https://github.com/waveshareteam/e-Paper
- The E-Ink display I'm using: https://www.microcenter.com/product/632694/inland-213-inch-e-ink-lcd-display-screen
- A useful tutorial: https://medium.com/swlh/create-an-e-paper-display-for-your-raspberry-pi-with-python-2b0de7c8820c

## Pin Mapping
Raspberry Pi Pin Layout: https://pinout.xyz/

E-Ink Display:
![IMG_5635-1](https://github.com/user-attachments/assets/6771397b-6113-4fb6-b80b-e2f6a4fb8b96)

Mapping:
DISPLAY - PI Pin (#)
- VCC - 3.3V (17)
- GND - Ground (20)
- SDI - GPIO 10 (19)
- SCLK - GPIO 11 (23)
- CS - GPIO 8 (24)
- D/C - GPIO 25 (22)
- RES - GPIO 17 (11)
- BUSY - GPIO 24 (18)

## Setup
This program can be run on docker, or directly on the host machine. 

The program uses files in the .data directory. There are two files expected:
- [.data/config.yaml](.data/config.yaml.example) - The main configuration file for the project.
- [.data/extra_hosts.yaml](.data/extra_hosts.yaml.example) - If using docker, the host/ip mapping for the hosts to connect to.
  - This is required because even with host networking, docker will not be able to find the machines by hostname without the IP addresses mapped.

The config.yaml file has the following fields:
- line_count: The number of lines to use for text on the E-Ink display
- font_size: (Optional) The font size to use
- font_file: (Optional) Path to a font file to use for displaying text
- display_title: The title to display on the first line
- display_time: The time to display each page on for
- ssh_key: Path to an ssh key to use for accessing the machines
- servers: The list of machines to display stats for
  - host: The host name
  - user: The ssh username

The extra_hosts.yml file should be in the format of the example file, with the hosts listed in the extra_hosts array with the format "{hostname}:{ip address}".

To SSH into the machines and grab the data, provide an SSH private key file, and make sure that the public key has been added to the authorized keys file on each of the machines. You can generate a new pair with the following command:
```
ssh-keygen -t rsa
```

And then add the public key to the machines with the following command:
```
cat ~{path to public key file} | ssh {target machine user}@{target machine host} "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

Once everything is set up, you can run the project locally with:
```
python display.py
```

Or on docker with:
```
docker compose up --build
```

## Note
Currently, this is only set up for grabbing data from Raspberry Pis. The commands used are Raspberry Pi specific. However, the program could easily be modified to work on other systems by adding and using the appropriate commands.
