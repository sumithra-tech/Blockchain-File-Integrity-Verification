import os
import json
import time
import hashlib
from datetime import datetime


class Block:
    """
    Represents an individual block in the file integrity blockchain.
    
    Each block contains:
    - index: Position of the block in the chain (0 for Genesis Block)
    - timestamp: Unix epoch time when the block was created
    - file_name: Original name of the registered file
    - file_hash: Cryptographic SHA-256 hash of the file
    - previous_hash: SHA-256 hash of the preceding block in the chain
    - current_hash: SHA-256 hash of this block's contents
    - nonce: Counter used for Proof-of-Work mining
    - file_size: Optional human-readable file size for dashboard display
    """
    def __init__(self, index, timestamp, file_name, file_hash, previous_hash, 
                 file_size="N/A", nonce=0, current_hash=None):
        self.index = index
        self.timestamp = timestamp
        self.file_name = file_name
        self.file_hash = file_hash
        self.file_size = file_size
        self.previous_hash = previous_hash
        self.nonce = nonce
        
        # If current_hash is provided (e.g., when loading from JSON), use it;
        # otherwise, calculate it using SHA-256
        self.current_hash = current_hash if current_hash else self.calculate_hash()
        self.hash = self.current_hash  # Alias for compatibility

    def calculate_hash(self):
        """
        Uses SHA-256 to calculate the block hash.
        Combines block index, timestamp, file name, file hash, previous hash, and nonce.
        """
        block_content = (
            f"{self.index}"
            f"{self.timestamp}"
            f"{self.file_name}"
            f"{self.file_hash}"
            f"{self.previous_hash}"
            f"{self.nonce}"
        )
        return hashlib.sha256(block_content.encode('utf-8')).hexdigest()

    def mine_block(self, difficulty=2):
        """
        Educational Proof of Work: Increment nonce until block hash
        starts with a specified number of leading zeroes.
        """
        target = "0" * difficulty
        while not self.current_hash.startswith(target):
            self.nonce += 1
            self.current_hash = self.calculate_hash()
            self.hash = self.current_hash

    def to_dict(self):
        """
        Converts the Block object into a Python dictionary
        suitable for JSON serialization and web API responses.
        """
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "formatted_time": datetime.fromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
            "file_name": self.file_name,
            "file_hash": self.file_hash,
            "file_size": self.file_size,
            "previous_hash": self.previous_hash,
            "current_hash": self.current_hash,
            "hash": self.current_hash,
            "nonce": self.nonce,
            # Structured data representation for dashboard UI
            "data": {
                "filename": self.file_name,
                "file_hash": self.file_hash,
                "file_size": self.file_size,
                "message": self.file_name if self.index == 0 else ""
            }
        }


