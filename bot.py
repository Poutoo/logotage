from PIL import Image
import os
import discord
import config
import image_process
import logging
import logging.handlers
import sys
import requests
import json

import keep_alive # Import du fichier créé
keep_alive.keep_alive()

def setup_logging():
    # Crée un dossier 'logs' s'il n'existe pas
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Configuration des logs pour écrire dans un fichier 'bot.log'
    logging.basicConfig(
        level=logging.INFO, # Niveau d'enregistrement : INFO et plus haut
        format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        handlers=[
            # 1. Écrit dans un fichier (max 5 Mo, conserve 5 fichiers)
            logging.handlers.RotatingFileHandler(
                filename='logs/bot.log',
                encoding='utf-8',
                maxBytes=5 * 1024 * 1024,  # 5 Mo
                backupCount=5,
            ),
            # 2. Affiche aussi dans la console (VS Code)
            logging.StreamHandler(sys.stdout)
        ]
    )

# Appel de la fonction de configuration avant de lancer le client
setup_logging()

# Le logger de discord.py sera automatiquement configuré
logger = logging.getLogger('discord')

intents = discord.Intents.default()
intents.message_content = True 
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    logger.info(f'Bot démarré et connecté en tant que {client.user}')
    try:
        # Importation du Webhook URL depuis config.py
        webhook = discord.Webhook.from_url(config.ERROR_WEBHOOK_URL, client=client)
        
        # Création de l'Embed de succès de connexion
        embed = discord.Embed(
            title="🟢 Bot Démarré et Opérationnel",
            description=f"Le bot est en ligne et opère sur **{len(client.guilds)} serveurs**.",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Connecté en tant que {client.user.name}")
        
        await webhook.send(embed=embed)
        
    except Exception as e:
        # Si même le Webhook d'alerte ne fonctionne pas, on le log localement
        logger.warning(f"Impossible d'envoyer le log de connexion via Webhook : {e}")

@client.event
async def on_disconnect():
    """
    Utilise la méthode synchrone (requests) pour garantir que l'alerte soit envoyée 
    même si le processus est en train de s'arrêter.
    """
    
    # 1. Log local pour un enregistrement permanent
    logger.critical('Le bot s\'est déconnecté du Gateway Discord. Tentative de reconnexion automatique en cours...')

    # 2. PRÉPARATION DE L'EMBED
    embed = discord.Embed(
        title="🔴 ALERTE : BOT DÉCONNECTÉ",
        description="Le bot a perdu sa connexion au Gateway Discord. Une reconnexion est probablement en cours. **Surveillez le log de reconnexion !**",
        color=discord.Color.red()
    )
    embed.set_footer(text=f"Déconnexion détectée à : {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # 3. ENVOI SYNCHRONE DU WEBHOOK
    try:
        # Prépare le payload (le contenu JSON de la requête)
        payload = {
            'embeds': [embed.to_dict()] # Convertit l'objet Embed en dictionnaire pour le JSON
        }
        
        # Envoi synchrone qui ne nécessite pas d'await
        requests.post(
            config.ERROR_WEBHOOK_URL, 
            json=payload, 
            timeout=5 # Ajout d'un timeout de 5s pour ne pas bloquer trop longtemps
        )
        
    except Exception as e:
        # Si l'envoi du Webhook échoue (ex: mauvaise URL ou coupure réseau), on le log localement
        logger.warning(f"Impossible d'envoyer l'alerte de déconnexion Webhook : {e}")
        
@client.event
async def on_message(message):
    
    # Ignorer les messages de tous les bots, y compris le nôtre
    if message.author.bot:
        return
        
    # Vérifier si le message est dans un des salons ciblés
    if message.channel.id not in config.CHANNEL_IDS:
        return
        
    # Vérifier si le message contient au moins une pièce jointe
    if message.attachments:
        attachment = message.attachments[0]
        
        # Vérifier si c'est bien une image (simplifié)
        if attachment.content_type.startswith('image/'):
            
            # Définir les chemins des fichiers
            original_filename = f"original_{message.id}_{attachment.filename}"
            logoted_filename = f"logoted_{message.id}_{attachment.filename}"
            
            # Tenter le traitement
            try:
                await attachment.save(original_filename)
                
                success = image_process.add_watermark(original_filename, logoted_filename)
                
                if success:
                    # --- CRÉATION DE L'EMBED DE SUCCÈS ---
                    embed = discord.Embed(
                        title="✅ Logotage terminé",
                        description=f"L'image de {message.author.mention} a été traitée avec succès.",
                        color=discord.Color.green()
                    )
                    timestamp_text = message.created_at.strftime('Date : %Y-%m-%d - %H:%M:%S')
                    embed.set_footer(text=timestamp_text)
                    
                    # 1. ENVOI de l'Embed et du Fichier
                    await message.channel.send(
                        embed=embed, 
                        file=discord.File(logoted_filename)
                    )
                    
                    # 2. SUPPRESSION du message original
                    try:
                        await message.delete() 
                    except discord.Forbidden:
                        # --- ERREUR DE PERMISSION DE SUPPRESSION ---
                        # On envoie un Embed distinct pour l'erreur de permission (visible uniquement si la suppression échoue)
                        error_embed = discord.Embed(
                            title=f"⚠️ Message de {message.author.name} non supprimé",
                            description=f"J'ai logoté l'image, mais je n'ai pas la permission de supprimer le message original. **Contactez <@{config.DEVELOPER_ID}>** pour corriger les permissions du bot (permission 'Gérer les messages').",
                            color=discord.Color.orange()
                        )
                        timestamp_text = message.created_at.strftime('Date : %Y-%m-%d - %H:%M:%S')
                        embed.set_footer(text=timestamp_text)
                        await message.channel.send(embed=error_embed, reference=message)
                        
                else:
                    # --- ERREUR DE TRAITEMENT (Pillow) ---
                    error_embed = discord.Embed(
                        title="❌ Erreur de Traitement de l'Image",
                        description=f"{message.author.mention}, votre image n'a pas pu être logotée. Si cette erreur persiste, **contactez <@{config.DEVELOPER_ID}>**.",
                        color=discord.Color.red()
                    )
                    timestamp_text = message.created_at.strftime('Date : %Y-%m-%d - %H:%M:%S')
                    embed.set_footer(text=timestamp_text)
                    await message.channel.send(embed=error_embed, reference=message)

            except Exception as e:

                logger.error(f"Erreur critique inattendue : {e}", exc_info=True)    

                error_embed = discord.Embed(
                    title="🚨 Erreur Critique du Bot", 
                    description=f"Une erreur inattendue s'est produite lors du traitement de votre image. L'erreur a été notifiée à **<@{config.DEVELOPER_ID}>** pour diagnostic.",
                    color=discord.Color.red() 
                )
                
                error_embed.add_field(
                    name="Détails pour le développeur (Console)",
                    value=f"Erreur : `{e}`", 
                    inline=False
                )
                timestamp_text = message.created_at.strftime('Date : %Y-%m-%d - %H:%M:%S')
                error_embed.set_footer(text=timestamp_text)
                
                # Envoi de l'Embed, avec une référence au message original pour la clarté
                await message.channel.send(embed=error_embed, reference=message)

                try:
                    webhook = discord.Webhook.from_url(config.ERROR_WEBHOOK_URL, client=client)
                    
                    alert_embed = discord.Embed(
                        title=f"🔴 ERREUR CRITIQUE (CLIENT: {message.guild.name})",
                        description=f"Le bot a rencontré une erreur non gérée lors du traitement d'une image. L'erreur complète a été enregistrée dans `bot.log`.",
                        color=discord.Color.dark_red()
                    )
                    alert_embed.add_field(name="Erreur", value=f"`{e}`")
                    alert_embed.add_field(name="Salon", value=message.channel.name)
                    alert_embed.add_field(name="Utilisateur", value=message.author.name)

                    await webhook.send(embed=alert_embed)
                except Exception as webhook_e:
                    logger.warning(f"Impossible d'envoyer l'alerte Webhook : {webhook_e}")
                
            finally:
                # Assurez-vous que le nettoyage est toujours la dernière étape
                image_process.cleanup_files(original_filename, logoted_filename)
                
client.run(config.TOKEN)