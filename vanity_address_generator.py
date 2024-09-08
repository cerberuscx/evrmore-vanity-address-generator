import hashlib
import base58
import ecdsa
import os
import time
import logging
import multiprocessing

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Evrmore address prefix (0x21 in hex)
EVR_PREFIX = 33
# Evrmore WIF prefix (0x80 in hex for private keys starting with 'E')
EVR_WIF_PREFIX = 128
SUFFIX = 'Enso'  # Set your desired suffix here

def generate_private_key():
    return os.urandom(32)

def private_key_to_wif(private_key):
    extended_key = bytes([EVR_WIF_PREFIX]) + private_key + b'\x01'  # compressed key
    sha256_1 = hashlib.sha256(extended_key).digest()
    sha256_2 = hashlib.sha256(sha256_1).digest()
    checksum = sha256_2[:4]
    return base58.b58encode(extended_key + checksum).decode('utf-8')

def public_key_to_address(public_key):
    sha256_hash = hashlib.sha256(public_key).digest()
    ripemd160_hash = hashlib.new('ripemd160', sha256_hash).digest()
    network_hash = bytes([EVR_PREFIX]) + ripemd160_hash
    checksum = hashlib.sha256(hashlib.sha256(network_hash).digest()).digest()[:4]
    binary_address = network_hash + checksum
    return base58.b58encode(binary_address).decode('utf-8')

def generate_keypair():
    private_key = generate_private_key()
    sk = ecdsa.SigningKey.from_string(private_key, curve=ecdsa.SECP256k1)
    public_key = b'\x02' + sk.get_verifying_key().to_string()[:32]  # compressed public key
    address = public_key_to_address(public_key)
    return private_key, address

def worker(suffix, result_queue):
    attempts = 0
    start_time = time.time()
    while True:
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

def generate_vanity_address(suffix, num_processes=None):
    if num_processes is None:
        num_processes = os.cpu_count()

    start_time = time.time()
    logging.info(f"Starting search for vanity address with suffix '{suffix}' using {num_processes} processes")
    
    result_queue = multiprocessing.Queue()
    processes = []

    for _ in range(num_processes):
        p = multiprocessing.Process(target=worker, args=(suffix, result_queue))
        processes.append(p)
        p.start()

    # Wait for a result
    private_key, address, attempts = result_queue.get()

    # Terminate all processes
    for p in processes:
        p.terminate()

    # Wait for all processes to finish
    for p in processes:
        p.join()

    elapsed_time = time.time() - start_time
    rate = attempts / elapsed_time
    logging.info(f"Found vanity address after approximately {attempts} attempts")
    logging.info(f"Total time: {elapsed_time:.2f} seconds")
    logging.info(f"Approximate rate: {rate:.2f} attempts/second")

    return private_key, address

if __name__ == "__main__":
    multiprocessing.freeze_support()  # Necessary for Windows
    private_key, address = generate_vanity_address(suffix=SUFFIX)
    if private_key:
        wif_key = private_key_to_wif(private_key)
        p2pkh_key = f"p2pkh:{wif_key}"
        print(f"Address: {address}")
        print(f"Private Key (p2pkh format): {p2pkh_key}")
    else:
        print("Failed to find a matching address.")
