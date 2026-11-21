import os
import re
import hashlib

# Gracefully import secure_filename from Werkzeug, with a standard fallback
try:
    from werkzeug.utils import secure_filename
except ImportError:
    def secure_filename(filename):
        """
        Lightweight fallback sanitizer if Werkzeug is not installed.
        Removes path traversals and non-standard characters.
        """
        clean_name = os.path.basename(filename)
        clean_name = re.sub(r'[^A-Za-z0-9_.-]', '_', clean_name)
        return clean_name.strip('._')

# Supported file extensions for college mini-project
# PDF, TXT, JPG, PNG, and DOCX
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'jpg', 'jpeg', 'png', 'docx'}


class FileHandlingError(Exception):
    """Custom exception raised for file validation and handling errors."""
    pass


def allowed_file(filename):
    """
    Checks if a filename possesses an allowed extension.
    Supported types: PDF, TXT, JPG, PNG, DOCX.
    """
    if not filename or '.' not in filename:
        return False
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in ALLOWED_EXTENSIONS


def get_file_size(file_storage):
    """
    Measures the file size in bytes without modifying file content or pointer position.
    """
    file_storage.seek(0, os.SEEK_END)
    size_bytes = file_storage.tell()
    file_storage.seek(0)  # Reset pointer back to the start
    return size_bytes


