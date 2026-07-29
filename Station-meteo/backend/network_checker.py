# ============================================================
# IMPORT DE LA BIBLIOTHÈQUE SOCKET
# ============================================================

# Permet de créer des connexions réseau bas niveau
#
# Une socket est un point de communication permettant
# à un programme de dialoguer avec un autre ordinateur.
import socket


# ============================================================
# FONCTION DE TEST DE LA CONNEXION INTERNET
# ============================================================

def is_network_available(
    host: str = "8.8.8.8",
    port: int = 53,
    timeout: float = 2.0
) -> bool:

    """
    Vérifie si la machine possède un accès réseau.

    La méthode consiste à essayer de se connecter
    au DNS public de Google.

    Retour :
        True  -> réseau disponible
        False -> pas de connexion
    """

    try:

        # Définit un délai maximum d'attente.
        #
        # Ici :
        # 2 secondes
        #
        # Si aucune réponse n'arrive dans ce délai,
        # une exception sera déclenchée.
        socket.setdefaulttimeout(timeout)

        # Création d'une socket réseau.
        #
        # AF_INET :
        # protocole IPv4
        #
        # SOCK_STREAM :
        # protocole TCP
        #
        # TCP garantit que les données arrivent correctement.
        socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        ).connect(

            # Adresse cible
            #
            # 8.8.8.8 = DNS public Google
            #
            # Port 53 = port DNS
            (host, port)
        )

        # Si la connexion réussit,
        # Internet est considéré comme disponible.
        return True

    except OSError:

        # Si une erreur réseau survient :
        #
        # absence d'Internet
        # câble débranché
        # Wi-Fi coupé
        # pare-feu bloquant la connexion
        #
        # on retourne False.
        return False