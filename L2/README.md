# Lab 2: Dockerization

This folder contains the dockerized versions of:
1. The weather application (`main.py`)
2. The `opencode-ai` coding agent sandbox

## 1. Weather Application

### Build the Image
```bash
docker build -t weather-app .
```

### Run the Container
```bash
docker run --rm weather-app
```

---

## 2. Opencode Sandbox

This container is used to run the `opencode-ai` coding agent in an isolated environment.

### Build the Image
```bash
docker build -f Dockerfile.opencode -t opencode-sandbox .
```

### Run the Sandbox
```bash
docker run -it --rm -v $(pwd):/workspace opencode-sandbox
```
If you are on Windows PowerShell:
```powershell
docker run -it --rm -v ${PWD}:/workspace opencode-sandbox
```
