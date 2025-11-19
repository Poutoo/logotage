# Fichier : keep_alive.py
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import logging

# On désactive les logs du serveur web pour ne pas polluer la console
logging.getLogger("werkzeug").setLevel(logging.ERROR)

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Gère les requêtes classiques (Navigateur)"""
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"I am alive")

    def do_HEAD(self):
        """Gère les requêtes de surveillance (UptimeRobot)"""
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        # Cette fonction vide empêche le serveur d'afficher chaque requête dans la console
        return

def run():
    server_address = ('', 8000)
    # On gère l'erreur si le port est déjà pris (redémarrage rapide)
    try:
        httpd = HTTPServer(server_address, SimpleHandler)
        print("✅ Serveur Keep-Alive démarré sur le port 8000")
        httpd.serve_forever()
    except OSError:
        print("⚠️ Le port 8000 est déjà occupé, le serveur tourne probablement déjà.")

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()