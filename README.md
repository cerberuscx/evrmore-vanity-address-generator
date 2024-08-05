# Evrmore Vanity Address Generator

This script generates a vanity address for Evrmore (EVR) using multiprocessing for efficient address generation.

## Requirements

- **Python 3.x**
- **Libraries**: `hashlib`, `base58`, `ecdsa`, `os`, `time`, `logging`, `multiprocessing`

Install dependencies using pip:
```bash
pip install base58 ecdsa
```


## Usage
Save the script to a file, for example, vanity_address_generator.py, and run it:
```
python3 vanity_address_generator.py
```


## Important Information

- **Valid Characters**: Evrmore addresses use Base58 encoding, which means not all characters are valid. The valid characters are:
```
1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz
```
- **Security Warning**: The private key is generated and stored in memory. Ensure that you keep it secure and do not share it with anyone.

- **Importing to Evrmore Electrum**: Use the following command in the Electrum console to import the private key:
```python
importprivkey('your_private_key_wif')
```
- **Performance Note**: Generating a vanity address with an all-uppercase prefix (e.g., "ENSO") can take significantly longer than a mixed-case prefix due to the increased complexity of matching the case-sensitive characters.


## License
This project is licensed under the MIT License.
