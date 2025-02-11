"""
Tool registry and file operation tools.
"""
from typing import Dict, List, Callable, Any
from functools import wraps
from pathlib import Path
from rich.console import Console
import subprocess
import os

console = Console()

# Configuration
OUTPUT_DIR = Path("output")  # Directory for generated files
OUTPUT_DIR.mkdir(exist_ok=True)

def normalize_path(path: str) -> Path:
    """
    Normalize a path to be relative to OUTPUT_DIR and resolve any '..' or '.' while allowing safe nested directories.
    
    Args:
        path (str): Path to normalize, can include subdirectories (e.g., 'src/utils/helper.py')
        
    Returns:
        Path: Normalized path relative to OUTPUT_DIR
        
    Example:
        >>> normalize_path('src/utils/helper.py')
        Path('output/src/utils/helper.py')
        >>> normalize_path('../etc/passwd')  # Attempts to escape
        Path('output/etc/passwd')
        >>> normalize_path('/absolute/path/file.py')  # Attempts absolute path
        Path('output/file.py')
    """
    # Handle empty path and './' as root directory
    if path in ('', '.', './'):
        return OUTPUT_DIR
    
    clean_path = Path(path)
    
    # Remove any leading slashes or absolute paths
    parts = [part for part in clean_path.parts if part not in ('/', '\\', '..')]
    
    # Allow single '.' to represent current directory but prevent directory traversal
    parts = [p for p in parts if p != '.']
    
    if not parts:
        return OUTPUT_DIR
        
    # Reconstruct path relative to OUTPUT_DIR
    safe_path = OUTPUT_DIR.joinpath(*parts)
    
    # Ensure the final path is still within OUTPUT_DIR
    try:
        safe_path.relative_to(OUTPUT_DIR)
    except ValueError:
        # If path somehow escapes OUTPUT_DIR, fall back to just the filename
        safe_path = OUTPUT_DIR / parts[-1]
        
    return safe_path

class ToolRegistry:
    """Centralized registry for all available tools."""
    _tools: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def register(cls, name: str = None, description: str = None, input_schema: Dict = None):
        """Decorator to register a tool function with its schema."""
        def decorator(func: Callable):
            nonlocal name, description, input_schema
            name = name or func.__name__
            description = description or func.__doc__
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                console.print(f"[dim]Executing {name}[/dim]")
                return func(*args, **kwargs)
            
            tool_def = {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": input_schema or {},
                    "required": list(input_schema.keys()) if input_schema else []
                },
                "function": wrapper
            }
            
            cls._tools[name] = tool_def
            return wrapper
        return decorator
    
    @classmethod
    def get_all_tools(cls) -> List[Dict[str, Any]]:
        """Get all registered tools as a list of tool definitions."""
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"]
            }
            for tool in cls._tools.values()
        ]
    
    @classmethod
    def get_tool(cls, name: str) -> Callable:
        """Get a specific tool's function by name."""
        tool = cls._tools.get(name)
        return tool["function"] if tool else None

# Tool definitions
@ToolRegistry.register(
    name="read_file",
    description="Read contents of a file. Supports nested directories (e.g., 'src/utils/helper.py')",
    input_schema={
        "path": {
            "type": "string",
            "description": "Path to the file to read, can include subdirectories"
        }
    }
)
def read_file(path: str) -> str:
    """Read contents of a file.
    
    Args:
        path (str): Path to the file to read, can include subdirectories (e.g., 'src/utils/helper.py')
        
    Returns:
        str: Contents of the file
    """
    try:
        file_path = normalize_path(path)
        console.print(f"[dim]Reading file: {path}[/dim]")
        
        # Ensure parent directories exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                return content
        except FileNotFoundError:
            return f"File '{path}' does not exist."
    except ValueError as e:
        return f"Error: {str(e)}"

@ToolRegistry.register(
    name="write_file",
    description="Write content to a file. Supports nested directories (e.g., 'src/utils/helper.py')",
    input_schema={
        "path": {
            "type": "string",
            "description": "Path to the file to write, can include subdirectories"
        },
        "content": {
            "type": "string",
            "description": "Content to write to the file"
        }
    }
)
def write_file(path: str, content: str) -> str:
    """Write content to a file with optional overwrite protection.
    
    Args:
        path (str): Path to the file to write, can include subdirectories (e.g., 'src/utils/helper.py')
        content (str): Content to write to the file
        overwrite (bool): Whether to overwrite the file if it exists
        
    Returns:
        str: Success or error message
    """
    try:
        file_path = normalize_path(path)
        
        if file_path.suffix == '':
            return "Error: The provided path does not include a filename."
        
        console.print(f"[dim]Writing to file: {path}[/dim]")
        
        # Ensure parent directories exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the content to the file
        with open(file_path, 'w') as f:
            f.write(content)
        
        return f"Successfully wrote to {path}"
    except ValueError as e:
        return f"Error: {str(e)}"
    except Exception as ex:
        return f"Error: An unexpected error occurred: {str(ex)}"

