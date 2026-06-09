# Grabador Automático de Zoom para Linux (Wayland / GNOME)

Esta es una aplicación modular escrita en Python bajo el paradigma de **Programación Orientada a Objetos (POO)**. Permite automatizar la grabación de llamadas de Zoom (pantalla completa y audio mezclado) en entornos modernos de escritorio Linux basados en GNOME Shell y Wayland.

El script monitorea en segundo plano el estado de la aplicación Zoom, detecta de forma automática cuándo se inicia o finaliza una llamada/reunión, graba de forma silenciosa la pantalla y los audios (micrófono + altavoces de los participantes), y comprime todo al final de la llamada en un archivo de formato MP4, ahorrando hasta un 80% de tamaño de disco sin perder calidad de lectura en textos ni diapositivas compartidas.

---

## 📂 Estructura de Archivos del Proyecto

El proyecto está diseñado de manera modular y desacoplada para mantener archivos limpios y de pocas líneas:

*   **[main.py](file:///home/cristina/Documentos/grabarPantalla/main.py)**: Orquestador principal (`ZoomRecorderApp`) que corre en bucle e implementa el daemon de monitoreo de llamadas.
*   **[gui.py](file:///home/cristina/Documentos/grabarPantalla/gui.py)**: Interfaz gráfica de usuario (GUI) nativa en GTK 3 para controlar de forma visual la grabación, ver el temporizador en tiempo real y elegir el modo de grabación.
*   **[install.py](file:///home/cristina/Documentos/grabarPantalla/install.py)**: Script instalador que crea el acceso directo con icono en tu Escritorio y en el menú de aplicaciones del sistema.
*   **[detector.py](file:///home/cristina/Documentos/grabarPantalla/detector.py)**: Clase `ZoomDetector` que utiliza `xwininfo` para inspeccionar la existencia de ventanas activas de llamadas de Zoom.

*   **[video_recorder.py](file:///home/cristina/Documentos/grabarPantalla/video_recorder.py)**: Clase `VideoRecorder` que maneja el inicio y detención del motor de grabación de GNOME Shell mediante D-Bus.
*   **[audio_recorder.py](file:///home/cristina/Documentos/grabarPantalla/audio_recorder.py)**: Clase `AudioRecorder` que mezcla dinámicamente y graba en Opus el micrófono y los altavoces usando un pipeline de GStreamer.
*   **[processor.py](file:///home/cristina/Documentos/grabarPantalla/processor.py)**: Clase `MediaProcessor` encargada de invocar a FFmpeg para realizar el multiplexado y compresión óptima de los archivos.
*   **[config.py](file:///home/cristina/Documentos/grabarPantalla/config.py)**: Archivo central de configuraciones (rutas de guardado, tasa de fotogramas, factor de compresión, nombres).
*   **[recover.py](file:///home/cristina/Documentos/grabarPantalla/recover.py)**: Script auxiliar para recuperar, fusionar y comprimir grabaciones temporales si el proceso principal falla o se interrumpe antes del post-procesado.
*   **[PROYECTO.md](file:///home/cristina/Documentos/grabarPantalla/PROYECTO.md)**: Documento técnico de diseño, requerimientos y justificación de decisiones técnicas.


---

## 🛠️ Requisitos Previos e Instalación

Para que la aplicación pueda comunicarse con el bus D-Bus de GNOME, capturar y mezclar canales de audio de altavoces/micrófono, y realizar la compresión final del vídeo, requiere dependencias tanto a nivel de sistema operativo como de Python.

### 1. Instalación Recomendada (Gestor de paquetes del sistema)
En distribuciones basadas en Debian, Ubuntu o Zorin OS, la forma más rápida y estable es utilizar `apt` para instalar directamente las dependencias de Python ya empaquetadas por el sistema:

```bash
sudo apt update
sudo apt install python3-dbus python3-gi gstreamer1.0-plugins-good gstreamer1.0-plugins-base gstreamer1.0-plugins-bad ffmpeg x11-utils
```

### 2. Instalación Alternativa (Pip y requirements.txt)
Si prefieres usar un entorno virtual de Python (`venv`) o instalar las librerías mediante `pip`, hemos generado el archivo **[requirements.txt](file:///home/cristina/Documentos/grabarPantalla/requirements.txt)**.

Debido a que `dbus-python` y `PyGObject` son extensiones en C nativas, su instalación por `pip` requiere compilar código fuente. Tienes dos maneras de resolver esto:

#### Método A: Reutilizar paquetes del sistema (Recomendado y más fácil)
Puedes crear el entorno virtual indicándole que herede las librerías del sistema operativo. Esto evita tener que compilar nada:
1. Instala los paquetes oficiales en el sistema:
   ```bash
   sudo apt install python3-dbus python3-gi
   ```
2. Crea el entorno virtual usando la bandera `--system-site-packages`:
   ```bash
   python3 -m venv --system-site-packages .venv
   ```
3. Activa tu entorno y ejecuta el script directamente.

#### Método B: Instalar herramientas de compilación
Si deseas compilar las librerías de forma aislada dentro de tu entorno virtual tradicional, debes instalar primero el compilador C (`gcc` y `make`), los archivos de cabeceras de desarrollo de Python (`python3-dev`), y los archivos de cabeceras de desarrollo de tu sistema:
```bash
sudo apt update
sudo apt install build-essential python3-dev libdbus-1-dev libglib2.0-dev
```
Una vez instalado lo anterior, ejecuta el comando original:
```bash
pip install -r requirements.txt
```



### 📋 Detalle de las Dependencias del Sistema
*   `python3-dbus` o `dbus-python` (Pip): Permite interactuar con la API de grabación de pantalla de GNOME Shell.
*   `python3-gi` o `PyGObject` (Pip): Enlace nativo con las librerías GLib/GObject necesarias para ejecutar el motor de audio GStreamer.
*   `gstreamer1.0-plugins-*`: Complementos de GStreamer para capturar audio desde PulseAudio (`pulsesrc`), mezclar los canales (`audiomixer`) y codificar a Opus.
*   `ffmpeg`: Motor multimedia externo encargado de unir las pistas de audio/vídeo y realizar la compresión avanzada final.
*   `x11-utils`: Proporciona la utilidad `xwininfo` para monitorear las ventanas de Zoom de manera ultra-ligera y sin consumo de recursos.


---

## 🖥️ Interfaz Gráfica (GUI) e Instalador

Si prefieres controlar tus grabaciones de forma visual mediante botones y ver un temporizador en tiempo real en vez de usar la terminal, el proyecto cuenta con una interfaz gráfica nativa en **GTK 3**.

### 1. Instalar el Lanzador en tu Escritorio y Menú
Hemos preparado un instalador automatizado que te creará un acceso directo con icono tanto en tu Escritorio como en el menú principal de aplicaciones de Zorin OS.

Ejecuta el instalador desde la carpeta del proyecto:
```bash
python3 install.py
```

Esto generará el lanzador **Grabador de Zoom** en:
1.  Tu **Escritorio** (`~/Escritorio/grabador-zoom.desktop`).
2.  Tu **Menú de Aplicaciones** (buscador de sistema de Zorin/GNOME).

### 2. Ejecutar la Interfaz Gráfica
Puedes abrir la interfaz simplemente haciendo doble clic en el icono del **Grabador de Zoom** en tu escritorio (o buscándolo en tu menú) o ejecutándola desde terminal:
```bash
python3 gui.py
```

*   **Uso de la GUI**:
    *   **Selecciona el modo**: Marca "Automático" (para que espere a que empiece una reunión de Zoom) o "Manual" (para capturar la pantalla completa en el acto).
    *   **Grabar**: Haz clic en el botón **Grabar** (se iluminará en verde/azul). El temporizador empezará a correr en formato `HH:MM:SS`.
    *   **Detener**: Haz clic en el botón **Detener** (rojo). Detendrá los grabadores en segundo plano de forma inmediata y realizará el multiplexado y compresión pesados en un hilo secundario (evitando congelar la aplicación). Al terminar, te notificará que el archivo `.mp4` se ha guardado correctamente.

---

## 🚀 Cómo Ejecutar la Aplicación (Modo Terminal)


1.  Abre una terminal y colócate en la carpeta del script:
    ```bash
    cd /home/cristina/Documentos/grabarPantalla
    ```
2.  Inicia la aplicación:
    ```bash
    python3 main.py
    ```

3.  **Selección de Modo al Iniciar**:
    Al iniciar el script, se presentará un menú interactivo en la terminal con dos opciones:
    
    *   **Opción 1: Grabación automática al detectar llamadas de Zoom (Daemon)**  
        El detector esperará en segundo plano a que se abra la ventana de una llamada de Zoom. Cuando se detecte, iniciará la grabación (pantalla + audio mixto de micrófono y altavoces) de forma automática y silenciosa. Al colgar o cerrar la llamada, guardará y comprimirá el archivo de forma automática, volviendo a quedar a la espera de una nueva llamada.
        
    *   **Opción 2: Grabación manual de pantalla completa e inmediata**  
        Iniciará de inmediato la grabación de la pantalla completa y el audio de tu sistema/micrófono. Mostrará un aviso y grabará indefinidamente hasta que presiones `ENTER` (o `Ctrl + C`) en la terminal, momento en el cual detendrá la grabación y procesará el archivo comprimido final.

4.  **Parámetros por línea de comandos (atajos)**:
    Si no deseas interactuar con el menú inicial, puedes iniciar directamente en el modo preferido usando las banderas de la terminal:
    *   Para iniciar directamente en **modo automático (Zoom)**:
        ```bash
        python3 main.py --auto   # o -a
        ```
    *   Para iniciar directamente en **modo manual (pantalla completa inmediata)**:
        ```bash
        python3 main.py --manual # o -m
        ```

5.  **Interrupción Limpia**:
    Puedes detener el script de forma segura en cualquier momento usando `Ctrl + C`. Si la grabación estaba activa (tanto en modo automático como manual), el script detendrá los grabadores y procesará los archivos capturados hasta ese momento para asegurar que no se pierda la grabación en curso.


---

## ⚙️ Configuración Personalizada

Puedes abrir el archivo **[config.py](file:///home/cristina/Documentos/grabarPantalla/config.py)** para cambiar parámetros de funcionamiento según tus necesidades de almacenamiento o rendimiento:

```python
# Directorio donde se guardarán las grabaciones finales
OUTPUT_DIR = "/home/cristina/Documentos/Zoom"

# Calidad y compresión (CRF: 18-28. Mayor CRF = Menor peso de archivo)
VIDEO_CRF = 24

# FPS del vídeo final (10fps es ideal para lectura de texto y diapositivas)
VIDEO_FRAMERATE = 10
```
