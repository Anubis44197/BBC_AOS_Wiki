# Quick Start Guide

This guide gets you started with `bbc-aos` for local development.

## 1. Installation
Install the package directly from PyPI:
```bash
pip install bbc-aos
```

## 2. Initialize a Project
Initialize a local project in your workspace directory:
```bash
bbc init
```
This creates a local `.bbc/` folder containing working session databases and local audit logs.

## 3. Codebase Indexing
Scan your codebase symbols and compile the initial semantic memory map:
```bash
bbc index .
```

## 4. Run the Orchestrator
Start the JSON-RPC sidecar interface server:
```bash
bbc start
```
The sidecar server is now ready to receive JSON-RPC queries from your IDE.
