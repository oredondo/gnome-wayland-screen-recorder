import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import logging
import os
import time
import config

logger = logging.getLogger(__name__)

class AudioRecorder:
    """Manages audio recording of speaker output and/or microphone using GStreamer."""
    
    def __init__(self, output_path: str = "temp_zoom_audio.ogg"):
        self.output_path = os.path.abspath(output_path)
        self._pipeline = None
        self._is_recording = False
        
        Gst.init(None)
        
    def _discover_devices(self):
        """Discovers active microphone and speaker monitor device names dynamically."""
        monitor = Gst.DeviceMonitor.new()
        monitor.add_filter("Audio/Source", None)
        devices = monitor.get_devices()
        
        mic_device = None
        monitor_device = None
        
        for dev in devices:
            props = dev.get_properties()
            if not props:
                continue
                
            node_name = props.get_string("node.name") if props.has_field("node.name") else None
            device_class = props.get_string("device.class") if props.has_field("device.class") else None
            media_class = props.get_string("media.class") if props.has_field("media.class") else None
            
            if not node_name:
                continue
                
            # Check if it is a monitor (speaker output)
            if device_class == "monitor" or "monitor" in node_name.lower():
                dev_name = node_name if node_name.endswith(".monitor") else f"{node_name}.monitor"
                monitor_device = dev_name
                logger.info(f"Discovered speaker monitor: '{dev.get_display_name()}' ({monitor_device})")
            # Check if it is a microphone
            elif device_class == "sound" or media_class == "Audio/Source":
                if "monitor" not in node_name.lower():
                    mic_device = node_name
                    logger.info(f"Discovered microphone: '{dev.get_display_name()}' ({mic_device})")
                    
        return mic_device, monitor_device

    def start(self) -> bool:
        """Starts the audio recording pipeline."""
        if self._is_recording:
            logger.warning("Audio recording is already in progress.")
            return True
            
        mic, mon = self._discover_devices()
        
        # Fallback to PulseAudio/PipeWire default devices if dynamic discovery returned None
        if mon is None:
            mon = "@DEFAULT_SINK@.monitor"
            logger.info(f"Using default speaker monitor fallback: '{mon}'")
            
        if mic is None and config.RECORD_MICROPHONE:
            mic = "@DEFAULT_SOURCE@"
            logger.info(f"Using default microphone fallback: '{mic}'")
        
        # Check config to see if microphone is enabled
        record_mic = config.RECORD_MICROPHONE and mic is not None
        record_mon = mon is not None
        
        if not record_mic and not record_mon:
            logger.error("No audio devices found or enabled for recording.")
            return False
            
        # Build GStreamer pipeline string
        if record_mic and record_mon:
            # Both microphone and system speaker monitor are active: mix them
            logger.info("Recording both microphone and speaker audio...")
            pipeline_str = (
                f"audiomixer name=mixer ! audioconvert ! audioresample ! opusenc ! oggmux ! filesink location=\"{self.output_path}\" "
                f"pulsesrc device=\"{mic}\" ! audioconvert ! audioresample ! queue ! mixer.sink_0 "
                f"pulsesrc device=\"{mon}\" ! audioconvert ! audioresample ! queue ! mixer.sink_1"
            )
        elif record_mon:
            # Only speaker monitor is active/enabled
            logger.info("Recording only internal speaker audio (microphone disabled)...")
            pipeline_str = (
                f"pulsesrc device=\"{mon}\" ! audioconvert ! audioresample ! opusenc ! oggmux ! filesink location=\"{self.output_path}\""
            )
        else:
            # Only microphone is active/enabled
            logger.info("Recording only microphone audio (speaker monitor disabled)...")
            pipeline_str = (
                f"pulsesrc device=\"{mic}\" ! audioconvert ! audioresample ! opusenc ! oggmux ! filesink location=\"{self.output_path}\""
            )
        logger.debug(f"Audio GStreamer Pipeline: {pipeline_str}")
        
        try:

            self._pipeline = Gst.parse_launch(pipeline_str)
            logger.info("Setting audio pipeline to PLAYING...")
            self._pipeline.set_state(Gst.State.PLAYING)
            self._is_recording = True
            return True
        except Exception as e:
            logger.error(f"Failed to start audio pipeline: {e}")
            self._pipeline = None
            return False

    def stop(self) -> str:
        """Stops the audio recording pipeline and returns the path to the recorded Ogg file."""
        if not self._is_recording or not self._pipeline:
            logger.warning("Audio recording was not active.")
            return self.output_path
            
        try:
            logger.info("Stopping audio pipeline (sending EOS)...")
            self._pipeline.send_event(Gst.Event.new_eos())
            
            # Wait for EOS on the bus to flush the buffer and close file cleanly
            bus = self._pipeline.get_bus()
            msg = bus.timed_pop_filtered(
                5 * Gst.SECOND,
                Gst.MessageType.EOS | Gst.MessageType.ERROR
            )
            
            if msg:
                if msg.type == Gst.MessageType.ERROR:
                    err, debug = msg.parse_error()
                    logger.error(f"GStreamer pipeline error: {err.message}")
                else:
                    logger.info("Audio pipeline reached EOS.")
            else:
                logger.warning("Timeout waiting for audio pipeline EOS event.")
                
        except Exception as e:
            logger.error(f"Error while stopping audio pipeline: {e}")
        finally:
            if self._pipeline:
                self._pipeline.set_state(Gst.State.NULL)
                self._pipeline = None
            self._is_recording = False
            
        return self.output_path
