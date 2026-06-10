import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Pango
import logging
import os
import sys
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
    """Native GTK 3 Graphical User Interface for Zoom and Screen Recorder."""
    
    def __init__(self):
        super().__init__(title="Zoom & Screen Recorder")
        self.set_default_size(400, 300)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # Initialize Core Logic
        self.detector = ZoomDetector()
        self.processor = MediaProcessor()
        self.video_recorder = None
        self.audio_recorder = None
        
        self.is_recording = False
        self.is_waiting_zoom = False
        self.is_processing = False
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
        hb.props.subtitle = "Zorin OS / GNOME"
        self.set_titlebar(hb)
        
        # Main Layout Box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        self.add(main_box)
        
        # Mode Selection Group
        mode_frame = Gtk.Frame(label="Recording Mode")
        mode_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        mode_box.set_margin_start(15)
        mode_box.set_margin_end(15)
        mode_box.set_margin_top(10)
        mode_box.set_margin_bottom(10)
        mode_frame.add(mode_box)
        main_box.pack_start(mode_frame, False, False, 0)
        
        self.radio_auto = Gtk.RadioButton.new_with_label_from_widget(None, "Automatic (Detect Zoom)")
        self.radio_manual = Gtk.RadioButton.new_with_label_from_widget(self.radio_auto, "Manual (Record Full Screen)")
        mode_box.pack_start(self.radio_auto, False, False, 0)
        mode_box.pack_start(self.radio_manual, False, False, 0)
        
        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.pack_start(sep, False, False, 0)
        
        # Display Box (Timer and Status)
        display_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        main_box.pack_start(display_box, True, True, 0)
        
        # Large Digital Timer Label
        self.timer_label = Gtk.Label(label="00:00:00")
        self.timer_label.modify_font(Pango.FontDescription("monospace bold 28"))
        display_box.pack_start(self.timer_label, True, True, 0)
        
        # Status Label
        self.status_label = Gtk.Label(label="Ready to record")
        self.status_label.modify_font(Pango.FontDescription("italic 10"))
        display_box.pack_start(self.status_label, False, False, 0)
        
        # Progress Bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_text("")
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_no_show_all(True)
        self.progress_bar.hide()
        display_box.pack_start(self.progress_bar, False, False, 5)
        
        # Buttons Box
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        btn_box.set_homogeneous(True)
        main_box.pack_start(btn_box, False, False, 0)
        
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
        
    def on_record_clicked(self, widget):
        # Disable inputs
        self.radio_auto.set_sensitive(False)
        self.radio_manual.set_sensitive(False)
        self.btn_record.set_sensitive(False)
        self.btn_stop.set_sensitive(True)
        
        if self.radio_manual.get_active():
            # Manual Mode
            self.status_label.set_text("Starting manual recording...")
            if self.start_recording_session():
                self.status_label.set_text("Recording full screen...")
        else:
            # Auto (Zoom) Mode
            self.is_waiting_zoom = True
            self.status_label.set_text("Waiting for Zoom call...")
            self.zoom_poll_timeout_id = GLib.timeout_add_seconds(config.POLLING_INTERVAL, self.poll_zoom_status)
            
    def on_stop_clicked(self, widget):
        self.btn_stop.set_sensitive(False)
        
        if self.is_waiting_zoom and not self.is_recording:
            # Cancel waiting
            logger.info("Zoom waiting canceled by user.")
            if self.zoom_poll_timeout_id:
                GLib.source_remove(self.zoom_poll_timeout_id)
                self.zoom_poll_timeout_id = None
            self.is_waiting_zoom = False
            self.reset_ui_state("Recording canceled")
        else:
            # Active recording
            self.status_label.set_text("Processing and compressing recording...")
            self.stop_recording_session_and_process()
            
    def start_recording_session(self) -> bool:
        """Initializes and starts video and audio recorders."""
        video_temp_template = f"temp_zoom_video_{int(time.time())}"
        audio_temp_path = os.path.join(config.TEMP_DIR, f"temp_zoom_audio_{int(time.time())}.ogg")
        
        try:
            self.video_recorder = VideoRecorder(filename_template=video_temp_template)
            self.audio_recorder = AudioRecorder(output_path=audio_temp_path)
            
            # Start Video
            if not self.video_recorder.start():
                self.reset_ui_state("Error: Video recorder failed")
                return False
                
            # Start Audio
            if not self.audio_recorder.start():
                self.video_recorder.stop()
                self.reset_ui_state("Error: Audio recorder failed")
                return False
                
            self.is_recording = True
            self.recording_start_time = datetime.now()
            
            # Start Timer UI Timeout
            self.timer_timeout_id = GLib.timeout_add_seconds(1, self.update_timer)
            return True
            
        except Exception as e:
            logger.error(f"Error starting recording session: {e}")
            self.reset_ui_state("Error starting recorders")
            return False
            
    def stop_recording_session_and_process(self):
        """Stops recorders and spins a background thread to compress media."""
        if not self.is_recording:
            return
            
        self.is_recording = False
        
        # Stop Timer
        if self.timer_timeout_id:
            GLib.source_remove(self.timer_timeout_id)
            self.timer_timeout_id = None
            
        # Stop Zoom Polling if any
        if self.zoom_poll_timeout_id:
            GLib.source_remove(self.zoom_poll_timeout_id)
            self.zoom_poll_timeout_id = None
            
        video_file = None
        audio_file = None
        
        if self.video_recorder:
            video_file = self.video_recorder.stop()
        if self.audio_recorder:
            audio_file = self.audio_recorder.stop()
            
        logger.info("Recording stopped. Spawning merge and compression thread...")
        
        # Setup and show progress bar
        self.is_processing = True
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_text("Initializing compression...")
        self.progress_bar.show()
        
        # Spin worker thread to do the heavy compression without freezing the GUI
        threading.Thread(
            target=self.merge_and_compress_worker,
            args=(video_file, audio_file),
            daemon=True
        ).start()
        
    def merge_and_compress_worker(self, video_file: str, audio_file: str):
        """Worker thread for compression."""
        time.sleep(2.0) # Ensure files are flushed
        
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
        """Updates the progress bar in the main thread."""
        self.progress_bar.set_fraction(progress)
        percentage = int(progress * 100)
        self.progress_bar.set_text(f"Compressing... {percentage}%")

    def on_processing_complete(self, success: bool, info: str):
        """Callback run on main thread when compression completes."""
        self.is_processing = False
        self.progress_bar.hide()
        if success:
            logger.info(f"Processing complete: {info}")
            self.reset_ui_state(f"Recording saved: {info}")
        else:
            logger.error(f"Processing failed: {info}")
            self.reset_ui_state(f"Error: {info}")
            
    def poll_zoom_status(self) -> bool:
        """Periodic callback to check Zoom call status."""
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
            # If in Auto mode, we reset to waiting state for next call after processing
            self.is_waiting_zoom = True
            
        return True # Keep timeout alive
        
    def update_timer(self) -> bool:
        """Periodic callback to update timer label."""
        if not self.is_recording or not self.recording_start_time:
            return False
            
        delta = datetime.now() - self.recording_start_time
        # Format delta as HH:MM:SS
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        timer_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.timer_label.set_text(timer_str)
        return True # Keep timeout alive
        
    def reset_ui_state(self, status_text: str):
        """Resets buttons and selectors back to original state."""
        self.radio_auto.set_sensitive(True)
        self.radio_manual.set_sensitive(True)
        self.btn_record.set_sensitive(True)
        self.btn_stop.set_sensitive(False)
        self.status_label.set_text(status_text)
        self.timer_label.set_text("00:00:00")
        
        self.is_recording = False
        self.is_waiting_zoom = False
        self.is_processing = False
        
    def on_delete_event(self, widget, event) -> bool:
        """Handles close window event to warn user if recording or processing."""
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
                return True # Cancel close
            else:
                logger.warning("User chose to abort compression. Terminating FFmpeg...")
                self.processor.abort()
                return False # Proceed with close
                
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
                return True # Cancel close so it finishes merging
            else:
                return False # Proceed with close
                
        return False # Proceed with close
        
    def on_destroy(self, widget):
        # Cleanup recording
        if self.is_recording:
            logger.info("Window closed while recording. Saving current data...")
            # Stop immediately
            if self.timer_timeout_id:
                GLib.source_remove(self.timer_timeout_id)
            if self.zoom_poll_timeout_id:
                GLib.source_remove(self.zoom_poll_timeout_id)
                
            video_file = self.video_recorder.stop() if self.video_recorder else None
            audio_file = self.audio_recorder.stop() if self.audio_recorder else None
            
            if video_file and audio_file:
                # Synchronous merge on exit
                now = datetime.now()
                filename = f"{now.strftime(config.FILENAME_FORMAT)}.mp4"
                output_path = os.path.join(config.OUTPUT_DIR, filename)
                self.processor.merge_and_compress(video_file, audio_file, output_path)
                
        if self.is_processing:
            self.processor.abort()
            
        Gtk.main_quit()

if __name__ == "__main__":
    # Ensure dependencies are loaded
    if not MediaProcessor().is_available():
        print("[WARNING] FFmpeg is not installed. Install it by running: sudo apt install ffmpeg")
        
    app = ZoomRecorderGUI()
    app.show_all()
    Gtk.main()
