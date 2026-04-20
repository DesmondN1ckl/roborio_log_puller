
## Requirements

- Python 3.10+
- [Paramiko](https://www.paramiko.org/)
- Network access to the roboRIO
- SSH enabled on the target roboRIO (Enabled by default)

## Installation

Clone the repo:

```bash
git clone https://github.com/DesmondN1ckl/roborio_log_puller.git
cd roborio_log_puller
```

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install paramiko
```

## Usage

Basic run:

```bash
python3 roborio_log_puller.py
```