@ToolRegistry.register(
    name="create_directory",
    description="Create a new directory. Supports nested directories (e.g., 'src/utils')",
    input_schema={
        "path": {
            "type": "string",
            "description": "Path to the directory to create, can include nested directories"
        }
    }
)
def create_directory(path: str) -> str:
    """Create a new directory.
    
    Args:
        path (str): Path to the directory to create, can include nested directories (e.g., 'src/utils')
        
    Returns:
        str: Success or error message
    """
    try:
        dir_path = normalize_path(path)
        
        # Check if the path already exists
        if dir_path.exists():
            if dir_path.is_dir():
                return f"Directory '{path}' already exists."
            else:
                return f"Error: A file with the name '{path}' already exists."
        
        # Check if any parent in the path is an existing file
        for parent in dir_path.parents:
            if parent == OUTPUT_DIR:
                continue  # Skip the base output directory
            if parent.exists() and parent.is_file():
                return f"Error: Cannot create directory under '{parent}' because it is an existing file."
        
        # Create the directory
        dir_path.mkdir(parents=True, exist_ok=False)
        
        return f"Successfully created directory '{path}'."
    except ValueError as e:
        return f"Error: {str(e)}"
    except FileExistsError:
        return f"Error: Directory '{path}' already exists."
    except Exception as ex:
        return f"Error: An unexpected error occurred: {str(ex)}"

@ToolRegistry.register(
    name="edit_file",
    description=(
        "Edit content of a file between given markers (or delimiters). Specify the file path "
        "and the unique begin and end markers. IMPORTANT: Before calling this tool, use "
        "read_file to inspect the file contents and ensure that the provided markers accurately "
        "match text in the file. This prevents applying edits on incorrect or missing sections."
    ),
    input_schema={
         "path": {
             "type": "string",
             "description": "Path to the file to edit, can include nested directories."
         },
         "begin_marker": {
             "type": "string",
             "description": "Unique text marker indicating the beginning of the section to edit."
         },
         "end_marker": {
             "type": "string",
             "description": "Unique text marker indicating the ending of the section to edit."
         },
         "new_content": {
             "type": "string",
             "description": "New content to insert between the markers."
         }
    }
)
def edit_file(path: str, begin_marker: str, end_marker: str, new_content: str) -> str:
    """Edit content of a file between specified markers.
    
    The tool locates the first occurrence of the given begin_marker and the following occurrence
    of end_marker in the file. It then replaces any content between these markers with the provided
    new_content, keeping the markers intact.
    
    IMPORTANT: Always perform a read_file operation before using this tool so that you can verify
    that the file contains the expected markers (or delimiters). The markers you supply must match
    what exists in the file; otherwise, the edit will fail.
    
    After editing, the tool reads the updated file content and returns it along with a success message.
    
    Args:
        path (str): Path to the file to edit.
        begin_marker (str): Unique text indicating the beginning boundary.
        end_marker (str): Unique text indicating the ending boundary.
        new_content (str): The content to insert between the markers.
        
    Returns:
        str: A success message along with the updated file content, or an error message.
    """
    try:
        file_path = normalize_path(path)
        
        # Ensure the file exists
        if not file_path.exists():
            return f"Error: File '{path}' does not exist."
        
        # Read the file content
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Find the beginning marker
        start_idx = content.find(begin_marker)
        if start_idx == -1:
            return f"Error: Begin marker '{begin_marker}' not found in file."
        
        # Find the ending marker after the begin marker
        end_idx = content.find(end_marker, start_idx + len(begin_marker))
        if end_idx == -1:
            return f"Error: End marker '{end_marker}' not found in file after the begin marker."
        
        # Construct the new file content; preserve markers and insert new content between them
        new_file_content = (
            content[:start_idx + len(begin_marker)] +
            "\n" + new_content + "\n" +
            content[end_idx:]
        )
        
        # Write the updated content back to the file
        with open(file_path, 'w') as f:
            f.write(new_file_content)
        
        # Implied read_file: read back the updated file content
        with open(file_path, 'r') as f:
            updated_content = f.read()

        return f"Successfully edited {path} between markers. Updated file content:\n{updated_content}"
    except ValueError as e:
        return f"Error: {str(e)}"
    except Exception as ex:
        return f"Error: An unexpected error occurred: {str(ex)}"

