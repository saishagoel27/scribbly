import streamlit as st
from pathlib import Path
import mimetypes
from config import config

class FileHandler:
    """Handles file upload, validation, and basic processing"""
    
    def __init__(self):
        self.max_size_bytes = config.max_file_size_mb * 1024 * 1024  # Convert MB to bytes
        self.supported_types = config.supported_file_types
    
    def create_upload_interface(self):
        """Creates the Streamlit file upload interface"""
        st.subheader("📁 Upload Your Document")
        
        # Show supported file types
        with st.expander("ℹ️ What files can I upload?", expanded=False):
            st.write("**Supported formats:**")
            st.write("- 📄 PDF files (.pdf)")
            st.write("- 🖼️ Images with text (.png, .jpg, .jpeg)")
            st.write("- 📝 Text files (.txt)")
            st.write("- 📋 Word documents (.docx)")
            st.write(f"- 📏 Maximum size: {config.max_file_size_mb} MB")
        
        # File uploader widget
        uploaded_file = st.file_uploader(
            "Choose a file to analyze",
            type=self.supported_types,
            help=f"Max size: {config.max_file_size_mb}MB"
        )
        
        return uploaded_file
    
    def validate_file(self, uploaded_file):
        """Validates the uploaded file"""
        if not uploaded_file:
            return False, "No file uploaded"
        
        # Check file size
        if uploaded_file.size > self.max_size_bytes:
            return False, f"File too large! Maximum size is {config.max_file_size_mb}MB"
        
        # Check if file is empty
        if uploaded_file.size == 0:
            return False, "File is empty"
        
        # Check file extension
        file_extension = Path(uploaded_file.name).suffix.lower().lstrip('.')
        if file_extension not in self.supported_types:
            return False, f"Unsupported file type: .{file_extension}"
        
        return True, "File is valid"
    
    def get_file_info(self, uploaded_file):
        """Gets detailed information about the uploaded file"""
        file_size_mb = uploaded_file.size / (1024 * 1024)
        file_extension = Path(uploaded_file.name).suffix.lower().lstrip('.')
        
        return {
            "name": uploaded_file.name,
            "size_bytes": uploaded_file.size,
            "size_mb": round(file_size_mb, 2),
            "extension": file_extension,
            "mime_type": mimetypes.guess_type(uploaded_file.name)[0],
            "is_image": file_extension in ['png', 'jpg', 'jpeg'],
            "is_pdf": file_extension == 'pdf',
            "is_text": file_extension in ['txt', 'docx']
        }
    
    def display_file_info(self, uploaded_file):
        """Displays file information in a nice format"""
        file_info = self.get_file_info(uploaded_file)
        
        # Create columns for file info
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📄 File Name", file_info["name"])
        
        with col2:
            st.metric("📏 File Size", f"{file_info['size_mb']} MB")
        
        with col3:
            st.metric("🔤 File Type", f".{file_info['extension'].upper()}")
        
        # Show file type specific info
        if file_info["is_image"]:
            st.info("🖼️ Image file - Will extract text using OCR")
        elif file_info["is_pdf"]:
            st.info("📄 PDF file - Will extract text and structure")
        elif file_info["is_text"]:
            st.info("📝 Text file - Will read content directly")
    
    def prepare_file_for_azure(self, uploaded_file):
        """Prepares the file for Azure Document Intelligence API"""
        # Reset file pointer to beginning
        uploaded_file.seek(0)
        
        # Read file content as bytes
        file_bytes = uploaded_file.read()
        
        # Reset file pointer again for potential future reads
        uploaded_file.seek(0)
        
        # Get content type for Azure API
        content_type = self._get_content_type(uploaded_file.name)
        
        return file_bytes, content_type
    
    def _get_content_type(self, filename):
        """Gets the appropriate content type for Azure Document Intelligence"""
        file_extension = Path(filename).suffix.lower().lstrip('.')
        
        content_type_mapping = {
            'pdf': 'application/pdf',
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'txt': 'text/plain',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        
        return content_type_mapping.get(file_extension, 'application/octet-stream')

# Create a global instance
file_handler = FileHandler()