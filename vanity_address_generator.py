import hashlib
import base58
import ecdsa
import os
import time
import logging
import multiprocessing
from typing import Tuple, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Evrmore address prefix (0x21 in hex)
EVR_PREFIX = 33
# Evrmore WIF prefix (0x80 in hex for private keys starting with 'E')
EVR_WIF_PREFIX = 128

def generate_private_key() -> bytes:
    return os.urandom(32)

def private_key_to_wif(private_key: bytes) -> str:
    extended_key = bytes([EVR_WIF_PREFIX]) + private_key + b'\x01'  # compressed key
    sha256_1 = hashlib.sha256(extended_key).digest()
    sha256_2 = hashlib.sha256(sha256_1).digest()
    checksum = sha256_2[:4]
    return base58.b58encode(extended_key + checksum).decode('utf-8')

def public_key_to_address(public_key: bytes) -> str:
    sha256_hash = hashlib.sha256(public_key).digest()
    ripemd160_hash = hashlib.new('ripemd160', sha256_hash).digest()
    network_hash = bytes([EVR_PREFIX]) + ripemd160_hash
    checksum = hashlib.sha256(hashlib.sha256(network_hash).digest()).digest()[:4]
    binary_address = network_hash + checksum
    return base58.b58encode(binary_address).decode('utf-8')

def generate_keypair() -> Tuple[bytes, str]:
    private_key = generate_private_key()
    sk = ecdsa.SigningKey.from_string(private_key, curve=ecdsa.SECP256k1)
    public_key = b'\x02' + sk.get_verifying_key().to_string()[:32]  # compressed public key
    address = public_key_to_address(public_key)
    return private_key, address

def worker(suffix: str, result_queue: multiprocessing.Queue, stop_event: multiprocessing.Event):
    attempts = 0
    start_time = time.time()
    while not stop_event.is_set():
        private_key, address = generate_keypair()
        attempts += 1
        if attempts % 10000 == 0:  # Less frequent logging to reduce overhead
            elapsed_time = time.time() - start_time
            rate = attempts / elapsed_time
            logging.info(f"Process {multiprocessing.current_process().name}: {attempts} attempts, {rate:.2f} attempts/second")
        
        if address.endswith(suffix):
            elapsed_time = time.time() - start_time
            rate = attempts / elapsed_time
            logging.info(f"Process {multiprocessing.current_process().name}: Found matching address after {attempts} attempts, rate: {rate:.2f} attempts/second")
            result_queue.put((private_key, address, attempts))
            return

def generate_vanity_address(suffix: str, num_processes: Optional[int] = None) -> Tuple[Optional[bytes], Optional[str]]:
    if num_processes is None:
        num_processes = os.cpu_count()
    start_time = time.time()
    logging.info(f"Starting search for vanity address with suffix '{suffix}' using {num_processes} processes")
    
    result_queue = multiprocessing.Queue()
    stop_event = multiprocessing.Event()
    processes = []
    for _ in range(num_processes):
        p = multiprocessing.Process(target=worker, args=(suffix, result_queue, stop_event))
        processes.append(p)
        p.start()

    try:
        # Wait for a result
        private_key, address, attempts = result_queue.get()
        stop_event.set()  # Signal all processes to stop
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt detected. Stopping all processes.")
        stop_event.set()
        private_key, address, attempts = None, None, 0
    finally:
        # Wait for all processes to finish
        for p in processes:
            p.join()

    elapsed_time = time.time() - start_time
    if private_key and address:
        rate = attempts / elapsed_time
        logging.info(f"Found vanity address after approximately {attempts} attempts")
        logging.info(f"Total time: {elapsed_time:.2f} seconds")
        logging.info(f"Approximate rate: {rate:.2f} attempts/second")
    else:
        logging.info("Search terminated without finding a matching address.")

    return private_key, address

if __name__ == "__main__":
    multiprocessing.freeze_support()  # Necessary for Windows
    
    # Prompt the user for the desired suffix
    suffix = input("Enter the desired suffix for your vanity address: ").strip()
    
    # Validate user input
    if not suffix:
        print("Error: Suffix cannot be empty.")
    elif not suffix.isalnum():
        print("Error: Suffix must contain only letters and numbers.")
    else:
        private_key, address = generate_vanity_address(suffix=suffix)
        if private_key:
            wif_key = private_key_to_wif(private_key)
            p2pkh_key = f"p2pkh:{wif_key}"
            print(f"Address: {address}")
            print(f"Private Key (p2pkh format): {p2pkh_key}")
        else:
            print("Failed to find a matching address.")
