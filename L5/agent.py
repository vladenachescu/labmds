import json
import os
import sys
import subprocess
import requests

# Try to import openai, but fail gracefully if not installed
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

OLLAMA_URL = "http://localhost:11434/v1"

# === TOOL IMPLEMENTATIONS ===

def get_weather(city: str) -> str:
    """Get the current weather for a city using Open-Meteo."""
    # Simple city coordinates mapping
    coords = {
        "bucharest": (44.4323, 26.1063),
        "london": (51.5074, -0.1278),
        "tokyo": (35.6762, 139.6503),
        "new york": (40.7128, -74.0060),
        "paris": (48.8566, 2.3522)
    }
    
    clean_city = city.lower().strip()
    if clean_city not in coords:
        return f"Weather tool only supports: {', '.join(coords.keys())}."
        
    lat, lon = coords[clean_city]
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        temp = data.get("current_weather", {}).get("temperature")
        wind = data.get("current_weather", {}).get("windspeed")
        return f"Current weather in {city.capitalize()}: {temp}°C, Wind speed: {wind} km/h."
    except Exception as e:
        return f"Error fetching weather: {e}"

def calculate(expression: str) -> str:
    """Safely evaluate an arithmetic expression."""
    # Allow only digits, basic operators, and spaces
    if not all(c in "0123456789+-*/(). " for c in expression):
        return "Error: unsafe characters in mathematical expression."
    try:
        # Use eval after verification
        result = eval(expression, {"__builtins__": None}, {})
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error evaluating expression: {e}"

def add_task(description: str, due_date: str) -> str:
    """Add a task to tasks.json."""
    tasks_file = "tasks.json"
    tasks = []
    if os.path.exists(tasks_file):
        try:
            with open(tasks_file, "r") as f:
                tasks = json.load(f)
        except Exception:
            tasks = []
            
    new_id = max([t.get("id", 0) for t in tasks] + [0]) + 1
    new_task = {
        "id": new_id,
        "description": description,
        "due_date": due_date,
        "status": "pending"
    }
    tasks.append(new_task)
    try:
        with open(tasks_file, "w") as f:
            json.dump(tasks, f, indent=4)
        return f"Successfully added task {new_id}: '{description}' due by {due_date}."
    except Exception as e:
        return f"Error saving task: {e}"

def run_command(command: str) -> str:
    """Run a terminal command after asking the user for confirmation."""
    print(f"\n[SECURITY WARNING] The agent wants to execute the following command:")
    print(f"  > {command}")
    confirm = input("Do you allow execution? [y/N]: ").strip().lower()
    if confirm in ("y", "yes"):
        try:
            result = subprocess.run(command, shell=True, text=True, capture_output=True, timeout=10)
            output = result.stdout + result.stderr
            return f"Command executed with exit code {result.returncode}.\nOutput:\n{output}"
        except Exception as e:
            return f"Command execution failed: {e}"
    else:
        return "Command execution aborted by the user."

# === TOOL DEFINITION METADATA FOR OPENAI/OLLAMA ===

tools_metadata = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a city. Supports: Bucharest, London, Tokyo, New York, Paris.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "The name of the city"}
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate an arithmetic math expression.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "The math expression, e.g. '123 * 456'"}
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_task",
            "description": "Schedule a new task/todo. Translates natural language descriptions into tasks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "The task description, e.g. 'Pay taxes'"},
                    "due_date": {"type": "string", "description": "Due date, e.g., '25-05-2026' or 'May 25'"}
                },
                "required": ["description", "due_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a bash/powershell command on the user's computer. Dangerous tool, use only when explicitly requested.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The exact shell command to run"}
                },
                "required": ["command"]
            }
        }
    }
]

# === LOCAL RULE-BASED NLP SIMULATOR (FALLBACK) ===

