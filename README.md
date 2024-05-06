[![python](https://img.shields.io/badge/Python-3.9-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
![version](https://img.shields.io/badge/version-1.1.1-red)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/Kaminyou/space-warner/blob/main/LICENSE)
![linting workflow](https://github.com/Kaminyou/space-warner/actions/workflows/main.yml/badge.svg)
# space-warner
Send a message to your Slack whenever your space is becoming full!

## Setup
1. Create `.env`
```
API_ENDPOINT=  # YOUR SLACK API ENDPOINT
FILE_SYSTEMS=  # separated by , and :: can be used to set a local threshold e.g., xxx::0.6,yyy,zzz::0.5
GLOBAL_THRESHOLD=  # e.g., 0.70 -> send a message when space usage >= 70% (will be considered when a local threshold is not set)
TRIGGER_INTERVAL=60  # second # if there is no warning triggered previously -> interval to check the system
WARNING_INTERVAL=3600  # second # once a warning is triggered, trigger again after WARNING_INTERVAL
```
2. 
```
$ docker-compose up --build -d
```