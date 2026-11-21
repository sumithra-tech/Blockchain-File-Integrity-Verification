import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from blockchain import Blockchain
from file_handler import (
    FileHandlingError,
    process_uploaded_file,
    generate_file_sha256,
    format_file_size,
    allowed_file
)

app = Flask(__name__)

# Max upload limit: 50 MB
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# Instantiate custom educational blockchain with persistent local JSON storage
blockchain = Blockchain(storage_file="blockchain_data.json", difficulty=2)


# =====================================================================
# Route 1: / – Display the home dashboard
# =====================================================================
@app.route('/', methods=['GET'])
def index():
    """Renders the main dashboard."""
    return render_template('index.html')


# =====================================================================
# Route 2: /upload – Accept an uploaded file and calculate its SHA-256 hash
# =====================================================================
@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Accepts an uploaded file, validates format and size, reads in binary mode,
    computes its SHA-256 hash using Python hashlib, and returns the hash.
    Does NOT store the uploaded file permanently.
    """
    if 'file' not in request.files:
        return jsonify({
            "success": False,
            "message": "No file uploaded. Please select a file to hash."
        }), 400

    file = request.files['file']
    try:
        # Validate and calculate SHA-256 hash in binary mode
        file_info = process_uploaded_file(file)
        return jsonify({
            "success": True,
            "message": "File uploaded and SHA-256 hash successfully calculated.",
            "filename": file_info["filename"],
            "file_hash": file_info["file_hash"],
            "file_size": file_info["file_size"],
            "size_bytes": file_info["size_bytes"]
        }), 200
    except FileHandlingError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Server error processing file: {str(e)}"
        }), 500


# =====================================================================
# Route 3: /store – Store the file name and hash in a new blockchain block
# =====================================================================
@app.route('/store', methods=['POST'])
def store_file():
    """
    Stores the file name and SHA-256 hash into a new blockchain block.
    Accepts either:
      1. Direct multipart file upload: request.files['file']
      2. JSON payload: {"filename": "...", "file_hash": "...", "file_size": "..."}
      3. Form data: filename, file_hash, file_size
    """
    filename = None
    file_hash = None
    file_size = "N/A"

    # Case 1: Direct file upload
    if 'file' in request.files and request.files['file'].filename != '':
        try:
            file_info = process_uploaded_file(request.files['file'])
            filename = file_info["filename"]
            file_hash = file_info["file_hash"]
            file_size = file_info["file_size"]
        except FileHandlingError as e:
            return jsonify({"success": False, "message": str(e)}), 400
    else:
        # Case 2: JSON or Form payload
        data = request.get_json(silent=True) or request.form
        filename = data.get('filename') or data.get('file_name')
        file_hash = data.get('file_hash')
        file_size = data.get('file_size', 'N/A')

    if not filename or not file_hash:
        return jsonify({
            "success": False,
            "message": "Both 'filename' and 'file_hash' are required to store a block."
        }), 400

    filename = secure_filename(filename)
    if len(file_hash) != 64:
        return jsonify({
            "success": False,
            "message": "Invalid SHA-256 hash. Hash must be 64 hexadecimal characters."
        }), 400

    # Check for duplicate entry on the blockchain
    existing_block = blockchain.find_file(file_hash)
    if existing_block:
        return jsonify({
            "success": False,
            "already_exists": True,
            "message": f"This file hash is already permanently registered in Block #{existing_block.index}.",
            "block": existing_block.to_dict(),
            "filename": filename,
            "file_hash": file_hash
        }), 409

    # Add new block to the blockchain (mines block with Proof of Work)
    new_block = blockchain.add_block(
        file_name=filename,
        file_hash=file_hash,
        file_size=file_size
    )

    return jsonify({
        "success": True,
        "message": f"Block #{new_block.index} successfully mined and appended to the blockchain!",
        "block": new_block.to_dict(),
        "filename": filename,
        "file_hash": file_hash
    }), 201


# =====================================================================
# Route 4: /verify – Calculate uploaded file hash and compare with existing record
# =====================================================================
@app.route('/verify', methods=['POST'])
def verify_file():
    """
    Calculates the uploaded file's SHA-256 hash and compares it:
    - Against a specifically selected existing blockchain record (if block_index is provided), OR
    - Against all existing blockchain records (if no block_index is provided).
    """
    if 'file' not in request.files:
        return jsonify({
            "success": False,
            "message": "No file uploaded. Please select a file to verify."
        }), 400

    file = request.files['file']
    try:
        file_info = process_uploaded_file(file)
        file_hash = file_info["file_hash"]
        filename = file_info["filename"]
        file_size = file_info["file_size"]

        # Check if user selected a specific block record to compare with
        block_index_raw = request.form.get('block_index') or request.args.get('block_index')

        if block_index_raw is not None and str(block_index_raw).strip() != "":
            try:
                target_index = int(block_index_raw)
            except ValueError:
                return jsonify({
                    "success": False,
                    "message": f"Invalid block index: '{block_index_raw}'."
                }), 400

            # Find specific block in chain
            target_block = None
            for b in blockchain.chain:
                if b.index == target_index:
                    target_block = b
                    break

            if not target_block:
                return jsonify({
                    "success": False,
                    "message": f"Block #{target_index} does not exist in the blockchain."
                }), 404

            # Compare uploaded file hash with selected block's hash
            if target_block.index == 0:
                is_match = False
                msg = "Block #0 is the Genesis Block and does not contain user file records."
            else:
                is_match = (file_hash == target_block.file_hash)
                if is_match:
                    msg = f"Integrity Verified! File matches Block #{target_block.index} ({target_block.file_name}) perfectly."
                else:
                    msg = (
                        f"Integrity Alert! File does NOT match selected Block #{target_block.index}. "
                        f"Expected: {target_block.file_hash[:16]}..., Calculated: {file_hash[:16]}..."
                    )

            return jsonify({
                "success": True,
                "verified": is_match,
                "message": msg,
                "filename": filename,
                "file_hash": file_hash,
                "file_size": file_size,
                "selected_block": target_block.to_dict(),
                "matched_block": target_block.to_dict() if is_match else None
            }), 200

        else:
            # Auto-search across all existing blockchain records
            matched_block = blockchain.find_file(file_hash)
            if matched_block:
                return jsonify({
                    "success": True,
                    "verified": True,
                    "message": f"File integrity verified! Authentic record found in Block #{matched_block.index}.",
                    "filename": filename,
                    "file_hash": file_hash,
                    "file_size": file_size,
                    "matched_block": matched_block.to_dict()
                }), 200
            else:
                return jsonify({
                    "success": True,
                    "verified": False,
                    "message": "Integrity alert! No matching hash found on the blockchain. The file may be altered or not registered.",
                    "filename": filename,
                    "file_hash": file_hash,
                    "file_size": file_size
                }), 200

    except FileHandlingError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Verification error: {str(e)}"
        }), 500


# =====================================================================
# Route 5: /records – Display all blockchain records
# =====================================================================
@app.route('/records', methods=['GET'])
def get_records():
    """
    Returns all blockchain records currently stored in the ledger.
    """
    records = [block.to_dict() for block in blockchain.chain]
    return jsonify({
        "success": True,
        "total_records": len(records),
        "records": records,
        "chain": records  # Alias for explorer rendering
    }), 200


# =====================================================================
# Route 6: /validate-chain – Check whether the blockchain is valid
# =====================================================================
@app.route('/validate-chain', methods=['GET'])
def validate_chain():
    """
    Validates whether the blockchain has been modified or tampered with:
    - Recalculates all hashes.
    - Checks previous_hash linkage.
    - Validates Proof of Work.
    """
    is_valid, validation_msg = blockchain.is_chain_valid()
    return jsonify({
        "success": True,
        "is_valid": is_valid,
        "message": validation_msg,
        "total_blocks": len(blockchain.chain)
    }), 200


# =====================================================================
# Compatibility Aliases (for existing /api endpoints)
# =====================================================================
@app.route('/api/upload', methods=['POST'])
def api_upload():
    return store_file()

@app.route('/api/verify', methods=['POST'])
def api_verify():
    return verify_file()

@app.route('/api/chain', methods=['GET'])
def api_chain():
    return get_records()


# =====================================================================
# Error Handlers
# =====================================================================
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        "success": False,
        "message": "File exceeds the maximum allowed size of 50MB."
    }), 413

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "message": "Endpoint not found."
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "message": "Internal server error. Please try again."
    }), 500


if __name__ == '__main__':
    # Run development server
    app.run(host='127.0.0.1', port=5001, debug=True)
