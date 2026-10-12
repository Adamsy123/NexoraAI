import os
import subprocess
import webbrowser
import platform
import datetime
import pyautogui

def open_application(app_name: str):
    """Opens a common application or file path on the local system."""
    app_name = app_name.lower()
    try:
        if platform.system() == "Windows":
            if "notepad" in app_name:
                subprocess.Popen(["notepad.exe"])
            elif "calculator" in app_name:
                subprocess.Popen(["calc.exe"])
            elif "browser" in app_name or "chrome" in app_name:
                webbrowser.open("https://www.google.com")
            elif "explorer" in app_name or "files" in app_name:
                subprocess.Popen(["explorer.exe"])
            else:
                os.startfile(app_name)
        elif platform.system() == "Darwin":  # macOS
            subprocess.Popen(["open", "-a", app_name])
        else:  # Linux
            subprocess.Popen([app_name])
        return f"Successfully launched {app_name}."
    except Exception as e:
        return f"Failed to launch {app_name}: {str(e)}"

def search_web(query: str):
    """Opens default web browser and searches Google for the query."""
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    webbrowser.open(url)
    return f"Opened web search for: {query}"

def get_system_info():
    """Returns current system time and platform details."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"System: {platform.system()} {platform.release()}, Current Time: {now}"

def take_screenshot():
    """Takes a screenshot of the main monitor and saves it to the project folder."""
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        screenshot = pyautogui.screenshot()
        screenshot.save(filename)
        return f"Screenshot successfully taken and saved as {filename}."
    except Exception as e:
        return f"Failed to take screenshot: {str(e)}"

def list_directory(folder_path: str = "."):
    """Lists files and folders in the specified directory path."""
    try:
        items = os.listdir(folder_path)
        return f"Contents of {folder_path}: " + ", ".join(items[:20])
    except Exception as e:
        return f"Failed to list directory: {str(e)}"

def get_battery_status():
    """Checks the system battery percentage and charging status."""
    try:
        import psutil
        battery = psutil.sensors_battery()
        if battery is None:
            return "Battery status not available (desktop PC)."
        plugged = "plugged in" if battery.power_plugged else "on battery power"
        return f"Battery is at {battery.percent}% and {plugged}."
    except ImportError:
        return "psutil package is required for battery info."
    except Exception as e:
        return f"Could not retrieve battery status: {str(e)}"

# Tool definitions schema for OpenAI function calling
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": "Open a local application like notepad, calculator, or browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Name of the app (e.g. notepad, calculator, browser)"}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web on Google for information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": "Get current local time and system platform information.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Take a screenshot of the computer screen.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files in the current project directory.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_battery_status",
            "description": "Check the battery level and charging status of the laptop.",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

def execute_tool(name: str, arguments: dict):
    """Dispatcher for executing the requested tool function."""
    if name == "open_application":
        return open_application(**arguments)
    elif name == "search_web":
        return search_web(**arguments)
    elif name == "get_system_info":
        return get_system_info()
    elif name == "take_screenshot":
        return take_screenshot()
    elif name == "list_directory":
        return list_directory()
    elif name == "get_battery_status":
        return get_battery_status()
    return f"Unknown tool: {name}"