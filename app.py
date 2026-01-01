# ====================================================================================
# ------ NutriSnap-HAI : Prototype Streamlit pour l'étude Humain-AI Interaction ------
# Comment exécuter l'application :
# python -m streamlit run app.py
# ====================================================================================

import streamlit as st
import time
import uuid
import pandas as pd
import os
from datetime import datetime

# =========================================================
#  0. CONFIGURATION GÉNÉRALE DE L’APPLICATION
# =========================================================
st.set_page_config(page_title="NutriSnap-HAI Prototype", layout="wide")

# =========================================================
#  1. STYLE VISUEL (BACKGROUND)
# =========================================================
def add_bg_from_url():
    st.markdown(
         f"""
         <style>
         .stApp {{
             background-image: url("https://raw.githubusercontent.com/Shirel25/NutriSnap-HAI/main/Images/background.webp");
             background-attachment: scroll;
             background-size: cover;
             background-position: center;
         }}
         /* Ajout d'un voile pour garder le texte lisible */
         .stApp::before {{
             content: "";
             position: absolute;
             top: 0; left: 0; width: 100%; height: 100%;
             background-color: rgba(255, 255, 255, 0.8); 
         }}
         </style>
         """,
         unsafe_allow_html=True
     )

add_bg_from_url()

# =========================================================
# 2. INITIALISATION DU SESSION STATE
# =========================================================
# Permet de conserver l'état entre les interactions Streamlit
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4()) # Identifiant anonyme

if "trial_id" not in st.session_state:    
    st.session_state.trial_id = 1                   # Numéro d'essai

if "fail_counter" not in st.session_state:
    st.session_state.fail_counter = 0               # Pour le garde-fou GF1 (2 échecs max)
    
if "consent" not in st.session_state:
    st.session_state.consent = False                # Consentement éthique
    
if "view" not in st.session_state:
    st.session_state.view = "upload"                # Gère l'affichage (upload, result, manual)

if "condition" not in st.session_state:
    st.session_state.condition = None               # Condition expérimentale (IA vs Humain seul)

if "condition_confirmed" not in st.session_state:
    st.session_state.condition_confirmed = False    # Verrouillage de la condition

if "start_time" not in st.session_state:
    st.session_state.start_time = None              # Pour le calcul du decision_time_ms


# =========================================================
# 3. FONCTION DE LOGGING
# =========================================================
def log_interaction(
    action,
    manual_input="none",
    ai_category="na",
    ai_text="na",
    ai_calories="na",
    ai_uncertainty="na",
    correct="na"
):
    """
    Enregistre UNE interaction utilisateur dans logs.csv
    """
    if st.session_state.start_time is None:
        duration = "na"
    else:
        duration = int((time.time() - st.session_state.start_time) * 1000)

    # Groupe contrôle : aucune sortie IA
    if st.session_state.condition == "Humain (H_only)":
        ai_category = "na"
        ai_text = "na"
        ai_calories = "na"
        ai_uncertainty = "na"
        correct = "na"

    log_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "session_id": st.session_state.session_id,
        "trial_id": st.session_state.trial_id,
        "condition": st.session_state.condition,

        # --- Sortie IA (atomique) ---
        "ai_category": ai_category,
        "ai_text": ai_text,
        "ai_calories": ai_calories,
        "ai_uncertainty": ai_uncertainty,

        # --- Action humaine ---
        "human_action": action,          # accept | override | reject | manual_entry
        "manual_input": manual_input,    # texte saisi par l’utilisateur
        "final_entry": manual_input if manual_input != "none" else ai_text,
        "human_intervention": 1 if action in ["override", "manual_entry"] else 0,

        # --- Métriques ---
        "explanation_variant": wiz_explanation if st.session_state.condition == "IA (H+IA)" else "na",
        "correct": correct,
        "decision_time_ms": duration

    }
    

    pd.DataFrame([log_data]).to_csv(
        "logs.csv",
        mode="a",
        index=False,
        header=not os.path.exists("logs.csv"),
        encoding="utf-8"
    )


# =========================================================
# 4. ÉCRAN DE CONSENTEMENT ÉTHIQUE (G16 / G17 / G18)
# =========================================================
if not st.session_state.consent:
    st.title("NutriSnap-HAI - Consentement")
    st.write("Bienvenue dans l'étude NutriSnap. " \
    "Nous collectons des données anonymisées sur l'interaction Humain-IA.")

    if st.checkbox("J'accepte de partager mes statistiques d'utilisation anonymement avec les labos de recherche."):
        
        if st.button("Commencer l'expérience"):
            st.session_state.consent = True
            st.rerun()

    # Empêche l'exécution du reste tant que le consentement n'est pas donné
    st.stop()

