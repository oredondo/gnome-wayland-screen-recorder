import os
import sys
import subprocess
import shutil

def install():
    print("=========================================================")
    print("           Zoom & Screen Recorder Installer              ")
    print("=========================================================")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    gui_path = os.path.join(script_dir, "gui.py")
    
    # Check dependencies
    print("\n[1/3] Checking dependencies...")
    
    missing_packages = []
    # Check PyGObject (GTK 3)
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk
        print("  - Gtk 3.0: OK")
    except (ImportError, ValueError):
        missing_packages.append("python3-gi")
        print("  - Gtk 3.0: Not found")
        
    # Check Python DBus
    try:
        import dbus
        print("  - D-Bus: OK")
    except ImportError:
        missing_packages.append("python3-dbus")
        print("  - D-Bus: Not found")
        
    # Check FFmpeg
    ffmpeg_found = shutil.which("ffmpeg") is not None
    if ffmpeg_found:
        print("  - FFmpeg: OK")
    else:
        print("  - FFmpeg: Not found")
        
    # Check xwininfo
    xwininfo_found = shutil.which("xwininfo") is not None
    if xwininfo_found:
        print("  - xwininfo: OK")
    else:
        print("  - xwininfo: Not found")
        
    if missing_packages or not ffmpeg_found or not xwininfo_found:
        print("\n[WARNING] System dependencies are missing.")
        print("For the application to function correctly, please install the following:")
        sys_install_cmd = "sudo apt update && sudo apt install "
        pkgs = []
        if "python3-gi" in missing_packages: pkgs.extend(["python3-gi", "gstreamer1.0-plugins-good", "gstreamer1.0-plugins-base", "gstreamer1.0-plugins-bad"])
        if "python3-dbus" in missing_packages: pkgs.append("python3-dbus")
        if not ffmpeg_found: pkgs.append("ffmpeg")
        if not xwininfo_found: pkgs.append("x11-utils")
        
        print(f"        {sys_install_cmd}{' '.join(pkgs)}")
        
        confirm = input("\nDo you wish to continue creating the launcher shortcut anyway? (y/N): ").strip().lower()
        if confirm not in ("y", "yes", "s", "si"):
            print("Installation canceled.")
            return
            
    # Create Desktop Launcher
    print("\n[2/3] Creating Desktop launcher...")
    
    desktop_dir_es = os.path.expanduser("~/Escritorio")
    desktop_dir_en = os.path.expanduser("~/Desktop")
    
    desktop_dir = desktop_dir_es if os.path.exists(desktop_dir_es) else desktop_dir_en
    if not os.path.exists(desktop_dir):
        print(f"  - Desktop directory not found. Creating: {desktop_dir}")
        os.makedirs(desktop_dir, exist_ok=True)
        
    venv_python = os.path.join(script_dir, ".venv", "bin", "python")
    python_bin = venv_python if os.path.exists(venv_python) else sys.executable

    desktop_entry = f"""[Desktop Entry]
Name=Zoom & Screen Recorder
Comment=Automatically record full screen or Zoom calls
Exec={python_bin} {gui_path}
Path={script_dir}
Icon=video-display
Terminal=false
Type=Application
Categories=Utility;AudioVideo;
StartupNotify=true
"""
    
    try:
        with open(launcher_path, "w") as f:
            f.write(desktop_entry)
        print(f"  - Created file: {launcher_path}")
        
        # Make executable
        os.chmod(launcher_path, 0o755)  # nosec B103
        print("  - Execution permissions granted.")
        
        # Trust the desktop file (removes warning in GNOME/Zorin OS)
        subprocess.run(["gio", "set", launcher_path, "metadata::trusted", "yes"], stderr=subprocess.DEVNULL)
        print("  - Marked launcher as trusted in the system.")
        
    except Exception as e:
        print(f"  - [ERROR] Failed to create launcher on Desktop: {e}")
        
    # Create Applications Menu Entry
    print("\n[3/3] Adding application to the system menu...")
    menu_dir = os.path.expanduser("~/.local/share/applications")
    os.makedirs(menu_dir, exist_ok=True)
    menu_launcher_path = os.path.join(menu_dir, "grabador-zoom.desktop")
    
    try:
        with open(menu_launcher_path, "w") as f:
            f.write(desktop_entry)
        print(f"  - Created menu shortcut: {menu_launcher_path}")
        os.chmod(menu_launcher_path, 0o755)  # nosec B103
    except Exception as e:
        print(f"  - [ERROR] Failed to create menu shortcut: {e}")
        
    print("\n=========================================================")
    print("      INSTALLATION COMPLETED SUCCESSFULLY!               ")
    print("=========================================================")
    print(f"The launcher shortcut is now available on your Desktop")
    print(f"and in the applications menu of Zorin OS / GNOME.")
    print("=========================================================\n")

if __name__ == "__main__":
    install()
