import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

# Charger le fichier .env
load_dotenv()


def get_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            charset="utf8mb4",
        )
        if conn.is_connected():
            print("Connexion MySQL réussie")
            cursor = conn.cursor()
            cursor.execute("SET NAMES utf8mb4;")
            cursor.close()
            return conn
        else:
            print("Échec de la connexion MySQL")
            return None
    except Error as e:
        print(f"Erreur de connexion MySQL : {e}")
        return None