# =========================================================
# 5. SIDEBAR : MAGICIEN D'OZ (SIMULATION DE L'IA)
# =========================================================
# Cette partie est utilisée uniquement par l'expérimentateur
with st.sidebar:
    st.header("Contrôles du Magicien (WoZ)")

    # Sélection de la condition (IA) vs (Humain seul)
    if not st.session_state.condition_confirmed:
        temp_condition = st.radio(
            "Condition d'étude",
            ["IA (H+IA)", "Humain (H_only)"],
            index=None
        )

        if temp_condition is not None:
            if st.button("Confirmer la condition"):
                st.session_state.condition = temp_condition
                st.session_state.condition_confirmed = True
                st.rerun()
    
    else:
        st.markdown("### Condition d'étude (verrouillée)")
        st.success(f"Groupe : {st.session_state.condition}")


    # ------------------------------------------------------------
    # --- Précision si la condition n'est pas encore confirmée ---
    if not st.session_state.condition_confirmed:
        st.caption("⬆️ Veuillez d'abord confirmer la condition expérimentale")
    # ------------------------------------------------------------

    st.divider()
    st.subheader("Simulation de l'IA")

    # Champ indispensable pour le calcul de la Reliance
    wiz_correct = st.radio("L'IA a-t-elle raison ?", ["Y", "N"])  

    # Sortie simulée de l'IA
    wiz_dish_category = st.selectbox(
        "Plat détecté", 
        ["Pates", "Riz/Céréales", "Salade", "Fruit", "Legume", "Oeuf", "Pain",
          "Poisson", "Fromage", "Viande",
          "Sandwich", "Pizza", "Poke Bowl", "Soupe", 
          "Snack/Gouter", "Dessert", "Boisson"]
        )
    
    wiz_dish_text = st.text_input(
        "Formulation affichée à l'utilisateur",
        value=wiz_dish_category
    )
    
    wiz_uncertainty = st.select_slider(
        "Incertitude IA", 
        options=["Low", "Medium", "High"]
        )
    
    wiz_calories = st.number_input(
        "Calories estimées",
          0, 2000, 450
          )
    
    wiz_macros = st.text_input(
        "Macros (P/G/L)", # Format : "Protéines/Glucides/Lipides"
        "20g/50g/15g"
        )
    

    st.subheader("Explication IA (G4)")
    wiz_explanation = st.text_area(
        "Principaux facteurs",
        "Pâtes, sauce tomate, fromage"
    )

# =============================================================
# 5bis. GARDE-FOU GLOBAL — CONDITION EXPÉRIMENTALE OBLIGATOIRE
# =============================================================
if not st.session_state.condition_confirmed:
    st.warning(
        "⚠️ Veuillez d'abord sélectionner et confirmer la condition expérimentale "
        "dans la barre latérale pour commencer l'expérience."
    )
    st.stop()

# =========================================================
# 6. INTERFACE UTILISATEUR PRINCIPALE
# =========================================================
st.title("NutriSnap-HAI")

# =========================================================
# 6.1 VUE 1 — UPLOAD DE LA PHOTO (DÉCLENCHEUR DE L'ESSAI)
# =========================================================
if st.session_state.view == "upload":
    st.subheader(f"Essai n°{st.session_state.trial_id}")

    st.info(
    "📏 Conseil : pour une meilleure estimation des quantités, "
    "incluez votre main sur la photo comme référence de taille."
    )

    uploaded_file = st.file_uploader(
        "Prenez votre plat en photo", 
        type=["jpg", "png"]
        )
    
    if uploaded_file:  
        # Stockage de l'image pour affichage ultérieur
        st.session_state.uploaded_image = uploaded_file 

        # Redirection selon la condition expérimentale
        if st.session_state.condition == "Humain (H_only)":
            st.session_state.view = "manual"
        else:
            st.session_state.view = "wizard_prepare"

        st.rerun()

# =========================================================
# 6.1bis VUE INTERMÉDIAIRE — PRÉPARATION
# =========================================================
elif st.session_state.view == "wizard_prepare":
    st.subheader("🧙‍♂️ Préparation de la réponse IA (Magicien)")

    col_img, col_help = st.columns([8, 10])

    # --- Image observée par le magicien ---
    with col_img:
        if "uploaded_image" in st.session_state:
            st.image(
                st.session_state.uploaded_image,
                caption="Photo observée par le Magicien",
                use_container_width=True
            )

    # --- Instructions + action ---
    with col_help:
        st.info(
            "Analysez la photo ci-contre puis ajustez la sortie IA "
            "dans la barre latérale avant de l'afficher à l'utilisateur.\n\n"
            "Lorsque la réponse est prête, cliquez sur le bouton ci-dessous "
            "pour l’afficher à l’utilisateur."
        )
        
        st.markdown("")  # petit espace visuel

        if st.button("➡️ Afficher la réponse à l'utilisateur", use_container_width=True):
            # Démarrage du chronomètre pour decision_time_ms
            st.session_state.start_time = time.time()
            st.session_state.view = "result"
            st.rerun()


