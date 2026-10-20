# ✦ Deskmate

A Python desktop assistant powered by AI, built with PySide6 and Groq. It combines a modern chat interface with Windows automation, allowing users to control supported PC functions through natural-language instructions.

## Features

- 💬 AI-powered conversational interface
- ⚡ Global hotkey activation
- 🖥️ Launch installed applications
- 📂 Search for and open files and folders
- 🗃️ Create, copy, move, and delete supported files and folders
- 🔄 Automatically generated application list for each user's PC
- 🎨 Modern dark-themed PySide6 GUI

## Project Structure

- `main.py` — Application entry point
- `ai/` — AI integration
- `core/` — System tools and desktop automation
- `gui/` — User interface and styling
- `data/` — Locally generated application data
- `requirements.txt` — Python dependencies
- `.env` — Local API configuration (not committed)

## Requirements

- Python 3.10 or a compatible version supported by the dependencies
- A Groq API key
- Windows PC

## Setup

1. Clone this repository.
2. Create and activate a Python virtual environment.
3. Install dependencies from `requirements.txt`.
4. Create a `.env` file and configure your Groq API key using the environment variable expected by the code.
5. Run `python main.py`.

The assistant generates its application list locally based on the user's PC.

## Security

- Never share or commit API keys.
- Review file operations carefully, especially deletion and overwriting.
- AI-generated responses may be inaccurate; verify important actions.

## License

Choose and add a license file before describing this repository as open source under a particular license.