@ToolRegistry.register(
    name="list_directory",
    description="List the contents of a directory. Provide the path to the directory (e.g., 'src/utils').",
    input_schema={
         "path": {
             "type": "string",
             "description": "Path to the directory whose contents should be listed, can include nested directories."
         }
    }
)
def list_directory(path: str) -> str:
    """List the contents of a directory.

    Args:
        path (str): Path to the directory whose contents to list (relative to OUTPUT_DIR).

    Returns:
        str: A string listing files and subdirectories, or an error message.
    """
    try:
        dir_path = normalize_path(path)
        
        if not dir_path.exists():
            return f"Error: Directory '{path}' does not exist."
        
        if not dir_path.is_dir():
            return f"Error: Path '{path}' is not a directory."
        
        contents = list(dir_path.iterdir())
        
        if not contents:
            return f"Directory '{path}' is empty."
        
        result = f"Contents of directory '{path}':\n"
        
        for item in sorted(contents, key=lambda x: x.name):
            if item.is_dir():
                result += f"[DIR]  {item.name}\n"
            else:
                result += f"[FILE] {item.name}\n"
                
        return result.strip()  # remove trailing newline
    except Exception as ex:
        return f"Error: An unexpected error occurred: {str(ex)}"

@ToolRegistry.register(
    name="create_file",
    description="Create a new file with the specified content. Provide the file path and content for each file you want to create.",
    input_schema={
         "path": {
             "type": "string",
             "description": "Path to the file to create. Must include a filename and may include nested directories."
         },
         "content": {
             "type": "string",
             "description": "Content to include in the newly created file."
         }
    }
)
def create_file(path: str, content: str) -> str:
    """Create a new file with the given content.
    
    This tool is intended for project scaffolding tasks such as creating multiple files at once
    that are part of the application structure or common configuration files.
    
    Args:
        path (str): Path to the file to create. Must include a filename.
        content (str): The content that will be written to the file.
    
    Returns:
        str: Success message if the file was created, or an error message if it already exists or an unexpected error occurred.
    """
    try:
        file_path = normalize_path(path)
        
        # Check if the file already exists
        if file_path.exists():
            return f"Error: File '{path}' already exists. Use a different tool to update existing files."
        
        # Ensure parent directories exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create and write content to the new file
        with open(file_path, 'w') as f:
            f.write(content)
        
        return f"Successfully created file '{path}'."
    except Exception as e:
        return f"Error: An unexpected error occurred: {str(e)}"

@ToolRegistry.register(
    name="run_npm",
    description="Execute any npm/npx command in a controlled environment",
    input_schema={
        "command": {
            "type": "string",
            "description": "Full npm/npx command to execute (e.g. 'install', 'run build', 'npx create-react-app')"
        }
    }
)
def run_npm(command: str) -> str:
    """Execute npm/npx commands safely in the output directory."""
    blocked_commands = {
        "start", "dev", "serve", "publish", 
        "run prod", "deploy", "exec", "restart"
    }
    
    # Block dangerous commands
    if any(cmd in command.lower() for cmd in blocked_commands):
        return f"Blocked potentially dangerous command: {command.split()[0]}"

    try:
        parts = command.split()
        if not parts or parts[0] not in ["npm", "npx"]:
            return "Invalid command - must start with npm/npx"

        # Windows executable handling
        exe_suffix = ".cmd" if os.name == "nt" else ""
        executable = f"{parts[0]}{exe_suffix}"
        
        result = subprocess.run(
            [executable, *parts[1:]],
            cwd=OUTPUT_DIR,
            capture_output=True,
            text=True,
            shell=True,
            timeout=120  # Increased timeout for complex operations
        )
        
        output = f"{parts[0]} output:\n{result.stdout}"
        if result.stderr:
            output += f"\n{parts[0]} errors:\n{result.stderr}"
            
        return output
        
    except Exception as e:
        return f"{parts[0]} error: {str(e)}"

@ToolRegistry.register(
    name="run_pip",
    description="Execute pip commands in project directory. Only allowed: install, freeze",
    input_schema={
        "command": {
            "type": "string",
            "enum": ["install", "freeze"],
            "description": "PIP command to execute"
        },
        "packages": {
            "type": "string",
            "description": "Package specifier(s) to install"
        }
    }
)
def run_pip(command: str, packages: str = "") -> str:
    """Safely execute pip commands in isolated output directory"""
    allowed = {"install", "freeze"}
    if command not in allowed:
        return f"Blocked dangerous pip command: {command}"
    
    try:
        args = [command, packages] if command == "install" else [command]
        result = subprocess.run(
            ["pip", *args],
            cwd=OUTPUT_DIR,
            timeout=120,
            capture_output=True,
            text=True
        )
        return f"pip {command}:\n{result.stdout}\n{result.stderr}"
    except Exception as e:
        return f"pip error: {str(e)}" 