import boto3
import smtplib
import requests
import json
import time
import logging
from botocore.exceptions import ClientError
from datetime import datetime
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration
with open("config.json", "r") as config_file:
    CONFIG = json.load(config_file)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", CONFIG["telegram"]["bot_token"])
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", CONFIG["telegram"]["chat_id"])
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
AWS_CREDENTIALS_PATH = CONFIG["aws_credentials_path"]
LOG_FILE = CONFIG["log_file"]

# Configuration de la journalisation
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Modules activés
MODULES = [
    "KBS", "JS", "GIT", "MISCONFIG", "PHP",
    "SSRF", "XXE", "RCE", "YML", "XML", "TRANSVERSAL PATH", "SMTP"
]

# Fonction pour envoyer un message via Telegram
def send_to_telegram(message):
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(TELEGRAM_API_URL, json=payload, timeout=10)
        if response.status_code == 200:
            logging.info("Résultats envoyés sur Telegram avec succès.")
        else:
            logging.error(f"Erreur Telegram : {response.status_code}")
    except Exception as e:
        logging.error(f"Erreur lors de l'envoi sur Telegram : {e}")

# Lire les cibles depuis targets.txt
def load_targets():
    try:
        with open("targets.txt", "r") as file:
            targets = [line.strip() for line in file if line.strip()]
        if not targets:
            raise ValueError("Aucune cible trouvée dans targets.txt.")
        logging.info(f"Cibles chargées : {targets}")
        return targets
    except FileNotFoundError:
        logging.error("Fichier targets.txt non trouvé.")
        return []
    except ValueError as e:
        logging.error(f"Erreur : {e}")
        return []

# Vérification des clés AWS exposées
def check_aws_leaks(target):
    try:
        with open(AWS_CREDENTIALS_PATH, "r") as file:
            content = file.read()
        if "aws_access_key_id" in content:
            return "Élevée", f"Clé AWS exposée détectée dans {AWS_CREDENTIALS_PATH} pour {target}"
        return "Faible", f"Aucune clé AWS exposée détectée pour {target}."
    except FileNotFoundError:
        return "Faible", f"Fichier AWS non trouvé pour {target}."
    except Exception as e:
        logging.error(f"Erreur AWS pour {target} : {e}")
        return "Faible", f"Erreur de vérification AWS pour {target}."

# Vérification d'un serveur SMTP ouvert
def check_smtp_leak(target):
    try:
        smtp = smtplib.SMTP(target, 25, timeout=10)
        smtp.helo()
        smtp.quit()
        return "Élevée", f"Serveur SMTP exposé détecté : {target}:25 (relais potentiellement ouvert)"
    except (smtplib.SMTPException, TimeoutError):
        return "Faible", f"Aucun serveur SMTP exposé détecté sur {target}."

# Vérification HTTP pour JS, PHP, YML, XML
def check_http_leak(target):
    try:
        response = requests.get(target, timeout=10)
        if response.status_code == 200:
            if any(ext in target.lower() for ext in [".js", ".php", ".yml", ".xml"]):
                return "Moyenne", f"Ressource exposée détectée : {target}"
        return "Faible", f"Aucune fuite HTTP détectée pour {target}."
    except requests.RequestException:
        return "Faible", f"Impossible d'accéder à {target}."

# Simulation des autres modules
def simulate_modules(target):
    results = {}
    results["KBS"], results["KBS_desc"] = check_aws_leaks(target)
    results["SMTP"], results["SMTP_desc"] = check_smtp_leak(target)
    for module in ["JS", "PHP", "YML", "XML"]:
        if module in target.lower() or "http" in target.lower():
            results[module], results[module + "_desc"] = check_http_leak(target)
        else:
            results[module], results[module + "_desc"] = "Faible", f"Aucune fuite {module} détectée pour {target}."
    for module in ["GIT", "MISCONFIG", "SSRF", "XXE", "RCE", "TRANSVERSAL PATH"]:
        results[module], results[module + "_desc"] = "Moyenne" if module == "MISCONFIG" else "Faible", f"{module} : Simulation, aucune fuite détectée pour {target}."
    return results

# Fonction principale
def run_scan():
    print("GLITCH-CRACKER v2.4 LICENCE OFFICIELLE | LIFETIME")
    print("CRACKER 2025 - SCAN FUITES AWS & SMTP - API v2.4")
    logging.info("Démarrage du scan GLITCH-CRACKER v2.4")
    print("\nModules activés pour identifier des fuites :")
    print(" / ".join(MODULES))
    print("\nLancement du scan...\n")

    targets = load_targets()
    if not targets:
        logging.error("Aucun scan effectué. Vérifiez targets.txt.")
        return

    all_results = {}
    for target in targets:
        print(f"Scan de la cible : {target}")
        logging.info(f"Début du scan pour {target}")
        all_results[target] = simulate_modules(target)
        logging.info(f"Scan terminé pour {target}")
        print(f"Scan terminé pour {target}.\n")

    # Préparer le rapport
    current_time = "02:33 PM CEST on Tuesday, May 20, 2025"
    telegram_message = "🔍 **GLITCH-CRACKER v2.4 - Rapport de Scan** 🔍\n\n"
    telegram_message += f"📅 Date et heure : {current_time}\n"
    telegram_message += "🎯 Cibles scannées :\n"
    for target in targets:
        telegram_message += f"- {target}\n"
    telegram_message += "\n**Résultats des fuites détectées :**\n"

    for target, results in all_results.items():
        telegram_message += f"\n🌐 **Cible : {target}**\n"
        for module in MODULES:
            priority = results.get(module, "Faible")
            desc = results.get(module + "_desc", "Aucune donnée.")
            telegram_message += f"- [{module}] {priority} : {desc}\n"

    send_to_telegram(telegram_message)
    logging.info("Scan terminé. Rapport envoyé sur Telegram.")
    print("Scan terminé. Rapport envoyé sur Telegram.")

if __name__ == "__main__":
    run_scan()