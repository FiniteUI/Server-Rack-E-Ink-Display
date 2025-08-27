from epd_text import epd_text
import logging
import yaml
import raspberry_pi_system_information_commands as RSYSINFO
import subprocess
import time
import socket
import os
from cache_file import CacheFile
import sys

CONFIG = None
DOCKER = None
SERVER_COUNT = None
SERVERS = None
CACHE = None

def get_shell_return(command, ssh=False, ssh_user=None, ssh_host=None, ssh_key=None):
    if ssh:
        command = f'ssh -o StrictHostKeyChecking=no -i {ssh_key} {ssh_user}@{ssh_host} {command}'

    logging.info(f'Running shell command: {command}')
    result = subprocess.check_output(command, shell=True).decode().strip()
    logging.debug(f'Shell command return: {result}')
    return result

def get_server_details(host, user):
    logging.info(f'Grabbing data for host: {host}')

    details = {'host': host}

    ip = None
    try:
        ip = socket.gethostbyname(host)
    except socket.gaierror as e:
        logging.warning(e)
    
    if ip is None:
        try:
            ip = socket.gethostbyname(f'{host}.local')
        except socket.gaierror as e:
            logging.warning(e)
    
    if ip is None:
        accessible = False
        logging.warning(f'Host {host} inaccessible.')
    else:
        accessible = True
        logging.info(f'IP for host {host}: {ip}')
        details['ip'] = ip

    #if accessible, grab details
    details['accessible'] = accessible
    if accessible:
        #use ssh unless it's local
        if host == socket.gethostname():
            ssh = False
            ssh_key = None
        else:
            ssh = True

            #get path to key file from relative path
            ssh_key = os.path.join(os.path.dirname(os.path.realpath(__file__)), CONFIG['ssh_key'])
            logging.info(f'SSH Key File: {ssh_key}')

        temp = CACHE.getValue(f'{host}-system')
        if temp is None:
            temp = get_shell_return(RSYSINFO.MODEL, ssh=ssh, ssh_user=user, ssh_host=ip, ssh_key=ssh_key)
            CACHE.setValue(f'{host}-system', temp)
        details['system'] = temp

        #operating system
        temp = CACHE.getValue(f'{host}-operating_system')
        if temp is None:
            temp = get_shell_return(RSYSINFO.OPERATING_SYSTEM, ssh=ssh, ssh_user=user, ssh_host=ip, ssh_key=ssh_key)
            CACHE.setValue(f'{host}-operating_system', temp)
        details['operating_system'] = temp

        #cpu
        temp = CACHE.getValue(f'{host}-cpu_model')
        if temp is None:
            temp = get_shell_return(RSYSINFO.CPU_MODEL, ssh=ssh, ssh_user=user, ssh_host=ip, ssh_key=ssh_key)
            CACHE.setValue(f'{host}-cpu_model', temp)
        details['cpu_model'] = temp
        
        #architecture
        temp = CACHE.getValue(f'{host}-architecture')
        if temp is None:
            temp = get_shell_return(RSYSINFO.ARCHITECTURE, ssh=ssh, ssh_user=user, ssh_host=ip, ssh_key=ssh_key)
            CACHE.setValue(f'{host}-architecture', temp)
        details['architecture'] = temp

        temp = get_shell_return(RSYSINFO.CPU_LOAD, ssh=ssh, ssh_user=user, ssh_host=ip, ssh_key=ssh_key)
        details['cpu_load'] = temp

        temp = get_shell_return(RSYSINFO.CPU_TEMPERATURE, ssh=ssh, ssh_user=user, ssh_host=ip, ssh_key=ssh_key)
        temp = round(int(temp) / 1000)
        details['cpu_temp'] = temp

        #total memory
        temp = CACHE.getValue(f'{host}-memory')
        if temp is None:
            temp = get_shell_return(RSYSINFO.MEMORY, ssh=ssh, ssh_user=user, ssh_host=ip, ssh_key=ssh_key)
            CACHE.setValue(f'{host}-memory', temp)
        details['memory'] = temp

        temp = get_shell_return(RSYSINFO.USED_MEMORY_PERCENTAGE, ssh=ssh, ssh_user=user, ssh_host=ip, ssh_key=ssh_key)
        temp = round(float(temp))
        details['used_memory'] = temp

    logging.debug(f'Host {host} Details: {details}')
    return details

def display_server_details(display, details: dict, index=None):
    logging.info(f"Generating display for host: {details['host']}")

    #now write the details
    display.new_image()
    current_line = -1

    #first the display title
    display.set_line_text(current_line := current_line+1, CONFIG['display_title'], center=True)
    #also display the counter
    if index is not None:
        display.set_line_text(current_line, f'{index + 1} / {SERVER_COUNT}', right_justify=True)

    if not details['accessible']:
        display.write_text(f"***HOST {details['host']} OFFLINE***", center=True)
    else:
        display.set_line_text(current_line := current_line+1, f"Host: {details['host']} ({details['ip']})")
        display.set_line_text(current_line := current_line+1, f"System: {details['system']}")
        display.set_line_text(current_line := current_line+1, f"OS: {details['operating_system']}")
        display.set_line_text(current_line := current_line+1, f"CPU: {details['cpu_model']} ({details['architecture']}),  {details['cpu_load']}%,  {details['cpu_temp']}°C")
        display.set_line_text(current_line := current_line+1, f"Memory: {details['memory']}MB,  {details['used_memory']}%")

    #now update
    display.update()