def mock_agent_loop(prompt: str):
    """Simulates LLM tool selection in case Ollama is not running."""
    prompt_lower = prompt.lower()
    
    # 1. Weather check
    if "weather" in prompt_lower:
        for city in ["bucharest", "london", "tokyo", "new york", "paris"]:
            if city in prompt_lower:
                return "get_weather", {"city": city}
        return "get_weather", {"city": "Bucharest"} # default
        
    # 2. Math check
    if any(c in prompt_lower for c in ["*", "/", "+", "-"]) and any(c.isdigit() for c in prompt_lower):
        # Extract the math expression
        clean_expr = "".join(c for c in prompt if c in "0123456789+-*/(). ")
        return "calculate", {"expression": clean_expr.strip()}
        
    # 3. Add task check
    if "task" in prompt_lower or "todo" in prompt_lower or "add" in prompt_lower:
        # Simple extraction heuristics
        desc = "Task"
        due = "Today"
        if "add" in prompt_lower:
            parts = prompt.split("by")
            if len(parts) == 2:
                due = parts[1].strip()
                desc = parts[0].replace("Add", "").replace("task", "").replace("to", "").replace("for", "").strip()
            else:
                desc = prompt.replace("Add", "").replace("task", "").strip()
        return "add_task", {"description": desc, "due_date": due}
        
    # 4. Command check
    if "run" in prompt_lower or "execute" in prompt_lower or "cmd" in prompt_lower:
        # Extract quoted command or rest of the string
        cmd = prompt.replace("run", "").replace("execute", "").strip()
        return "run_command", {"command": cmd}
        
    return None, None

# === MAIN AGENT LOOP ===

def run_agent():
    print("=== AI Agent Loop (Lab 5) ===")
    
    # Check if Ollama is running
    ollama_running = False
    if OPENAI_AVAILABLE:
        try:
            r = requests.get(f"{OLLAMA_URL.replace('/v1', '')}/api/tags", timeout=1)
            if r.status_code == 200:
                ollama_running = True
        except Exception:
            pass
            
    if ollama_running:
        print("[Status] Local Ollama server detected! Using live LLM (mistral/tinyllama).")
        client = OpenAI(base_url=OLLAMA_URL, api_key="ollama")
    else:
        print("[Status] Ollama server offline. Falling back to local NLP Mock Agent.")
        client = None
        
    print("Type your request in natural language (or 'exit' to quit).")
    print("Examples:")
    print("  - What is the weather in London?")
    print("  - Add a task for paying taxes by 25-05-2026")
    print("  - What is 123 * 456?")
    print("  - Run command 'echo Hello World'")
    
    while True:
        try:
            user_input = input("\nuser> ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                print("Exiting agent loop. Goodbye!")
                break
                
            if client:
                # Live OpenAI tool call pipeline
                try:
                    response = client.chat.completions.create(
                        model="mistral",
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant. Use the provided tools when needed."},
                            {"role": "user", "content": user_input}
                        ],
                        tools=tools_metadata
                    )
                    message = response.choices[0].message
                    if message.tool_calls:
                        print(f"[Agent] LLM requested tool calling:")
                        for tool_call in message.tool_calls:
                            name = tool_call.function.name
                            args = json.loads(tool_call.function.arguments)
                            print(f"  Calling tool '{name}' with arguments: {args}")
                            
                            # Execute local tool
                            if name == "get_weather":
                                result = get_weather(**args)
                            elif name == "calculate":
                                result = calculate(**args)
                            elif name == "add_task":
                                result = add_task(**args)
                            elif name == "run_command":
                                result = run_command(**args)
                            else:
                                result = f"Tool '{name}' not found."
                                
                            print(f"[Tool Output] {result}")
                    else:
                        print(f"agent> {message.content}")
                except Exception as e:
                    print(f"Ollama execution error: {e}. Falling back to NLP Mock.")
                    client = None # Force fallback
            
            if not client:
                # Fallback NLP Mock Execution
                tool_name, args = mock_agent_loop(user_input)
                if tool_name:
                    print(f"[Agent Simulator] Mock LLM selected tool '{tool_name}' with arguments: {args}")
                    if tool_name == "get_weather":
                        result = get_weather(**args)
                    elif tool_name == "calculate":
                        result = calculate(**args)
                    elif tool_name == "add_task":
                        result = add_task(**args)
                    elif tool_name == "run_command":
                        result = run_command(**args)
                    print(f"[Tool Output] {result}")
                else:
                    print("agent> I'm not sure which tool to use. Try asking about weather, math, or scheduling a task.")
                    
        except (KeyboardInterrupt, EOFError):
            print("\nExiting agent loop. Goodbye!")
            break

if __name__ == "__main__":
    run_agent()