# =========================================================
# 6.2 VUE 2 — RÉSULTAT IA + DÉCISION UTILISATEUR
# =========================================================
elif st.session_state.view == "result":
    
    # ---------------------------------------------
    # GF2 / G10 : Abstention si incertitude élevée
    # ---------------------------------------------
    if wiz_uncertainty == "High":
        st.error("⚠️ Image de mauvaise qualité (floue ou sombre).")
        st.info("L'IA n'est pas en mesure de donner une estimation fiable.")
        
        if st.button("Reprendre une photo"):
            st.session_state.view = "upload"
            st.rerun()

        if st.button("Saisie manuelle"):
            st.session_state.view = "manual"
            st.rerun()
    
    else:
        # Affichage du résultat selon le contrat d'interaction
        st.subheader(f"Estimation IA :")

        # -----------------------------
        # Affichage image + estimation
        # -----------------------------
        col_img, col_info = st.columns([8, 10])
        
        with col_img:
            if "uploaded_image" in st.session_state:
                st.image(
                    st.session_state.uploaded_image,
                    caption="Photo du plat",
                    use_container_width=True
                )

        with col_info:
            # Badge d'incertitude actionnable (G2)
            color = {"Low": "green", "Medium": "orange"}[wiz_uncertainty]
            st.markdown(f"Confiance IA : <span style='color:{color}; font-weight:bold'>{wiz_uncertainty}</span>", unsafe_allow_html=True)
            
            st.write(f"**Plat identifié :** {wiz_dish_text}")
            st.write(f"**Énergie :** {wiz_calories} kcal")
            st.write(f"**Macros :** {wiz_macros}")
            st.info("💡 *Ceci est une estimation, n'hésitez pas à corriger !*")
        

        # -----------------------------
        # Explication IA (G4)
        # -----------------------------
        st.markdown("**Pourquoi cette estimation ?**")
        st.write(wiz_explanation)


        # -----------------------------
        # Boutons de décision (G9)
        # -----------------------------
        st.divider()
        c1, c2, c3 = st.columns(3)
        action = None

        # ACCEPTATION
        with c1:
            if st.button("✅ OK (Accepter)", use_container_width=True):
                action = "accept"
       
        # OVERRIDE (ALMOST THERE)
        with c2:
            if st.button("⚠️ ALMOST THERE (Ajuster)", use_container_width=True):
                action = "override"

        # REJET    
        with c3:
            if st.button("❌ NO (Rejeter)", use_container_width=True):
                action = "reject"        


        # -----------------------------
        # Logging de l'interaction
        # -----------------------------
        if action:
            log_interaction(
                action=action,
                ai_category=wiz_dish_category,
                ai_text=wiz_dish_text,
                ai_calories=wiz_calories,
                ai_uncertainty=wiz_uncertainty,
                correct=wiz_correct
            )
            
            # --- Transitions ---
            if action == "accept":
                # Succès : on passe à l'essai suivant
                st.session_state.trial_id += 1
                st.session_state.view = "upload"
                st.session_state.start_time = None


            elif action == "override":
                # ALMOST THERE → correction manuelle, même essai
                # Pré-remplissage du formulaire manuel avec la sortie de l'IA
                st.session_state.prefill_text = f"{wiz_dish_text}, {wiz_calories} kcal, {wiz_macros}"
                st.session_state.view = "manual"

            elif action == "reject":
                # NO → on vérifie le garde-fou GF1
                st.session_state.fail_counter += 1
                if st.session_state.fail_counter >= 2:
                    st.warning("Deux échecs consécutifs. Passage en saisie manuelle.")
                    st.session_state.view = "manual"
                    st.session_state.start_time = None

                else:
                    # Même essai, nouvelle photo
                    st.session_state.view = "upload" # Seconde chance de photo 
                
            st.rerun()


# =========================================================
# 6.3 VUE 3 — SAISIE MANUELLE (FALLBACK / OVERRIDE)
# =========================================================
elif st.session_state.view == "manual":
    st.subheader("Saisie manuelle des ingrédients")

    # col_img, col_form = st.columns([8, 10])
    col_left, col_img, col_form, col_right = st.columns([6, 8, 10, 1])
    
    # Affichage de l’image 
    with col_img:
        if "uploaded_image" in st.session_state:
            st.image(
                st.session_state.uploaded_image,
                caption="Photo du plat",
                use_container_width=True
            )

    if st.session_state.start_time is None:
        st.session_state.start_time = time.time()

    # Création du formulaire
    with st.form("manual_form"):
        ingredients = st.text_area("Listez vos ingrédients :", 
                                   value=st.session_state.get("prefill_text", "")
                                 )

        submitted = st.form_submit_button("Enregistrer le repas")

        if submitted:
            # Logging de l'interaction
            log_interaction(
                action="manual_entry",
                manual_input=ingredients
            )

            st.session_state.fail_counter = 0
            st.session_state.trial_id += 1
            st.session_state.view = "upload"
            st.success("Repas enregistré manuellement !")
            st.session_state.start_time = None
            st.rerun()