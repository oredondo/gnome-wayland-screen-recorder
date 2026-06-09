import subprocess
import re
import logging
import config

logger = logging.getLogger(__name__)

class ZoomDetector:
    """Detects active Zoom calls by monitoring the window list."""
    
    def __init__(self):
        # Pattern to match: id "title": ("instance" "class")
        self._pattern = re.compile(r'^\s*(0x[0-9a-fA-F]+)\s+"([^"]*)":\s+\("([^"]*)"\s+"([^"]*)"\)')
        # Titles to ignore (main client window and system placeholders) from config
        self._ignored_titles = config.ZOOM_IGNORED_TITLES
        
    def is_meeting_active(self) -> bool:
        """Returns True if an active Zoom meeting is detected, False otherwise."""
        try:
            output = subprocess.check_output(["xwininfo", "-root", "-children"], stderr=subprocess.DEVNULL).decode("utf-8")
        except Exception as e:
            logger.error(f"Error executing xwininfo: {e}")
            return False
            
        for line in output.splitlines():
            match = self._pattern.match(line)
            if match:
                title = match.group(2).strip()
                cls = match.group(4).strip()
                
                # Check if this window belongs to Zoom
                if cls.lower() == "zoom":
                    title_lower = title.lower()
                    
                    # If title is empty, or belongs to the main dashboard or a service window, skip it
                    if not title:
                        continue
                    if title_lower in self._ignored_titles:
                        continue
                    if "selection owner" in title_lower or "clipboard" in title_lower:
                        continue
                        
                    # If we found another Zoom window, a meeting/call is active
                    logger.debug(f"Active Zoom meeting window detected: ID={match.group(1)}, Title='{title}'")
                    return True
                    
        return False
