# ChatGPT Account Creator

A Python automation script that creates ChatGPT accounts using Playwright browser automation and temporary email services.

## Features

- Automated ChatGPT account creation
- Temporary email generation for verification
- Random profile data generation (name, birthday)
- Browser stealth mode to avoid detection
- Sequential account creation
- Account data saved to `accounts.txt`

## Requirements

- Python 3.10+
- Playwright
- Firefox browser

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install firefox
```

## Configuration

Edit `config.json` to customize:

```json
{
  "max_workers": 3,
  "headless": false,
  "slow_mo": 1000,
  "timeout": 100000,
  "password": "YourPassword123!"
}
```

- `headless`: Run browser in headless mode (true/false)
- `slow_mo`: Delay between actions in milliseconds
- `timeout`: Operation timeout in milliseconds
- `password`: Password for created accounts (must be 12+ characters)

## Usage

Run the script:
```bash
python main.py
```

Enter the number of accounts you want to create when prompted.

## Output

Created accounts are saved to `accounts.txt` in the format:
```
email|password
```

## Project Structure

```
.
├── main.py              # Main entry point
├── config.json          # Configuration file
├── requirements.txt     # Python dependencies
├── modules/
│   ├── chatgpt.py      # Account creation logic
│   ├── config.py       # Configuration handler
│   └── logging.py      # Logging utilities
├── debug/               # Debug output
└── accounts.txt        # Created accounts
```

## Disclaimer

This tool is for educational purposes only. Use at your own risk and comply with OpenAI's Terms of Service.
