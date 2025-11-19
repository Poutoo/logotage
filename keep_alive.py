# Fichier : keep_alive.py
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"I am alive")

def run():
    # Écoute sur le port 8000 (standard pour Koyeb/Render)
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, SimpleHandler)
    print("Serveur Web de maintien en vie démarré sur le port 8000")
    httpd.serve_forever()

def keep_alive():
    t = Thread(target=run)
    t.daemon = True # Permet au thread de se fermer quand le bot s'arrête
    t.start()