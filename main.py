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


def main():

    trigger_interval = os.environ.get('TRIGGER_INTERVAL', 60)
    warning_interval = os.environ.get('WARNING_INTERVAL', 3600)

    while True:

        disk_usage_info = get_disk_usage()
        target_filesystems = set(os.environ.get('FILE_SYSTEMS', []).split(','))
        threshold = float(os.environ.get('THRESHOLD', 1.0))

        is_warning = False
        for info in disk_usage_info:
            if info['filesystem'] in target_filesystems:
                used = float(info['used%'].replace('%', ''))
                if used >= threshold:
                    is_warning = True
                    warn(filesystem=info['filesystem'], used=info['used%'])

        if is_warning:
            time.sleep(warning_interval)
        else:
            time.sleep(trigger_interval)


if __name__ == '__main__':
    main()
