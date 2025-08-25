from epd_text import epd_text
import logging
import yaml
import raspberry_pi_system_information_commands as RSYSINFO
import subprocess
import time
import socket
import os
from PIL import ImageFont

def get_shell_return(command, ssh=False, ssh_user=None, ssh_host=None, ssh_key=None):
    if ssh:
        command = f'ssh -o StrictHostKeyChecking=no -i {ssh_key} {ssh_user}@{ssh_host} {command}'

    logging.info(f'Running shell command: {command}')
    result = subprocess.check_output(command, shell=True).decode().strip()
    logging.debug(f'Shell command return: {result}')
    return result

def display_server_details(display, host, user, index=None):
    logging.info(f'Generating display for host: {host}')

    if host == socket.gethostname():
        ssh = False
        user = None
        ssh_ip = None
        ssh_key = None
    else:
        ssh = True
        ssh_ip = socket.gethostbyname(f'{host}.local')
        logging.info(f'IP for host {host}: {ssh_ip}')

        #get path to key file from relative path
        ssh_key = os.path.join(os.path.dirname(os.path.realpath(__file__)), CONFIG['ssh_key'])
        logging.info(f'SSH Key File: {ssh_key}')

    display.new_image()

    current_line = -1

    #first the display title
    display.set_line_text(current_line := current_line+1, CONFIG['display_title'], center=True, font=FONT)
    #also display the counter
    if index is not None:
        display.set_line_text(current_line, f'{index + 1} / {SERVER_COUNT}', right_justify=True, font=FONT)

    # #now the host name
    value = get_shell_return(RSYSINFO.HOSTNAME, ssh=ssh, ssh_user=user, ssh_host=ssh_ip, ssh_key=ssh_key)
    value2 = get_shell_return(RSYSINFO.IP_ADDRESS, ssh=ssh, ssh_user=user, ssh_host=ssh_ip, ssh_key=ssh_key)
    display.set_line_text(current_line := current_line+1, f'Host: {value}  -  {value2}', font=FONT)

    #system / model
    value = get_shell_return(RSYSINFO.MODEL, ssh=ssh, ssh_user=user, ssh_host=ssh_ip, ssh_key=ssh_key)
    display.set_line_text(current_line := current_line+1, f'System: {value}', font=FONT)

    #operating system
    value = get_shell_return(RSYSINFO.OPERATING_SYSTEM, ssh=ssh, ssh_user=user, ssh_host=ssh_ip, ssh_key=ssh_key)
    display.set_line_text(current_line := current_line+1, f'OS: {value}', font=FONT)

    #cpu
    value = get_shell_return(RSYSINFO.CPU_MODEL, ssh=ssh, ssh_user=user, ssh_host=ssh_ip, ssh_key=ssh_key)
    value2 = get_shell_return(RSYSINFO.ARCHITECTURE, ssh=ssh, ssh_user=user, ssh_host=ssh_ip, ssh_key=ssh_key)
    value3 = get_shell_return(RSYSINFO.CPU_LOAD, ssh=ssh, ssh_user=user, ssh_host=ssh_ip, ssh_key=ssh_key)
    value4 = get_shell_return(RSYSINFO.CPU_TEMPERATURE, ssh=ssh, ssh_user=user, ssh_host=ssh_ip, ssh_key=ssh_key)
    value4 = round(int(value4) / 1000)
    display.set_line_text(current_line := current_line+1, f'CPU: {value} ({value2}),  {value3}%,  {value4}°C', font=FONT)

    #total memory
    value = get_shell_return(RSYSINFO.MEMORY, ssh=ssh, ssh_user=user, ssh_host=ssh_ip, ssh_key=ssh_key)
    value2 = get_shell_return(RSYSINFO.USED_MEMORY_PERCENTAGE, ssh=ssh, ssh_user=user, ssh_host=ssh_ip, ssh_key=ssh_key)
    value2 = round(float(value2))
    display.set_line_text(current_line := current_line+1, f'Memory: {value}MB,  {value2}%', font=FONT)

    #now update
    display.draw()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.info('Process starting...')

    #load config file
    logging.debug('Loading config.yaml...')
    CONFIG = yaml.safe_load(open('config.yaml'))

    SERVER_COUNT = len(CONFIG['servers'])
    SERVERS = CONFIG['servers']
    logging.debug(f'Server Count: {SERVER_COUNT}')
    logging.debug(f'Servers: {SERVERS}')
    logging.debug('Servers: ' + str(CONFIG['display_time']))
    logging.debug('Servers: ' + CONFIG['display_title'])

    #load font
    if CONFIG.get('font_file'):
        font_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), CONFIG['font_file'])
        logging.debug(f"Loading font file [{font_file}]")
        FONT = ImageFont.truetype(font_file, CONFIG['font_size'])
    else:
        FONT = None

    #initialize display
    display = epd_text(CONFIG['line_count'], margin_x=1, margin_y=1)

    #process loop
    while True:
        logging.info('Starting process loop...')

        for i in range(SERVER_COUNT):
            display_server_details(display, SERVERS[i]['host'], SERVERS[i]['user'], index=i)

            logging.info('Wating - ' + str(CONFIG['display_time']) + 's')
            time.sleep(CONFIG['display_time'])