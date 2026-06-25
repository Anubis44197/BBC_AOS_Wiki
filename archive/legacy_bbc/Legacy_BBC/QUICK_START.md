# BBC Quick Start

## 1. Install

```bash
git clone https://github.com/Anubis44197/BBC_MASTER_BBCMath.git BBC
cd BBC
pip install -r requirements.txt
```

## 2. Analyze a Project

```bash
python bbc.py analyze /path/to/project
python bbc.py verify /path/to/project
```

## 3. Inject Rules for Detected AI Tools

```bash
python bbc.py inject /path/to/project
```

BBC writes rules only for detected IDEs/extensions. If nothing is detected, it keeps the sealed context in `.bbc/`.

## 4. Run in the Background

```bash
python bbc.py start /path/to/project --background
python bbc.py status /path/to/project
python bbc.py stop /path/to/project
```

## 5. Useful Checks

```bash
python bbc.py check generated.py --path /path/to/project
python bbc.py impact src/file.py --path /path/to/project
python bbc.py telemetry /path/to/project
python bbc.py audit /path/to/project
```

## 6. Remove BBC from a Target Project

```bash
python bbc.py purge /path/to/project --force
```

Use this before publishing a target project if you want BBC traces removed.
