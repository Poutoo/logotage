# Fichier : image_processor.py

from PIL import Image
import os
import config 

def add_watermark(input_image_path, output_image_path):
    """
    Applique le logo sur l'image de base.
    Le logo_path est maintenant tiré du fichier config.
    """

    # Simulation de l'erreur 413 pour les tests (à retirer en production)
    # file_size_kb = os.path.getsize(input_image_path) / 1024
    # if file_size_kb < 100:
    #     raise Exception("413 Payload Too Large (Simulé)")
    
    try:
        # Utilisation de config.LOGO_PATH
        base_image = Image.open(input_image_path).convert("RGBA")
        logo = Image.open(config.LOGO_PATH).convert("RGBA")
        
        # --- 1. Redimensionnement du Logo (inchangé) ---
        logo_width = int(base_image.width * 0.2)
        logo_height = int(logo.height * (logo_width / logo.width))
        logo = logo.resize((logo_width, logo_height))

        # --- 2. Positionnement (inchangé) ---
        x = base_image.width - logo_width - 15
        y = base_image.height - logo_height - 20
        
        # --- 3. Collage du Logo ---
        base_image.paste(logo, (x, y), logo)

        # --- 4. Sauvegarde avec Compression (pour éviter l'erreur 413) ---
        if output_image_path.lower().endswith(('.jpg', '.jpeg')):
            base_image.convert("RGB").save(output_image_path, "JPEG", quality=85)
        else:
            base_image.save(output_image_path, "PNG")
        
        return True

    except Exception as e:
        raise e 
        
# ----------------------------------------------------------------------

def cleanup_files(*file_paths):
    """Nettoie les fichiers temporaires après traitement."""
    for path in file_paths:
        if os.path.exists(path):
            os.remove(path)