import time
import json
import random
import paho.mqtt.client as mqtt

# ==========================================
# CONFIGURATION
# ==========================================
BROKER = "localhost"
PORT = 1883
TOPIC_PREFIX = "parking/P"
TOPIC_AVAILABLE = "parking/available"

# 10 places de parking au total. 
# True = Libre (Vert), False = Occupée (Rouge)
slots = {f"{i}": True for i in range(1, 11)}

# ==========================================
# FONCTIONS MQTT
# ==========================================
def on_connect(client, userdata, flags, rc):
    """Callback lors de la connexion au broker."""
    if rc == 0:
        print(f"✅ Connecté au broker MQTT Mosquitto ({BROKER}:{PORT})")
    else:
        print(f"❌ Échec de la connexion. Code d'erreur : {rc}")

def calculate_available():
    """Calcule le nombre global de places disponibles."""
    return sum(1 for is_free in slots.values() if is_free)

# ==========================================
# SIMULATION PRINCIPALE
# ==========================================
if __name__ == "__main__":
    print("🚗 Lancement du simulateur Smart Parking...")
    
    # Configuration du client MQTT
    client = mqtt.Client()
    client.on_connect = on_connect
    
    try:
        # Connexion au broker
        client.connect(BROKER, PORT, 60)
        client.loop_start()  # Démarrage de la boucle asynchrone
        
        # --- INITIALISATION ---
        # Envoi de l'état initial : toutes les places libres
        for slot in slots:
            topic = f"{TOPIC_PREFIX}{slot}"
            payload = json.dumps({"state": "free", "slot": slot})
            client.publish(topic, payload, retain=True)
            
        # Publication de la jauge (disponibilité : 10)
        client.publish(TOPIC_AVAILABLE, calculate_available(), retain=True)
        print("🚥 États initiaux (Libre) synchronisés. Début de la simulation en temps réel...\n")
        
        # --- BOUCLE DE CHANGEMENT ---
        while True:
            # Attend un intervalle aléatoire entre 3 et 5 secondes
            time.sleep(random.uniform(3.0, 5.0))
            
            # Choisir une place de P1 à P10 au hasard
            target_id = str(random.randint(1, 10))
            
            # Inverser l'état (true -> false, ou false -> true)
            slots[target_id] = not slots[target_id]
            
            # Préparer le message JSON (state + l'ID pour plus de flexibilité)
            state_str = "free" if slots[target_id] else "occupied"
            payload = json.dumps({"state": state_str, "slot": f"P{target_id}"})
            topic = f"{TOPIC_PREFIX}{target_id}"
            
            # Envoyer la nouvelle information sur le topic du parking
            client.publish(topic, payload, retain=True)
            
            # Mettre à jour le compteur global des places libres
            available_count = calculate_available()
            client.publish(TOPIC_AVAILABLE, available_count, retain=True)
            
            # Affichage console (historique dans le terminal)
            icon = "🟢" if state_str == "free" else "🔴"
            status_fr = "LIBRE" if state_str == "free" else "OCCUPÉE"
            time_log = time.strftime('%H:%M:%S')
            
            print(f"[{time_log}] {icon} Place P{target_id} -> {status_fr} | 🚘 Places disponibles : {available_count}/10")
            
    except KeyboardInterrupt:
        print("\n🛑 Simulation arrêtée manuellement. Déconnexion...")
        client.loop_stop()
        client.disconnect()
    except Exception as e:
        print(f"\n❌ Une erreur inattendue est survenue : {e}")