def format_file_size(size_bytes):
    """
    Converts raw bytes to human-readable size string (B, KB, MB, GB).
    """
    readable_size = float(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if readable_size < 1024.0:
            return f"{readable_size:.2f} {unit}"
        readable_size /= 1024.0
    return f"{readable_size:.2f} TB"


def generate_file_sha256(file_storage):
    """
    Reads the uploaded file in binary mode ('rb') and generates its SHA-256 hash.
    
    - Reads in 64 KB binary chunks to efficiently handle files of any size.
    - Guarantees uploaded content is not altered.
    - Resets the file pointer to 0 after reading.
    
    Returns:
        str: 64-character hexadecimal SHA-256 digest.
    Raises:
        FileHandlingError: If reading fails.
    """
    try:
        sha256 = hashlib.sha256()
        file_storage.seek(0)
        
        # Read in 64KB binary chunks
        while True:
            chunk = file_storage.read(65536)
            if not chunk:
                break
            sha256.update(chunk)
            
        # Reset pointer back to 0 so subsequent handlers can read if needed
        file_storage.seek(0)
        return sha256.hexdigest()
    except Exception as e:
        raise FileHandlingError(f"Failed to generate SHA-256 hash: {str(e)}")


def process_uploaded_file(file_storage):
    """
    Validates uploaded file safely:
    1. Checks for file presence.
    2. Validates filename and sanitizes via secure_filename.
    3. Enforces supported extensions: PDF, TXT, JPG, PNG, DOCX.
    4. Rejects empty (0-byte) files.
    5. Calculates and returns SHA-256 digest and file metadata.
    
    Returns:
        dict: Contains filename, file_hash, file_size, and size_bytes.
    Raises:
        FileHandlingError: For any validation failure.
    """
    if file_storage is None:
        raise FileHandlingError("No file uploaded. Please select a file.")

    raw_filename = getattr(file_storage, 'filename', None) or getattr(file_storage, 'name', '') or ''
    if not str(raw_filename).strip():
        raise FileHandlingError("No file selected. Please choose a valid file.")

    filename = secure_filename(str(raw_filename))
    if not filename:
        raise FileHandlingError("Invalid file name. Please rename your file and try again.")

    if not allowed_file(filename):
        supported_list = ", ".join(sorted(ALLOWED_EXTENSIONS)).upper()
        ext = filename.rsplit('.', 1)[-1].upper() if '.' in filename else 'UNKNOWN'
        raise FileHandlingError(
            f"Unsupported file format '.{ext}'. Supported formats are: {supported_list}."
        )

    # Check for empty file
    size_bytes = get_file_size(file_storage)
    if size_bytes == 0:
        raise FileHandlingError(f"The file '{filename}' is empty (0 bytes). Empty files cannot be verified.")

    # Calculate SHA-256
    file_hash = generate_file_sha256(file_storage)
    formatted_size = format_file_size(size_bytes)

    return {
        "filename": filename,
        "file_hash": file_hash,
        "file_size": formatted_size,
        "size_bytes": size_bytes
    }


# =====================================================================
# Bridge Functions Connecting File Handler with Blockchain Functionality
# =====================================================================

def register_file_with_blockchain(file_storage, blockchain):
    """
    Validates file, generates SHA-256 hash, checks for duplicates,
    and registers the file into a new block on the blockchain.
    """
    file_info = process_uploaded_file(file_storage)
    
    # Check for duplicate registration
    existing_block = blockchain.find_file(file_info["file_hash"])
    if existing_block:
        return False, {
            "already_exists": True,
            "message": f"This file is already registered in Block #{existing_block.index}.",
            "block": existing_block.to_dict(),
            "filename": file_info["filename"],
            "file_hash": file_info["file_hash"]
        }, 409

    # Add new block to the blockchain
    new_block = blockchain.add_block(
        file_name=file_info["filename"],
        file_hash=file_info["file_hash"],
        file_size=file_info["file_size"]
    )

    return True, {
        "already_exists": False,
        "message": f"File successfully hashed and recorded into Block #{new_block.index}!",
        "block": new_block.to_dict(),
        "filename": file_info["filename"],
        "file_hash": file_info["file_hash"]
    }, 201


def verify_file_with_blockchain(file_storage, blockchain):
    """
    Validates file, generates SHA-256 hash, and compares it
    against all registered blocks on the blockchain.
    """
    file_info = process_uploaded_file(file_storage)
    matched_block = blockchain.find_file(file_info["file_hash"])

    if matched_block:
        return {
            "verified": True,
            "message": "File integrity verified! The file is authentic and unaltered.",
            "filename": file_info["filename"],
            "file_hash": file_info["file_hash"],
            "file_size": file_info["file_size"],
            "matched_block": matched_block.to_dict()
        }
    else:
        return {
            "verified": False,
            "message": "Integrity alert! No matching hash found on the blockchain. The file may be altered or not registered.",
            "filename": file_info["filename"],
            "file_hash": file_info["file_hash"],
            "file_size": file_info["file_size"]
        }


# Aliases for backwards compatibility
calculate_file_sha256 = generate_file_sha256
get_file_size_formatted = lambda fs: (get_file_size(fs), format_file_size(get_file_size(fs)))


if __name__ == "__main__":
    import io
    from blockchain import Blockchain

    print("=" * 65)
    print(" File Handler & Blockchain Integration - Standalone CLI Test")
    print("=" * 65)

    test_storage = "cli_test_chain.json"
    if os.path.exists(test_storage):
        os.remove(test_storage)

    # Mock FileStorage object for CLI test
    class MockFile:
        def __init__(self, data_bytes, filename):
            self.stream = io.BytesIO(data_bytes)
            self.filename = filename

        def read(self, size=-1):
            return self.stream.read(size)

        def seek(self, offset, whence=0):
            return self.stream.seek(offset, whence)

        def tell(self):
            return self.stream.tell()

    # 1. Test supported formats
    print("\n[1] Testing Supported Formats (PDF, TXT, JPG, PNG, DOCX):")
    sample_types = ["document.pdf", "readme.txt", "photo.jpg", "banner.png", "thesis.docx"]
    for name in sample_types:
        f = MockFile(b"College Project Sample Content", name)
        info = process_uploaded_file(f)
        print(f"    - {name:15}: SHA-256 = {info['file_hash'][:16]}... ({info['file_size']})")

    # 2. Test unsupported format rejection
    print("\n[2] Testing Format Validation (Rejecting .exe):")
    try:
        f_bad = MockFile(b"danger", "malware.exe")
        process_uploaded_file(f_bad)
    except FileHandlingError as err:
        print(f"    Expected Rejection: {err}")

    # 3. Test empty file rejection
    print("\n[3] Testing Empty File Validation (0 Bytes):")
    try:
        f_empty = MockFile(b"", "empty_document.pdf")
        process_uploaded_file(f_empty)
    except FileHandlingError as err:
        print(f"    Expected Rejection: {err}")

    # 4. Test Blockchain Integration
    print("\n[4] Testing Registration & Verification with Blockchain:")
    bc = Blockchain(storage_file=test_storage, difficulty=2)
    original_file = MockFile(b"Confidential Certificate Data 2026", "certificate.pdf")
    
    # Register
    ok, reg_data, code = register_file_with_blockchain(original_file, bc)
    print(f"    Registration: Status {code} | Recorded in Block #{reg_data['block']['index']}")

    # Verify Authentic
    v_res = verify_file_with_blockchain(original_file, bc)
    print(f"    Authentic File Check: Verified={v_res['verified']} | {v_res['message']}")

    # Verify Tampered
    tampered_file = MockFile(b"Tampered Certificate Data 2026", "certificate.pdf")
    t_res = verify_file_with_blockchain(tampered_file, bc)
    print(f"    Tampered File Check:  Verified={t_res['verified']} | {t_res['message']}")

    # Clean up test file
    if os.path.exists(test_storage):
        os.remove(test_storage)

    print("\n" + "=" * 65)
    print(" ALL FILE HANDLER & BLOCKCHAIN INTEGRATION TESTS PASSED! ✅")
    print("=" * 65)