class Blockchain:
    """
    Manages the sequential chain of blocks, persistent JSON storage,
    and cryptographic validation.
    """
    def __init__(self, storage_file="blockchain_data.json", difficulty=2):
        self.storage_file = storage_file
        self.difficulty = difficulty
        self.chain = []

        # Load existing blockchain records if available; otherwise create Genesis block
        if not self.load_chain_from_file():
            self.create_genesis_block()

    def create_genesis_block(self):
        """
        Initializes the blockchain with the first block (Genesis Block).
        """
        genesis_block = Block(
            index=0,
            timestamp=time.time(),
            file_name="Genesis Block - System Initialized",
            file_hash="0" * 64,
            previous_hash="0",
            file_size="0 B"
        )
        genesis_block.mine_block(self.difficulty)
        self.chain = [genesis_block]
        self.save_chain_to_file()
        print(f"[Blockchain] Genesis block created (Hash: {genesis_block.current_hash[:16]}...)")

    def get_latest_block(self):
        """
        Returns the most recent block in the blockchain.
        """
        return self.chain[-1]

    def add_block(self, file_name, file_hash=None, file_size="N/A"):
        """
        Adds a new block containing file metadata to the blockchain.
        - Stores the previous block's hash.
        - Calculates current block hash via SHA-256 (with PoW).
        - Automatically persists updated chain to the local JSON file.
        """
        # Support passing a dictionary or keyword arguments
        if isinstance(file_name, dict):
            payload = file_name
            file_name = payload.get("filename") or payload.get("file_name", "Unknown File")
            file_hash = payload.get("file_hash", "")
            file_size = payload.get("file_size", "N/A")

        previous_block = self.get_latest_block()
        new_block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            file_name=file_name,
            file_hash=file_hash,
            previous_hash=previous_block.current_hash,
            file_size=file_size
        )
        # Mine the block to satisfy Proof of Work
        new_block.mine_block(self.difficulty)
        
        # Append to chain and persist to JSON storage
        self.chain.append(new_block)
        self.save_chain_to_file()
        
        print(f"[Blockchain] Block #{new_block.index} added for '{file_name}' (Hash: {new_block.current_hash[:16]}...)")
        return new_block

    def is_chain_valid(self):
        """
        Validates the integrity of the blockchain:
        1. Checks whether every block's stored hash matches its recalculated SHA-256 hash.
        2. Checks whether every block points to the previous block's hash.
        3. Checks whether Proof of Work difficulty criteria is met.
        """
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # 1. Verify block data has not been modified
            if current.current_hash != current.calculate_hash():
                return False, f"Integrity Failure: Block #{current.index} data has been altered!"

            # 2. Verify chain linkage (previous hash pointer)
            if current.previous_hash != previous.current_hash:
                return False, f"Integrity Failure: Block #{current.index} previous hash does not match Block #{previous.index} hash!"

            # 3. Verify Proof of Work
            if not current.current_hash.startswith("0" * self.difficulty):
                return False, f"Integrity Failure: Block #{current.index} does not satisfy Proof of Work difficulty!"

        return True, "Blockchain integrity is valid and intact."

    def find_file(self, file_hash):
        """
        Searches the blockchain (excluding Genesis) for a record matching the given file hash.
        Returns the Block if found, or None otherwise.
        """
        for block in reversed(self.chain[1:]):
            if block.file_hash == file_hash:
                return block
        return None

    def save_chain_to_file(self):
        """
        Saves all blocks in the blockchain to the local JSON file.
        """
        try:
            chain_data = [block.to_dict() for block in self.chain]
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(chain_data, f, indent=4)
            return True
        except Exception as e:
            print(f"[Blockchain] Error saving chain to {self.storage_file}: {e}")
            return False

    def load_chain_from_file(self):
        """
        Loads blockchain records from the local JSON file if it exists.
        Reconstructs Block objects and validates the chain.
        """
        if not os.path.exists(self.storage_file):
            return False

        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                raw_data = f.read().strip()
                if not raw_data:
                    return False
                chain_data = json.loads(raw_data)

            if not isinstance(chain_data, list) or len(chain_data) == 0:
                return False

            loaded_chain = []
            for item in chain_data:
                # Extract file metadata supporting both direct keys and nested data dict
                file_name = item.get("file_name") or item.get("data", {}).get("filename", "Unknown")
                file_hash = item.get("file_hash") or item.get("data", {}).get("file_hash", "")
                file_size = item.get("file_size") or item.get("data", {}).get("file_size", "N/A")
                current_hash = item.get("current_hash") or item.get("hash")

                block = Block(
                    index=item["index"],
                    timestamp=item["timestamp"],
                    file_name=file_name,
                    file_hash=file_hash,
                    previous_hash=item["previous_hash"],
                    file_size=file_size,
                    nonce=item.get("nonce", 0),
                    current_hash=current_hash
                )
                loaded_chain.append(block)

            self.chain = loaded_chain
            is_valid, msg = self.is_chain_valid()
            if is_valid:
                print(f"[Blockchain] Successfully loaded {len(self.chain)} blocks from '{self.storage_file}'.")
            else:
                print(f"[Blockchain] Warning: Loaded chain validation alert: {msg}")
            return True

        except Exception as e:
            print(f"[Blockchain] Could not load '{self.storage_file}': {e}. Rebuilding Genesis block.")
            return False


if __name__ == "__main__":
    print("=" * 65)
    print(" Blockchain-Based File Integrity System - Standalone CLI Test")
    print("=" * 65)

    # Instantiate blockchain with local JSON storage
    demo_storage = "blockchain_data.json"
    bc = Blockchain(storage_file=demo_storage, difficulty=2)

    # 1. Show Genesis Block
    genesis = bc.chain[0]
    print(f"\n[1] Genesis Block:")
    print(f"    Index:         {genesis.index}")
    print(f"    File Name:     {genesis.file_name}")
    print(f"    Current Hash:  {genesis.current_hash}")

    # 2. Add sample file
    print("\n[2] Registering a sample file record...")
    new_blk = bc.add_block(
        file_name="project_report.pdf",
        file_hash="a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e",
        file_size="1.2 MB"
    )
    print(f"    Added Block #{new_blk.index}")
    print(f"    File Name:     {new_blk.file_name}")
    print(f"    Previous Hash: {new_blk.previous_hash}")
    print(f"    Current Hash:  {new_blk.current_hash}")
    print(f"    Nonce (PoW):   {new_blk.nonce}")

    # 3. Validate Chain Integrity
    is_valid, msg = bc.is_chain_valid()
    print(f"\n[3] Chain Integrity Check:")
    print(f"    Valid: {is_valid}")
    print(f"    Message: {msg}")

    # 4. Search for file
    search_hash = "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
    found = bc.find_file(search_hash)
    print(f"\n[4] Querying File Hash:")
    print(f"    Found in Block #{found.index} ({found.file_name})")

    print("\n" + "=" * 65)
    print(f" Records persistently saved in '{demo_storage}'.")
    print("=" * 65)

