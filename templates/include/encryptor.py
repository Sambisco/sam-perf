# encryptor.py
from cryptography.fernet import Fernet

# Utiliser la clé générée
key = b'Vd6j5vNmJ6iHdwMXpug9mAxp0PqggDhKOBJfdFeC59g='

def encryptor(action, data):
    fernet = Fernet(key)

    if action == 'encrypt':
        encrypted_data = fernet.encrypt(data.encode())
        return encrypted_data.decode()
    elif action == 'decrypt':
        decrypted_data = fernet.decrypt(data.encode()).decode()
        return decrypted_data
    else:
        raise ValueError("Action non valide. Choisir entre 'encrypt' ou 'decrypt'.")
