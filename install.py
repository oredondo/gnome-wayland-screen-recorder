import os
import sys
import subprocess
import shutil

def install():
    print("=========================================================")
    print("       Instalador del Grabador de Pantalla y Zoom       ")
    print("=========================================================")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    gui_path = os.path.join(script_dir, "gui.py")
    
    # Check dependencies
    print("\n[1/3] Verificando dependencias...")
    
    missing_packages = []
    # Check PyGObject (GTK 3)
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk
        print("  - Gtk 3.0: OK")
    except (ImportError, ValueError):
        missing_packages.append("python3-gi")
        print("  - Gtk 3.0: No encontrado")
        
    # Check Python DBus
    try:
        import dbus
        print("  - D-Bus: OK")
    except ImportError:
        missing_packages.append("python3-dbus")
        print("  - D-Bus: No encontrado")
        
    # Check FFmpeg
    ffmpeg_found = shutil.which("ffmpeg") is not None
    if ffmpeg_found:
        print("  - FFmpeg: OK")
    else:
        print("  - FFmpeg: No encontrado")
        
    # Check xwininfo
    xwininfo_found = shutil.which("xwininfo") is not None
    if xwininfo_found:
        print("  - xwininfo: OK")
    else:
        print("  - xwininfo: No encontrado")
        
    if missing_packages or not ffmpeg_found or not xwininfo_found:
        print("\n[AVISO] Faltan dependencias en el sistema.")
        print("Para que la aplicación funcione correctamente, por favor instala lo siguiente:")
        sys_install_cmd = "sudo apt update && sudo apt install "
        pkgs = []
        if "python3-gi" in missing_packages: pkgs.extend(["python3-gi", "gstreamer1.0-plugins-good", "gstreamer1.0-plugins-base", "gstreamer1.0-plugins-bad"])
        if "python3-dbus" in missing_packages: pkgs.append("python3-dbus")
        if not ffmpeg_found: pkgs.append("ffmpeg")
        if not xwininfo_found: pkgs.append("x11-utils")
        
        print(f"        {sys_install_cmd}{' '.join(pkgs)}")
        
        confirm = input("\n¿Deseas continuar con la creación del lanzador a pesar de esto? (S/n): ").strip().lower()
        if confirm not in ("", "s", "si", "yes"):
            print("Instalación cancelada.")
            return
            
    # Create Desktop Launcher
    print("\n[2/3] Creando lanzador en el Escritorio...")
    
    desktop_dir_es = os.path.expanduser("~/Escritorio")
    desktop_dir_en = os.path.expanduser("~/Desktop")
    
    desktop_dir = desktop_dir_es if os.path.exists(desktop_dir_es) else desktop_dir_en
    if not os.path.exists(desktop_dir):
        print(f"  - No se encontró directorio de Escritorio. Se creará: {desktop_dir}")
        os.makedirs(desktop_dir, exist_ok=True)
        
    launcher_path = os.path.join(desktop_dir, "grabador-zoom.desktop")
    
    desktop_entry = f"""[Desktop Entry]
Name=Grabador de Zoom
Comment=Graba la pantalla completa o llamadas de Zoom de forma automática
Exec=python3 {gui_path}
Icon=video-display
Terminal=false
Type=Application
Categories=Utility;AudioVideo;
StartupNotify=true
"""
    
    try:
        with open(launcher_path, "w") as f:
            f.write(desktop_entry)
        print(f"  - Creado archivo: {launcher_path}")
        
        # Make executable
        os.chmod(launcher_path, 0o755)
        print("  - Permisos de ejecución otorgados.")
        
        # Trust the desktop file (removes warning in GNOME/Zorin OS)
        subprocess.run(["gio", "set", launcher_path, "metadata::trusted", "yes"], stderr=subprocess.DEVNULL)
        print("  - Marcado como lanzador de confianza en el sistema.")
        
    except Exception as e:
        print(f"  - [ERROR] Falló crear lanzador en Escritorio: {e}")
        
    # Create Applications Menu Entry
    print("\n[3/3] Añadiendo la aplicación al menú de inicio (Aplicaciones)...")
    menu_dir = os.path.expanduser("~/.local/share/applications")
    os.makedirs(menu_dir, exist_ok=True)
    menu_launcher_path = os.path.join(menu_dir, "grabador-zoom.desktop")
    
    try:
        with open(menu_launcher_path, "w") as f:
            f.write(desktop_entry)
        print(f"  - Creado acceso en menú: {menu_launcher_path}")
        os.chmod(menu_launcher_path, 0o755)
    except Exception as e:
        print(f"  - [ERROR] Falló crear acceso en menú: {e}")
        
    print("\n=========================================================")
    print("      ¡INSTALACIÓN COMPLETADA CON ÉXITO!                ")
    print("=========================================================")
    print(f"El acceso directo está disponible en tu Escritorio y en")
    print(f"el menú de aplicaciones de Zorin OS / GNOME.")
    print("=========================================================\n")

if __name__ == "__main__":
    install()
