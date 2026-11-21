# Blockchain-Based File Integrity Verification System

A lightweight, beginner-friendly web application designed for a **college-level mini project**. This system demonstrates how cryptographic hashing (**SHA-256**) and a **custom Python blockchain** can be used together to detect unauthorized file tampering and guarantee digital document integrity without relying on external cryptocurrencies or public networks.

---

## 📌 Project Overview

Digital files (such as academic certificates, legal contracts, medical records, and financial receipts) are vulnerable to silent modifications and cyber tampering. Traditional centralized databases can be modified by unauthorized users or database administrators.

This project implements a **local private blockchain ledger**:
1. When a file is uploaded, the system computes its unique **SHA-256 cryptographic hash** (digital fingerprint).
2. The hash, filename, file size, and timestamp are packed into a **Block** and mined using a Proof-of-Work (PoW) algorithm.
3. Each block points back to the previous block via cryptographic hashes, forming an **immutable chain**.
4. If a user subsequently checks a file, the system recomputes its hash and verifies whether it matches the permanently recorded blockchain ledger.
5. Even a single character change in the file alters its SHA-256 digest completely (the *avalanche effect*), instantly flagging tampering.

---

## 📂 Project Structure

```text
blockchain/
│
├── app.py                 # Flask web server and REST API endpoints
├── blockchain.py          # Custom Python Blockchain and Block classes with Proof of Work
├── file_handler.py        # Stream-based SHA-256 calculation and file utilities
├── requirements.txt       # Python dependencies (Flask, Werkzeug)
├── README.md              # Project documentation and presentation guide
│
├── templates/
│   └── index.html         # Modern dashboard UI with drag-and-drop and ledger view
│
└── static/
    ├── style.css          # Responsive CSS styles, cards, and theme styling
    └── script.js          # Client-side AJAX requests, drag-and-drop, and dynamic rendering
```

### Purpose of Each File:
* **`blockchain.py`**: Contains the pure Python implementation of the `Block` and `Blockchain` classes. It manages the genesis block, calculates SHA-256 block hashes, runs Proof of Work (mining), validates chain continuity, and queries file records.
* **`file_handler.py`**: Reads incoming file streams in memory-efficient 64 KB chunks, computes SHA-256 digests, and formats file sizes without writing temporary files to disk.
* **`app.py`**: The Flask application entry point. Bridges the web interface with the blockchain data structure via JSON APIs (`/api/upload`, `/api/verify`, `/api/chain`).
* **`templates/index.html`**: A clean, single-page dashboard containing upload zones, verification forms, real-time status counters, and the blockchain ledger explorer.
* **`static/style.css`**: Provides modern styling using a soft palette, card layouts, status badges, and visual blockchain connectors.
* **`static/script.js`**: Handles file drag-and-drop events, asynchronous `fetch` calls, loading spinners, and dynamically displays ledger blocks without page refreshes.
* **`requirements.txt`**: Specifies minimal, modern Python packages needed to run the project.

---

## 🛠️ Technology Stack

* **Backend**: Python 3.8+, Flask 3.x, Werkzeug
* **Cryptography**: Python standard `hashlib` (SHA-256)
* **Frontend**: Vanilla HTML5, CSS3, JavaScript (ES6+ Fetch API)
* **Design**: Responsive CSS Grid / Flexbox, Modern Dashboard aesthetics

---

## 🚀 Installation & Setup Instructions

### 1. Prerequisites
Ensure you have **Python 3.8** or higher installed on your system:
```bash
python3 --version
```

### 2. Navigate to Project Directory
```bash
cd /path/to/blockchain
```

### 3. Create and Activate Virtual Environment (Recommended)
* **On macOS / Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```
* **On Windows:**
  ```cmd
  python -m venv venv
  venv\Scripts\activate
  ```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Run the Application
```bash
python3 app.py
```

### 6. Open the Dashboard
Open your web browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 🧪 Demonstration & Testing Guide (For College Viva / Evaluation)

Follow these steps during your project presentation or lab demonstration:

### Step 1: Inspect the Genesis Block
* When you launch the web application, observe the **Blockchain Ledger Explorer** at the bottom.
* Notice **Block #0 (Genesis Block)** is automatically initialized with `Previous Hash: 0` and a valid mined hash starting with `00`.

### Step 2: Register a Sample File
1. Create a simple text file named `contract.txt` with the text: `Agreement between Party A and Party B`.
2. Drag and drop `contract.txt` into the **1. Register File on Blockchain** card.
3. Click **"Generate SHA-256 & Mine Block"**.
4. The system calculates the SHA-256 digest, mines the block, and displays:
   * Computed File Hash
   * Assigned Block Number (`Block #1`)
   * Block Hash and Proof of Work Nonce
5. Notice the new block instantly appears in the live **Ledger Explorer**.

### Step 3: Verify the Authentic File
1. Drop the exact same `contract.txt` into the **2. Verify File Integrity** card.
2. Click **"Verify File Integrity"**.
3. **Result:** You will see a green alert: `✅ Integrity Verified (Authentic)` indicating that the file matches the record in `Block #1`.

### Step 4: Simulate File Tampering (The Core Test)
1. Open `contract.txt` on your computer and edit one character (e.g., change `Party B` to `Party C`). Save the file.
2. Drop this modified `contract.txt` into the **2. Verify File Integrity** card.
3. Click **"Verify File Integrity"**.
4. **Result:** You will see a red alert: `❌ Integrity Verification Failed (No Match Found / File Altered)`.
5. **Viva Explanation:** Explain how the SHA-256 avalanche effect changed the file's hash completely, proving that the file was altered after registration.

### Step 5: Duplicate Detection
* Try uploading the original `contract.txt` again in the Register section.
* The system will detect that the hash already exists on the ledger and reject duplicate entry, maintaining ledger cleanliness.

---

## 📡 REST API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/` | `GET` | Serves the main interactive dashboard interface |
| `/upload` | `POST` | Accepts an uploaded file in binary mode and calculates its SHA-256 hash |
| `/store` | `POST` | Stores the file name and hash in a new block mined with Proof of Work |
| `/verify` | `POST` | Computes uploaded file hash and compares with a selected record or the full chain |
| `/records` | `GET` | Displays all blockchain records stored in the ledger |
| `/validate-chain` | `GET` | Checks whether the blockchain is valid and cryptographically intact |

---

## 💡 Key Concepts for College Presentation

* **Cryptographic Hash (SHA-256)**: A one-way mathematical function that converts arbitrary data into a fixed 256-bit (64 hex characters) string. It is deterministic, collision-resistant, and irreversible.
* **Proof of Work (PoW)**: A consensus mechanism where the computer solves a mathematical puzzle (finding a nonce such that the block hash begins with target zeroes, e.g. `00`).
* **Immutability**: If an attacker attempts to alter a previously stored block's data or hash, the `is_chain_valid()` check detects a mismatch with subsequent blocks, invalidating the entire chain from that point forward.
* **Zero Storage Overhead**: The system does not store copies of sensitive files on the server; only their mathematical hashes are retained, ensuring privacy and minimal storage requirements.
