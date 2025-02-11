from app.tools import ToolRegistry
from pathlib import Path
import shutil

def setup_environment():
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Clean previous test files
    for dir in ["node_modules", "my-app"]:
        shutil.rmtree(output_dir / dir, ignore_errors=True)

def test_npm_commands():
    print("\n=== Testing NPM/NPX Commands ===")
    setup_environment()
    run_npm = ToolRegistry.get_tool("run_npm")
    
    # Test valid commands
    commands = [
        "npm init -y",
        "npm install react react-dom",
        "npx create-react-app my-app",
        "npm run build",
        "npx eslint --init --skip-questions"
    ]
    
    for cmd in commands:
        print(f"\nTesting command: {cmd}")
        result = run_npm(cmd)
        print(f"Result:\n{result}")
        print("-" * 60)

    # Test blocked commands
    blocked_commands = [
        "npm start",
        "npx serve",
        "npm publish",
        "npm run deploy"
    ]
    
    for cmd in blocked_commands:
        print(f"\nTesting blocked command: {cmd}")
        result = run_npm(cmd)
        print(f"Result:\n{result}")
        print("-" * 60)

    # Cleanup
    setup_environment()

if __name__ == "__main__":
    test_npm_commands()
    print("\n=== Tests Complete ===") 