def display_overview_page(display, servers, accessible, temperatures: list, cpu_loads: list, memory_usages: list):
    logging.info('Display summary page...')
    display.new_image()

    #calculate averages
    average_temperature = round(sum(temperatures) / len(temperatures))
    average_cpu_load = round(sum(cpu_loads) / len(cpu_loads))
    average_memory_usage = round(sum(memory_usages) / len(memory_usages))

    #display
    current_line = -1
    display.set_line_text(current_line := current_line+1, CONFIG['display_title'], center=True)
    display.set_line_text(current_line := current_line+1, "Summary", center=True)
    display.set_line_text(current_line := current_line+1, f"Servers Up: {accessible} / {servers}", center=True)
    display.set_line_text(current_line := current_line+1, f"Avg. CPU Load: {average_cpu_load}%", center=True)
    display.set_line_text(current_line := current_line+1, f"Avg. CPU Temp: {average_temperature}°C", center=True)
    display.set_line_text(current_line := current_line+1, f"Avg. Memory Usage: {average_memory_usage}%", center=True)

    display.update()

def initialization():
    global CONFIG
    global FONT

    #check config file
    config_file = '.data/config.yaml'
    DOCKER = os.getenv('DOCKER')
    if DOCKER:
        logging.info('Running on docker...')

    if not os.path.isfile(config_file):
        logging.error(f'Could not find config file [{config_file}].')
        return False

    CONFIG = yaml.safe_load(open(config_file))
    logging.info(f'Config file: [{config_file}]')
    logging.debug(f'Config: {CONFIG}') 

    #check ssh key
    if 'ssh_key' not in CONFIG:
        logging.error(f'Missing config ssh_key.')
        return False

    ssh_key = os.path.join(os.path.dirname(os.path.realpath(__file__)), CONFIG['ssh_key'])
    if not os.path.isfile(ssh_key):
        logging.error(f'Invalid ssh_key file: [{ssh_key}]')
        return False
    
    logging.info(f'SSH Key File: {ssh_key}')
    
    #load font
    if CONFIG.get('font_file'):
        font_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), CONFIG['font_file'])
        if not os.path.isfile(font_file):
            logging.error(f'Invalid font_file file in config: [{font_file}]')
            return False
        CONFIG['full_font_file'] = font_file

    return True

def process_loop():
    #initialize display
    display = epd_text(CONFIG['line_count'], margin_x=1, margin_y=1, font_file=CONFIG.get('full_font_file'), font_size=CONFIG.get('font_size'))

    #process loop
    first_run = True
    while True:
        logging.info('Starting process loop...')
        
        accessible = 0
        temperatures = []
        cpu_loads = []
        memory_usage = []
        for i in range(SERVER_COUNT):
            #grab data
            wait_time = time.time()
            details = get_server_details(SERVERS[i]['host'], SERVERS[i]['user'])
            wait_time = time.time() - wait_time
            logging.info(f'Grabbing data took {wait_time} seconds.')

            #save results for use on summary page
            if details['accessible']:
                accessible += 1
                temperatures.append(float(details['cpu_temp']))
                cpu_loads.append(float(details['cpu_load']))
                memory_usage.append(float(details['used_memory']))

            #if there is time left, wait for it
            if not first_run:
                wait_time = round(CONFIG['display_time'] - wait_time, 2)
                if wait_time > 0:
                    logging.info('Wating - ' + str(wait_time) + 's')
                    time.sleep(wait_time)
            first_run = False

            #display
            display_server_details(display, details, index=i)
        
        logging.info('Wating - ' + str(CONFIG['display_time']) + 's')
        time.sleep(CONFIG['display_time'])

        #now that we're done with the loop, print an overview page
        display_overview_page(display, SERVER_COUNT, accessible, temperatures, cpu_loads, memory_usage)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.info('Process starting...')

    valid = initialization()
    if not valid:
        logging.error('Failed to initialize. Exiting...')
        sys.exit()

    SERVER_COUNT = len(CONFIG['servers'])
    SERVERS = CONFIG['servers']
    logging.debug(f'Server Count: {SERVER_COUNT}')
    logging.debug(f'Servers: {SERVERS}')
    logging.debug('Display Time: ' + str(CONFIG['display_time']))
    logging.debug('Display Title: ' + CONFIG['display_title'])

    #load cache file
    CACHE = CacheFile()
    logging.debug(f'Cache File: {CACHE.getFilePath()}')

    #run
    process_loop()