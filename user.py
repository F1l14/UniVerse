import os
import json
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
class User:
    def __init__(self):
        pass
    
    def login(self):
        if not os.path.isfile("data/user_credentials.json"):
            self.register()
        
        with open("data/user_credentials.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            encryption = input("Decrypt Password: ")
            encryption = pad(encryption.encode(), 16)  # pad the password to be a multiple of 16 bytes for AES compatibility
            cipher = AES.new(encryption, AES.MODE_ECB)
            # Decode the base64 encoded username and password
            enc_username = base64.b64decode(data["username"])
            enc_password = base64.b64decode(data["password"])
            # Decrypt the username and password
            username = unpad(cipher.decrypt(enc_username), 16).decode('utf-8')
            password = unpad(cipher.decrypt(enc_password), 16).decode('utf-8') 
            print(f"Username: {username}")
            print(f"Password: {password}")
            return username, password

    def register(self):
        if not os.path.exists("data"):
            os.mkdir("data")
        if not os.path.isfile("/data/user_credentials.text"):
            encryption = input("Decrypt Password: ")
            # pad the password to be a multiple of 16 bytes for AES compatibility
            encryption = pad(encryption.encode(), 16)
            cipher = AES.new(encryption, AES.MODE_ECB)
            username = input("Username: ")
            password = input("Password: ")
            
            # Encrypt the username and password after converting them to bytes
            enc_username = cipher.encrypt(pad(username.encode(), 16))
            enc_password = cipher.encrypt(pad(password.encode(), 16))
            data = {
                "username": base64.b64encode(enc_username).decode('utf-8'),
                "password": base64.b64encode(enc_password).decode('utf-8')
            }
            with open("data/user_credentials.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)