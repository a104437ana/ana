# ana
## Personal Project
Personal event manager in your terminal. Add, list, edit and remove events with a flexible date syntax.

## Install
```bash
git clone git@github.com:a104437ana/ana.git
cd ana
pip install -e .
```

After this, `ana` is available anywhere in your terminal.

## Usage
Example usage:
```
ana greet
ana add 15 4 2026 14:30 "dentist"
ana ls
ana edit 1 "date"
ana rm 1
ana add 1 1 2027 "new year"
ana clear
```