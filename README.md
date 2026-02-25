# Local AI Video Generation Studio

This project enables a fully local AI video generation pipeline using Ollama, Stable Diffusion, Bark, and FFmpeg.

## Prerequisites

### 1. Hardware
- **GPU**: NVIDIA GPU (6GB VRAM minimum, 12GB recommended).
- **RAM**: 16GB+.
- **OS**: Windows 10/11 or Linux.

### 2. Software
- [Python 3.10+](https://www.python.org/)
- [Git](https://git-scm.com/)
- [FFmpeg](https://ffmpeg.org/download.html) (Ensure it's in your system PATH)

## Installation Steps

### Step 1: Text Generation (Ollama)
1. Download and install Ollama from [ollama.com](https://ollama.com/).
2. Pull the Mistral model:
   ```bash
   ollama pull mistral
   ```
3. Start the Ollama server:
   ```bash
   ollama serve
   ```

### Step 2: Image Generation (Stable Diffusion)
1. Clone the WebUI:
   ```bash
   git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
   ```
2. Run `webui-user.bat` to install dependencies and start the UI.
3. Enable API: Edit `webui-user.bat` and add `--api` to `COMMANDLINE_ARGS`.
   ```batch
   set COMMANDLINE_ARGS=--api
   ```
4. Install **AnimateDiff Extension**:
   - Open WebUI -> Extensions -> Install from URL.
   - URL: `https://github.com/continue-revolution/sd-webui-animatediff`
   - Restart WebUI.

### Step 3: Python Environment
1. Create a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Folder Structure
- `src/`: Python source code for orchestration.
- `outputs/`: All generated assets.
- `requirements.txt`: Python package list.

## Usage
Run the master script:
```bash
python src/main.py
```

## Hardware Optimization Tips
- **Low VRAM**: Use `--medvram` or `--lowvram` in Stable Diffusion `COMMANDLINE_ARGS`.
- **Bark Speed**: Bark is heavy; use `SMALL_MODELS=True` environment variable for faster (lower quality) generation on weak GPUs.
- **FFmpeg**: Use hardware acceleration (e.g., `-c:v h264_nvenc`) if available.
