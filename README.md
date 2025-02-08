# Bespoke Dev - AI Development Agent

A two-tier AI development agent powered by Ollama that can analyze, plan, and execute coding tasks.

## Features

- **Two-Tier Architecture**
  - Analysis Tier (R1): Plans and breaks down tasks
  - Execution Tier (Qwen): Implements code changes with tool support

- **Smart Task Planning**
  - Breaks complex tasks into logical steps
  - Groups related changes together
  - Maintains context between steps

- **File Operations**
  - Read and write files
  - Maintains file content between operations
  - Safe file handling with error recovery

## Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running
- Required models pulled:
  ```bash
  ollama pull deepseek-r1:7b
  ollama pull qwen2.5-coder:7b
  ```

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd bespoke-dev
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   .\venv\Scripts\activate  # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Command Line Interface

The app can be run using the CLI:

```bash
# Basic usage
python -m app "Create a simple calculator with add and multiply functions"

# Or using the installed package
bespoke-dev "Create a simple calculator with add and multiply functions"
```

### Python API

You can also use the app programmatically:

```python
import asyncio
from app.workflow import process_task

async def main():
    task = "Create a simple calculator with add and multiply functions"
    results = await process_task(task)
    print(results)

asyncio.run(main())
```

## Example Tasks

1. **Create New Project**
   ```bash
   python -m app "Create a Flask API with two endpoints: /add and /multiply"
   ```

2. **Add Features**
   ```bash
   python -m app "Add input validation and error handling to calculator.py"
   ```

3. **Create Tests**
   ```bash
   python -m app "Create unit tests for the calculator functions"
   ```

## Output Structure

Generated files are placed in the `output/` directory:
```
output/
├── src/
│   └── your_generated_code.py
├── tests/
│   └── test_your_code.py
└── other_files...
```

## Configuration

The app can be configured through environment variables:
- `BESPOKE_OUTPUT_DIR`: Custom output directory (default: `./output`)
- `BESPOKE_MAX_STEPS`: Maximum number of steps (default: 25)

## Development

### Project Structure
```
bespoke-dev/
├── app/
│   ├── agents/
│   │   ├── analysis.py    # R1 analysis agent
│   │   ├── execution.py   # Qwen execution agent
│   │   └── utility.py     # Shared utilities
│   ├── tools.py           # Tool definitions
│   ├── workflow.py        # Core workflow
│   └── main.py           # CLI interface
├── requirements.txt
└── README.md
```

### Running Tests
```bash
pytest tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Your License Here]

## Acknowledgments

- [Ollama](https://ollama.ai/) for the AI models
- [Rich](https://rich.readthedocs.io/) for beautiful terminal output 