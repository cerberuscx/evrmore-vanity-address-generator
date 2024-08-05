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
# Set your desired vanity address prefix
PREFIX = 'ENSO'

def generate_private_key():
    """Generate a random 256-bit private key."""
    return os.urandom(32)

def private_key_to_wif(private_key):
    """Convert private key to Wallet Import Format (WIF)."""
    extended_key = bytes([EVR_WIF_PREFIX]) + private_key + b'\x01'  # compressed key
    sha256_1 = hashlib.sha256(extended_key).digest()
    sha256_2 = hashlib.sha256(sha256_1).digest()
    checksum = sha256_2[:4]
    return base58.b58encode(extended_key + checksum).decode('utf-8')

def public_key_to_address(public_key):
    """Convert public key to Evrmore address."""
    sha256_hash = hashlib.sha256(public_key).digest()
    ripemd160_hash = hashlib.new('ripemd160', sha256_hash).digest()
    network_hash = bytes([EVR_PREFIX]) + ripemd160_hash
    checksum = hashlib.sha256(hashlib.sha256(network_hash).digest()).digest()[:4]
    binary_address = network_hash + checksum
    return base58.b58encode(binary_address).decode('utf-8')

def generate_keypair():
    """Generate a private key and corresponding public key and address."""
    private_key = generate_private_key()
    sk = ecdsa.SigningKey.from_string(private_key, curve=ecdsa.SECP256k1)
    public_key = b'\x02' + sk.get_verifying_key().to_string()[:32]  # compressed public key
    address = public_key_to_address(public_key)
    return private_key, address

def worker(prefix, result_queue):
    """Worker function for multiprocessing to find a vanity address."""
    attempts = 0
    start_time = time.time()
    while True:
        private_key, address = generate_keypair()
        attempts += 1
        if attempts % 1000 == 0:
            elapsed_time = time.time() - start_time
            rate = attempts / elapsed_time
            logging.info(f"Process {multiprocessing.current_process().name}: {attempts} attempts, {rate:.2f} attempts/second")
        if address.startswith(prefix):
            logging.info(f"Process {multiprocessing.current_process().name}: Found matching address after {attempts} attempts")
            result_queue.put((private_key, address, attempts))
            return

def generate_vanity_address(prefix, num_processes=None):
    """Generate a vanity address using multiprocessing."""
    if num_processes is None:
        num_processes = os.cpu_count()

    start_time = time.time()
    logging.info(f"Starting search for vanity address with prefix '{prefix}' using {num_processes} processes")
    
    result_queue = multiprocessing.Queue()
    processes = []

    for _ in range(num_processes):
        p = multiprocessing.Process(target=worker, args=(prefix, result_queue))
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
    private_key, address = generate_vanity_address(PREFIX)
    if private_key:
        wif_key = private_key_to_wif(private_key)
        p2pkh_key = f"p2pkh:{wif_key}"
        print("\n======= Vanity Address Generator =======")
        print(f"Address: {address}")
        print(f"Private Key (WIF format): {wif_key}")
        print(f"Private Key (p2pkh format): {p2pkh_key}")
        print("\n======= Important Information =======")
        print("WARNING: The private key has been generated and stored in memory. Ensure that you keep it secure and do not share it with anyone.")
        print("To import the private key into Evrmore Electrum, use the following command in the Electrum console:")
        print(f"importprivkey('{wif_key}')")
        print("Ensure you have backed up your private key securely before using it.")
    else:
        print("Failed to find a matching address.")
