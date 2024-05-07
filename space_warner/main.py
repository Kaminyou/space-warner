import logging
import os
import subprocess
import time
import typing as t

import requests


def get_disk_usage() -> t.List[t.Dict[str, t.Any]]:
    # Execute the 'df -h' command and capture its output
    result = subprocess.run(['df', '-h'], stdout=subprocess.PIPE, text=True)
    output = result.stdout

    # Split the output into lines and remove the header line
    lines = output.splitlines()
    header = lines[0].split()
    data = []

    # Find the index for 'Avail' and 'Use%' columns
    avail_index = header.index('Avail')
    used_index = header.index('Use%')

    # Parse each line to extract the 'avail' and 'used%' values
    for line in lines[1:]:
        parts = line.split()
        if len(parts) > used_index:  # Checking to make sure the line has enough columns
            filesystem = parts[0]
            avail = parts[avail_index]
            used_percent = parts[used_index]
            data.append({'filesystem': filesystem, 'avail': avail, 'used%': used_percent})

    return data


def warn(filesystem: str, used: str) -> None:
    api_endpoint = os.environ.get('API_ENDPOINT', '')
    try:
        headers = {
            'Content-type': 'application/json',
        }

        json_data = {
            'text': f'WARNING: {filesystem}: used {used}',
        }

        _ = requests.post(
            api_endpoint,
            headers=headers,
            json=json_data,
        )

    except Exception as e:
        logging.log(f'error due to {e}')


def parse_filesystem_setting() -> t.Dict[str, float]:
    global_threshold = float(os.environ.get('GLOBAL_THRESHOLD', 1.0))
    file_systems_and_thresholds = os.environ.get('FILE_SYSTEMS', []).split(',')
    file_system_to_threshold = {}

    for file_system_and_threshold in file_systems_and_thresholds:
        if '::' in file_system_and_threshold:
            file_system, threshold = file_system_and_threshold.split('::')
            threshold = float(threshold)
        else:
            file_system = file_system_and_threshold
            threshold = global_threshold

        if file_system in file_system_to_threshold:
            raise ValueError('Duplicated file systems are detected')

        file_system_to_threshold[file_system] = threshold

    return file_system_to_threshold


def monitor(
    disk_usage_info: t.List[t.Dict[str, t.Any]],
    file_system_to_threshold: t.Dict[str, float],
    trigger_interval: int,
    warning_interval: int,
) -> None:
    is_warning = False
    for info in disk_usage_info:
        if info['filesystem'] in file_system_to_threshold:
            used = float(info['used%'].replace('%', ''))
            if used >= file_system_to_threshold[info['filesystem']]:
                is_warning = True
                warn(filesystem=info['filesystem'], used=info['used%'])

    if is_warning:
        time.sleep(warning_interval)
    else:
        time.sleep(trigger_interval)


def main():

    trigger_interval = os.environ.get('TRIGGER_INTERVAL', 60)
    warning_interval = os.environ.get('WARNING_INTERVAL', 3600)

    while True:
        disk_usage_info = get_disk_usage()
        file_system_to_threshold = parse_filesystem_setting()
        monitor(
            disk_usage_info=disk_usage_info,
            file_system_to_threshold=file_system_to_threshold,
            trigger_interval=trigger_interval,
            warning_interval=warning_interval,
        )


if __name__ == '__main__':
    main()
