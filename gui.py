import os
import sys
import glob

# Auto-inject project's .venv site-packages into sys.path if launched with system python
_proj_root = os.path.dirname(os.path.abspath(__file__))
_venv_sites = glob.glob(os.path.join(_proj_root, ".venv", "lib", "python3.*", "site-packages"))
for _sp in _venv_sites:
    if _sp not in sys.path:
        sys.path.insert(0, _sp)

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Pango
import logging
import time
import threading
from datetime import datetime

import config
from detector import ZoomDetector
from video_recorder import VideoRecorder
from audio_recorder import AudioRecorder
from processor import MediaProcessor

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(config.LOG_FILE)
    ]
)
logger = logging.getLogger("ZoomRecorderGUI")

class ZoomRecorderGUI(Gtk.Window):
    """Native GTK 3 Graphical User Interface for Zoom and Screen Recorder with EIR Notes pipeline."""
    
    def __init__(self):
        super().__init__(title="Zoom & Screen Recorder")
        self.set_default_size(460, 420)
        self.set_resizable(True)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # Initialize Core Logic
        self.detector = ZoomDetector()
        self.processor = MediaProcessor()
        self.video_recorder = None
        self.audio_recorder = None
        
        self.is_recording = False
        self.is_waiting_zoom = False
        self.is_processing = False
        self.is_running_pipeline = False
        self.is_running_handwritten = False
        self.selected_handwritten_images = []
        self.recording_start_time = None
        
        # Timer and Polling Sources
        self.timer_timeout_id = None
        self.zoom_poll_timeout_id = None
        
        # Build UI Components
        self.build_ui()
        
        # Window Close Events
        self.connect("delete-event", self.on_delete_event)
        self.connect("destroy", self.on_destroy)
        
    def build_ui(self):
        # HeaderBar (GNOME Native Style)
        hb = Gtk.HeaderBar()
        hb.set_show_close_button(True)
        hb.props.title = "Zoom & Screen Recorder"
        hb.props.subtitle = "EIR Apuntes y Memorización"
        self.set_titlebar(hb)
        
        # Notebook for Tabs
        self.notebook = Gtk.Notebook()
        self.add(self.notebook)
        
        # ==================== TAB 1: RECORDER ====================
        recorder_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        recorder_box.set_margin_start(20)
        recorder_box.set_margin_end(20)
        recorder_box.set_margin_top(20)
        recorder_box.set_margin_bottom(20)
        
        # Mode Selection Group
        mode_frame = Gtk.Frame(label="Recording Mode")
        mode_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        mode_box.set_margin_start(15)
        mode_box.set_margin_end(15)
        mode_box.set_margin_top(10)
        mode_box.set_margin_bottom(10)
        mode_frame.add(mode_box)
        recorder_box.pack_start(mode_frame, False, False, 0)
        
        self.radio_auto = Gtk.RadioButton.new_with_label_from_widget(None, "Automatic (Detect Zoom)")
        self.radio_manual = Gtk.RadioButton.new_with_label_from_widget(self.radio_auto, "Manual (Record Full Screen)")
        mode_box.pack_start(self.radio_auto, False, False, 0)
        mode_box.pack_start(self.radio_manual, False, False, 0)
        
        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        recorder_box.pack_start(sep, False, False, 0)
        
        # Display Box (Timer and Status)
        display_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        recorder_box.pack_start(display_box, True, True, 0)
        
        # Large Digital Timer Label
        self.timer_label = Gtk.Label(label="00:00:00")
        self.timer_label.modify_font(Pango.FontDescription("monospace bold 28"))
        display_box.pack_start(self.timer_label, True, True, 0)
        
        # Status Label
        self.status_label = Gtk.Label(label="Ready to record")
        self.status_label.modify_font(Pango.FontDescription("italic 10"))
        display_box.pack_start(self.status_label, False, False, 0)
        
        # Progress Bar (Compression)
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_text("")
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_no_show_all(True)
        self.progress_bar.hide()
        display_box.pack_start(self.progress_bar, False, False, 5)
        
        # Buttons Box
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        btn_box.set_homogeneous(True)
        recorder_box.pack_start(btn_box, False, False, 0)
        
        # Record Button
        self.btn_record = Gtk.Button(label="Record")
        self.btn_record.get_style_context().add_class("suggested-action")
        self.btn_record.connect("clicked", self.on_record_clicked)
        btn_box.pack_start(self.btn_record, True, True, 0)
        
        # Stop Button
        self.btn_stop = Gtk.Button(label="Stop")
        self.btn_stop.get_style_context().add_class("destructive-action")
        self.btn_stop.set_sensitive(False)
        self.btn_stop.connect("clicked", self.on_stop_clicked)
        btn_box.pack_start(self.btn_stop, True, True, 0)
        
        self.notebook.append_page(recorder_box, Gtk.Label(label="Grabador"))
        
        # ==================== TAB 2: EIR NOTES PIPELINE ====================
        pipeline_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        pipeline_box.set_margin_start(20)
        pipeline_box.set_margin_end(20)
        pipeline_box.set_margin_top(20)
        pipeline_box.set_margin_bottom(20)
        
        # Title
        pipe_title = Gtk.Label()
        pipe_title.set_markup("<b>Generación de Apuntes y Anki</b>")
        pipe_title.modify_font(Pango.FontDescription("bold 12"))
        pipeline_box.pack_start(pipe_title, False, False, 5)
        
        # File selection grid
        grid = Gtk.Grid(row_spacing=10, column_spacing=15)
        grid.set_column_homogeneous(False)
        pipeline_box.pack_start(grid, False, False, 5)
        
        # Video Selector
        lbl_video = Gtk.Label(label="Archivo de Vídeo (.mp4):")
        lbl_video.set_xalign(0)
        self.video_chooser = Gtk.FileChooserButton(title="Seleccionar Vídeo (.mp4)", action=Gtk.FileChooserAction.OPEN)
        filter_mp4 = Gtk.FileFilter()
        filter_mp4.set_name("Archivos MP4 (*.mp4)")
        filter_mp4.add_pattern("*.mp4")
        self.video_chooser.add_filter(filter_mp4)
        self.video_chooser.connect("file-set", self.on_video_file_set)
        
        grid.attach(lbl_video, 0, 0, 1, 1)
        grid.attach(self.video_chooser, 1, 0, 1, 1)
        self.video_chooser.set_hexpand(True)
        
        # Audio Selector
        lbl_audio = Gtk.Label(label="Archivo de Audio (.mp3):")
        lbl_audio.set_xalign(0)
        self.audio_chooser = Gtk.FileChooserButton(title="Seleccionar Audio (.mp3)", action=Gtk.FileChooserAction.OPEN)
        filter_mp3 = Gtk.FileFilter()
        filter_mp3.set_name("Archivos MP3 (*.mp3)")
        filter_mp3.add_pattern("*.mp3")
        self.audio_chooser.add_filter(filter_mp3)
        
        grid.attach(lbl_audio, 0, 1, 1, 1)
        grid.attach(self.audio_chooser, 1, 1, 1, 1)
        
        # Separator
        pipe_sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        pipeline_box.pack_start(pipe_sep, False, False, 5)
        
        # Pipeline Display Area
        pipe_display = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        pipeline_box.pack_start(pipe_display, True, True, 0)
        
        # Checkbox for optional Anki cards
        self.chk_anki = Gtk.CheckButton(label="Generar tarjetas de memorización para Anki")
        import pipeline_config
        self.chk_anki.set_active(getattr(pipeline_config, "GENERATE_ANKI", True))
        pipe_display.pack_start(self.chk_anki, False, False, 5)
        
        # Pipeline Status Label
        self.pipeline_status_label = Gtk.Label(label="Selecciona los archivos y presiona Generar")
        self.pipeline_status_label.set_line_wrap(True)
        self.pipeline_status_label.set_justify(Gtk.Justification.CENTER)
        self.pipeline_status_label.modify_font(Pango.FontDescription("monospace bold 10"))
        pipe_display.pack_start(self.pipeline_status_label, True, True, 0)
        
        # Pipeline Progress Bar
        self.pipeline_progress_bar = Gtk.ProgressBar()
        self.pipeline_progress_bar.set_text("")
        self.pipeline_progress_bar.set_show_text(True)
        self.pipeline_progress_bar.set_no_show_all(True)
        self.pipeline_progress_bar.hide()
        pipe_display.pack_start(self.pipeline_progress_bar, False, False, 5)
        
        # Generate Button
        self.btn_generate = Gtk.Button(label="Generar Apuntes y Anki")
        self.btn_generate.get_style_context().add_class("suggested-action")
        self.btn_generate.connect("clicked", self.on_generate_clicked)
        pipeline_box.pack_start(self.btn_generate, False, False, 0)
        
        self.notebook.append_page(pipeline_box, Gtk.Label(label="Apuntes EIR"))
        
        # ==================== TAB 3: HANDWRITTEN NOTES ====================
        handwritten_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        handwritten_box.set_margin_start(20)
        handwritten_box.set_margin_end(20)
        handwritten_box.set_margin_top(20)
        handwritten_box.set_margin_bottom(20)
        
        # Title
        hw_title = Gtk.Label()
        hw_title.set_markup("<b>Digitalización de Apuntes Manuscritos</b>")
        hw_title.modify_font(Pango.FontDescription("bold 12"))
        handwritten_box.pack_start(hw_title, False, False, 5)
        
        # Subtitle / Description
        hw_desc = Gtk.Label(label="Convierte fotos de apuntes manuscritos a Markdown (.md) respetando exactamente la información original.")
        hw_desc.set_line_wrap(True)
        hw_desc.set_justify(Gtk.Justification.CENTER)
        hw_desc.modify_font(Pango.FontDescription("italic 9"))
        handwritten_box.pack_start(hw_desc, False, False, 0)
        
        # File selector box
        hw_file_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        handwritten_box.pack_start(hw_file_box, False, False, 5)
        
        self.btn_select_images = Gtk.Button(label="Seleccionar Fotos de Apuntes (.jpg, .png...)")
        self.btn_select_images.connect("clicked", self.on_select_images_clicked)
        hw_file_box.pack_start(self.btn_select_images, False, False, 0)
        
        self.lbl_handwritten_count = Gtk.Label(label="0 imágenes seleccionadas")
        self.lbl_handwritten_count.modify_font(Pango.FontDescription("monospace 9"))
        hw_file_box.pack_start(self.lbl_handwritten_count, False, False, 0)
        
        # Separator
        hw_sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        handwritten_box.pack_start(hw_sep, False, False, 5)
        
        # Display Area
        hw_display = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        handwritten_box.pack_start(hw_display, True, True, 0)
        
        # Handwritten Status Label
        self.handwritten_status_label = Gtk.Label(label="Selecciona las fotos manuscritas y presiona Generar")
        self.handwritten_status_label.set_line_wrap(True)
        self.handwritten_status_label.set_justify(Gtk.Justification.CENTER)
        self.handwritten_status_label.modify_font(Pango.FontDescription("monospace bold 10"))
        hw_display.pack_start(self.handwritten_status_label, True, True, 0)
        
        # Handwritten Progress Bar
        self.handwritten_progress_bar = Gtk.ProgressBar()
        self.handwritten_progress_bar.set_text("")
        self.handwritten_progress_bar.set_show_text(True)
        self.handwritten_progress_bar.set_no_show_all(True)
        self.handwritten_progress_bar.hide()
        hw_display.pack_start(self.handwritten_progress_bar, False, False, 5)
        
        # Generate Handwritten Button
        self.btn_generate_handwritten = Gtk.Button(label="Generar Markdown Manuscrito")
        self.btn_generate_handwritten.get_style_context().add_class("suggested-action")
        self.btn_generate_handwritten.connect("clicked", self.on_generate_handwritten_clicked)
        handwritten_box.pack_start(self.btn_generate_handwritten, False, False, 0)
        
        self.notebook.append_page(handwritten_box, Gtk.Label(label="Manuscritos"))
        
    # ==================== RECORDER HANDLERS ====================
    def on_record_clicked(self, widget):
        self.radio_auto.set_sensitive(False)
        self.radio_manual.set_sensitive(False)
        self.btn_record.set_sensitive(False)
        self.btn_stop.set_sensitive(True)
        self.notebook.set_show_tabs(False) # Prevent switching tabs while recording
        
        if self.radio_manual.get_active():
            self.status_label.set_text("Starting manual recording...")
            if self.start_recording_session():
                self.status_label.set_text("Recording full screen...")
        else:
            self.is_waiting_zoom = True
            self.status_label.set_text("Waiting for Zoom call...")
            self.zoom_poll_timeout_id = GLib.timeout_add_seconds(config.POLLING_INTERVAL, self.poll_zoom_status)
            
    def on_stop_clicked(self, widget):
        self.btn_stop.set_sensitive(False)
        
        if self.is_waiting_zoom and not self.is_recording:
            logger.info("Zoom waiting canceled by user.")
            if self.zoom_poll_timeout_id:
                GLib.source_remove(self.zoom_poll_timeout_id)
                self.zoom_poll_timeout_id = None
            self.is_waiting_zoom = False
            self.reset_ui_state("Recording canceled")
        else:
            self.status_label.set_text("Processing and compressing recording...")
            self.stop_recording_session_and_process()
            
    def start_recording_session(self) -> bool:
        video_temp_template = f"temp_zoom_video_{int(time.time())}"
        audio_temp_path = os.path.join(config.TEMP_DIR, f"temp_zoom_audio_{int(time.time())}.ogg")
        
        try:
            self.video_recorder = VideoRecorder(filename_template=video_temp_template)
            self.audio_recorder = AudioRecorder(output_path=audio_temp_path)
            
            if not self.video_recorder.start():
                self.reset_ui_state("Error: Video recorder failed")
                return False
                
            if not self.audio_recorder.start():
                self.video_recorder.stop()
                self.reset_ui_state("Error: Audio recorder failed")
                return False
                
            self.is_recording = True
            self.recording_start_time = datetime.now()
            self.timer_timeout_id = GLib.timeout_add_seconds(1, self.update_timer)
            return True
            
        except Exception as e:
            logger.error(f"Error starting recording session: {e}")
            self.reset_ui_state("Error starting recorders")
            return False
            
        return True
        
    def stop_recording_session_and_process(self):
        if not self.is_recording:
            return
            
        self.is_recording = False
        
        if self.timer_timeout_id:
            GLib.source_remove(self.timer_timeout_id)
            self.timer_timeout_id = None
            
        if self.zoom_poll_timeout_id:
            GLib.source_remove(self.zoom_poll_timeout_id)
            self.zoom_poll_timeout_id = None
            
        video_file = self.video_recorder.stop() if self.video_recorder else None
        audio_file = self.audio_recorder.stop() if self.audio_recorder else None
        
        logger.info("Recording stopped. Spawning merge and compression thread...")
        
        self.is_processing = True
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_text("Initializing compression...")
        self.progress_bar.show()
        
        threading.Thread(
            target=self.merge_and_compress_worker,
            args=(video_file, audio_file),
            daemon=True
        ).start()
        
    def merge_and_compress_worker(self, video_file: str, audio_file: str):
        time.sleep(2.0)
        
        if not video_file or not os.path.exists(video_file) or not audio_file or not os.path.exists(audio_file):
            GLib.idle_add(self.on_processing_complete, False, "Temporary files not found")
            return
            
        now = datetime.now()
        filename = f"{now.strftime(config.FILENAME_FORMAT)}.mp4"
        output_path = os.path.join(config.OUTPUT_DIR, filename)
        
        def progress_cb(progress):
            GLib.idle_add(self.update_progress, progress)
            
        success = self.processor.merge_and_compress(video_file, audio_file, output_path, progress_callback=progress_cb)
        GLib.idle_add(self.on_processing_complete, success, filename if success else "FFmpeg error")
        
    def update_progress(self, progress: float):
        self.progress_bar.set_fraction(progress)
        percentage = int(progress * 100)
        self.progress_bar.set_text(f"Compressing... {percentage}%")
        
    def on_processing_complete(self, success: bool, info: str):
        self.is_processing = False
        self.progress_bar.hide()
        self.notebook.set_show_tabs(True)
        if success:
            logger.info(f"Processing complete: {info}")
            self.reset_ui_state(f"Recording saved: {info}")
        else:
            logger.error(f"Processing failed: {info}")
            self.reset_ui_state(f"Error: {info}")
            
    def poll_zoom_status(self) -> bool:
        if not self.is_waiting_zoom:
            return False
            
        meeting_active = self.detector.is_meeting_active()
        
        if meeting_active and not self.is_recording:
            logger.info("Zoom call detected by GUI poll!")
            self.status_label.set_text("Recording Zoom call...")
            self.start_recording_session()
        elif not meeting_active and self.is_recording:
            logger.info("Zoom call ended. Stopping GUI recording...")
            self.status_label.set_text("Call ended. Compressing...")
            self.stop_recording_session_and_process()
            self.is_waiting_zoom = True
            
        return True
        
    def update_timer(self) -> bool:
        if not self.is_recording or not self.recording_start_time:
            return False
            
        delta = datetime.now() - self.recording_start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        timer_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.timer_label.set_text(timer_str)
        return True
        
    def reset_ui_state(self, status_text: str):
        self.radio_auto.set_sensitive(True)
        self.radio_manual.set_sensitive(True)
        self.btn_record.set_sensitive(True)
        self.btn_stop.set_sensitive(False)
        self.status_label.set_text(status_text)
        self.timer_label.set_text("00:00:00")
        
        self.is_recording = False
        self.is_waiting_zoom = False
        self.is_processing = False
        self.notebook.set_show_tabs(True)

    # ==================== TAB 2: PIPELINE HANDLERS ====================
    def on_video_file_set(self, widget):
        """Automatically infers and selects corresponding MP3 if available."""
        video_path = widget.get_filename()
        if not video_path:
            return
            
        # Infer mp3 path (replacing suffix or using same base)
        base, _ = os.path.splitext(video_path)
        audio_path = base + ".mp3"
        
        if os.path.exists(audio_path):
            logger.info(f"Auto-selected matching audio: {audio_path}")
            self.audio_chooser.set_filename(audio_path)
            
    def on_generate_clicked(self, widget):
        video = self.video_chooser.get_filename()
        audio = self.audio_chooser.get_filename()
        
        if not video or not audio:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Faltan archivos por seleccionar"
            )
            dialog.format_secondary_text("Por favor, selecciona tanto el archivo de vídeo (.mp4) como el de audio (.mp3) antes de continuar.")
            dialog.run()
            dialog.destroy()
            return
            
        # Disable tab controls and generation button
        anki_enabled = self.chk_anki.get_active()
        self.btn_generate.set_sensitive(False)
        self.video_chooser.set_sensitive(False)
        self.audio_chooser.set_sensitive(False)
        self.chk_anki.set_sensitive(False)
        self.notebook.set_show_tabs(False)
        self.is_running_pipeline = True
        
        # Show progress bar
        self.pipeline_progress_bar.set_fraction(0.0)
        self.pipeline_progress_bar.set_text("Iniciando análisis...")
        self.pipeline_progress_bar.show()
        
        # Spin thread for background pipeline execution
        threading.Thread(
            target=self.pipeline_worker,
            args=(video, audio, anki_enabled),
            daemon=True
        ).start()
        
    def pipeline_worker(self, video_path: str, audio_path: str, anki_enabled: bool):
        """Worker thread to run notes and Anki cards generation."""
        def progress_cb(message, progress):
            GLib.idle_add(self.update_pipeline_ui, message, progress)
            
        try:
            from pipeline.generate_notes import NotesGenerator
            generator = NotesGenerator(video_path, audio_path, generate_anki=anki_enabled)
            # Run the generator
            notes_path, anki_path = generator.run(status_callback=progress_cb)
            if anki_path:
                status_msg = "¡Apuntes y Anki generados con éxito!"
            else:
                status_msg = "¡Apuntes generados con éxito! (Tarjetas de Anki omitidas)"
            GLib.idle_add(self.on_pipeline_complete, True, status_msg)
        except Exception as e:
            logger.exception("Pipeline failed in GUI:")
            GLib.idle_add(self.on_pipeline_complete, False, f"Error: {str(e)}")
            
    def update_pipeline_ui(self, message: str, progress: float):
        """Called on GTK idle loop to update progress and status."""
        self.pipeline_status_label.set_text(message)
        self.pipeline_progress_bar.set_fraction(progress)
        percentage = int(progress * 100)
        self.pipeline_progress_bar.set_text(f"Progreso: {percentage}%")
        
    def on_pipeline_complete(self, success: bool, status_text: str):
        """Re-enables controls and resets state after completion."""
        self.is_running_pipeline = False
        self.pipeline_progress_bar.hide()
        self.notebook.set_show_tabs(True)
        
        self.btn_generate.set_sensitive(True)
        self.video_chooser.set_sensitive(True)
        self.audio_chooser.set_sensitive(True)
        self.chk_anki.set_sensitive(True)
        
        self.pipeline_status_label.set_text(status_text)
        
        # Reset file choosers
        self.video_chooser.unselect_all()
        self.audio_chooser.unselect_all()
        
        # Pop notification message
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO if success else Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Proceso Completado" if success else "Error de Procesamiento"
        )
        dialog.format_secondary_text(status_text)
        dialog.run()
        dialog.destroy()
        
    # ==================== TAB 3: HANDWRITTEN HANDLERS ====================
    def on_select_images_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Seleccionar Fotografías de Apuntes",
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.ACCEPT
        )
        dialog.set_select_multiple(True)
        
        filter_images = Gtk.FileFilter()
        filter_images.set_name("Imágenes (*.jpg, *.png, *.heic, *.webp...)")
        filter_images.add_pattern("*.jpg")
        filter_images.add_pattern("*.jpeg")
        filter_images.add_pattern("*.png")
        filter_images.add_pattern("*.bmp")
        filter_images.add_pattern("*.webp")
        filter_images.add_pattern("*.heic")
        filter_images.add_pattern("*.HEIC")
        filter_images.add_pattern("*.heif")
        filter_images.add_pattern("*.HEIF")
        dialog.add_filter(filter_images)
        
        response = dialog.run()
        if response == Gtk.ResponseType.ACCEPT:
            filenames = dialog.get_filenames()
            self.selected_handwritten_images = filenames
            count = len(filenames)
            self.lbl_handwritten_count.set_text(f"{count} imágenes seleccionadas")
            logger.info(f"Selected {count} handwritten note images for processing.")
        dialog.destroy()
        
    def on_generate_handwritten_clicked(self, widget):
        if not self.selected_handwritten_images:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Imágenes no seleccionadas"
            )
            dialog.format_secondary_text("Por favor, selecciona al menos una fotografía de apuntes manuscritos antes de continuar.")
            dialog.run()
            dialog.destroy()
            return
            
        self.btn_generate_handwritten.set_sensitive(False)
        self.btn_select_images.set_sensitive(False)
        self.notebook.set_show_tabs(False)
        self.is_running_handwritten = True
        
        self.handwritten_progress_bar.set_fraction(0.0)
        self.handwritten_progress_bar.set_text("Iniciando análisis manuscrito...")
        self.handwritten_progress_bar.show()
        
        threading.Thread(
            target=self.handwritten_worker,
            args=(self.selected_handwritten_images,),
            daemon=True
        ).start()
        
    def handwritten_worker(self, image_paths: list):
        """Worker thread to run handwritten notes generation."""
        def progress_cb(message, progress):
            GLib.idle_add(self.update_handwritten_ui, message, progress)
            
        try:
            from pipeline.handwritten_notes import HandwrittenNotesGenerator
            generator = HandwrittenNotesGenerator(image_paths)
            md_path, raw_path = generator.run(status_callback=progress_cb)
            status_msg = f"¡Apuntes manuscritos generados con éxito en:\n{os.path.basename(md_path)}"
            GLib.idle_add(self.on_handwritten_complete, True, status_msg)
        except Exception as e:
            logger.exception("Handwritten Notes pipeline failed in GUI:")
            GLib.idle_add(self.on_handwritten_complete, False, f"Error: {str(e)}")
            
    def update_handwritten_ui(self, message: str, progress: float):
        """Called on GTK idle loop to update progress and status."""
        self.handwritten_status_label.set_text(message)
        self.handwritten_progress_bar.set_fraction(progress)
        percentage = int(progress * 100)
        self.handwritten_progress_bar.set_text(f"Progreso: {percentage}%")
        
    def on_handwritten_complete(self, success: bool, status_text: str):
        """Re-enables controls and resets state after handwritten process completion."""
        self.is_running_handwritten = False
        self.handwritten_progress_bar.hide()
        self.notebook.set_show_tabs(True)
        
        self.btn_generate_handwritten.set_sensitive(True)
        self.btn_select_images.set_sensitive(True)
        
        self.handwritten_status_label.set_text(status_text)
        
        # Reset selection
        self.selected_handwritten_images = []
        self.lbl_handwritten_count.set_text("0 imágenes seleccionadas")
        
        # Pop notification dialog
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO if success else Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Proceso Completado" if success else "Error de Procesamiento"
        )
        dialog.format_secondary_text(status_text)
        dialog.run()
        dialog.destroy()
        
    # ==================== WINDOW EVENT HANDLERS ====================
    def on_delete_event(self, widget, event) -> bool:
        if self.is_running_handwritten:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.NONE,
                text="Procesamiento Manuscrito en Curso"
            )
            dialog.add_button("Salir y Abortar", Gtk.ResponseType.CLOSE)
            dialog.add_button("Seguir Esperando", Gtk.ResponseType.OK)
            dialog.format_secondary_text(
                "La digitalización de los apuntes manuscritos se está ejecutando actualmente.\n\n"
                "¿Estás seguro de que quieres cerrar la aplicación? "
                "Esto cancelará la generación actual."
            )
            response = dialog.run()
            dialog.destroy()
            
            if response == Gtk.ResponseType.OK:
                return True # Cancel close
            else:
                return False # Proceed with close
                
        if self.is_running_pipeline:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.NONE,
                text="Análisis en Curso"
            )
            dialog.add_button("Salir y Abortar", Gtk.ResponseType.CLOSE)
            dialog.add_button("Seguir Esperando", Gtk.ResponseType.OK)
            dialog.format_secondary_text(
                "La generación de apuntes e IA se está ejecutando actualmente.\n\n"
                "¿Estás seguro de que quieres cerrar la aplicación? "
                "Esto cancelará la generación actual."
            )
            response = dialog.run()
            dialog.destroy()
            
            if response == Gtk.ResponseType.OK:
                return True # Cancel close
            else:
                return False # Proceed with close
                
        if self.is_processing:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.NONE,
                text="Compression in Progress"
            )
            dialog.add_button("Exit and Abort", Gtk.ResponseType.CLOSE)
            dialog.add_button("Keep Waiting", Gtk.ResponseType.OK)
            dialog.format_secondary_text(
                "Closing the application now will abort the compression process, "
                "which may corrupt the final video file.\n\n"
                "Do you want to keep waiting for it to finish?"
            )
            response = dialog.run()
            dialog.destroy()
            
            if response == Gtk.ResponseType.OK:
                return True
            else:
                logger.warning("User chose to abort compression. Terminating FFmpeg...")
                self.processor.abort()
                return False
                
        if self.is_recording:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text="Recording in Progress"
            )
            dialog.format_secondary_text(
                "A recording is currently active.\n\n"
                "Do you want to stop and save it before exiting?"
            )
            response = dialog.run()
            dialog.destroy()
            
            if response == Gtk.ResponseType.YES:
                self.stop_recording_session_and_process()
                return True
            else:
                return False
                
        return False
        
    def on_destroy(self, widget):
        if self.is_recording:
            logger.info("Window closed while recording. Saving current data...")
            if self.timer_timeout_id:
                GLib.source_remove(self.timer_timeout_id)
            if self.zoom_poll_timeout_id:
                GLib.source_remove(self.zoom_poll_timeout_id)
                
            video_file = self.video_recorder.stop() if self.video_recorder else None
            audio_file = self.audio_recorder.stop() if self.audio_recorder else None
            
            if video_file and audio_file:
                now = datetime.now()
                filename = f"{now.strftime(config.FILENAME_FORMAT)}.mp4"
                output_path = os.path.join(config.OUTPUT_DIR, filename)
                self.processor.merge_and_compress(video_file, audio_file, output_path)
                
        if self.is_processing:
            self.processor.abort()
            
        Gtk.main_quit()

if __name__ == "__main__":
    if not MediaProcessor().is_available():
        print("[WARNING] FFmpeg is not installed. Install it by running: sudo apt install ffmpeg")
        
    app = ZoomRecorderGUI()
    app.show_all()
    Gtk.main()
