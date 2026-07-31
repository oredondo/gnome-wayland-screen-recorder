import os
import sys
import pytest
import numpy as np
from unittest.mock import MagicMock, patch

# Add project root directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from pipeline.handwritten_notes import HandwrittenOCRExtractor, HandwrittenNotesGenerator

class TestHandwrittenOCRExtractor:
    
    @patch('cv2.imread')
    @patch('pytesseract.image_to_string')
    def test_extract_all_success(self, mock_tesseract, mock_imread, tmp_path):
        # Create a real dummy image file
        test_img = tmp_path / "dummy_page1.jpg"
        test_img.write_text("fake image content")
        
        # Mock cv2 image array
        dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_imread.return_value = dummy_img
        
        # Mock Tesseract text
        mock_tesseract.return_value = "Apuntes manuscritos de prueba\n- Punto 1\n- Punto 2"
        
        extractor = HandwrittenOCRExtractor([str(test_img)])
        full_text, pages = extractor.extract_all()
        
        assert "Apuntes manuscritos de prueba" in full_text
        assert len(pages) == 1
        mock_tesseract.assert_called()

    @patch('pillow_heif.register_heif_opener')
    @patch('PIL.Image.open')
    @patch('pytesseract.image_to_string')
    def test_extract_heic_image_success(self, mock_tesseract, mock_pil_open, mock_heif_reg, tmp_path):
        test_heic = tmp_path / "photo.heic"
        test_heic.write_text("fake heic content")
        
        mock_pil_img = MagicMock()
        mock_pil_img.convert.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_pil_open.return_value = mock_pil_img
        
        mock_tesseract.return_value = "Texto desde archivo HEIC"
        
        extractor = HandwrittenOCRExtractor([str(test_heic)])
        full_text, pages = extractor.extract_all()
        
        assert "Texto desde archivo HEIC" in full_text
        assert len(pages) == 1

class TestHandwrittenNotesGenerator:

    @patch('pipeline.handwritten_notes.HandwrittenOCRExtractor.extract_all')
    @patch('pipeline.handwritten_notes.LLMManager.process_node')
    @patch('builtins.open')
    @patch('shutil.copy')
    @patch('shutil.rmtree')
    def test_generator_run_success(self, mock_rmtree, mock_copy, mock_open, mock_llm_process, mock_extract_all, tmp_path):
        test_img = tmp_path / "dummy1.jpg"
        test_img.write_text("fake image content")
        
        mock_extract_all.return_value = ("Texto OCR manuscrito", ["Texto OCR manuscrito"])
        mock_llm_process.return_value = "# Apuntes Manuscritos\n\n- Punto 1\n- Punto 2"
        
        # Mock file writing
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        out_dir = tmp_path / "dummy_out"
        generator = HandwrittenNotesGenerator([str(test_img)], output_dir=str(out_dir))
        md_path, raw_path = generator.run()
        
        assert md_path.endswith("_manuscrito.md")
        assert raw_path.endswith("_manuscrito_bruto.txt")
        mock_llm_process.assert_called_once()
        mock_copy.assert_called_once()
