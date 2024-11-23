from llm_handler import process_llm_request, generate_training_program
from session_manager import create_program, apply_changes, get_sorted_sessions, get_profile
from profile_runner import profile_data
import sys, os
from datetime import datetime

def print_program(sessions):
    """Pretty print the training program"""
    print("\n=== Programme d'entraînement actuel ===")
    for session in sessions:
        date = datetime.strptime(session["date"], "%Y-%m-%d %H:%M").strftime("%d %B %Y à %H:%M")
        print(f"\n📅 {date}")
        print(f"🏃 Type: {session['type_de_seance']}")
        print(f"📏 Distance: {session['distance']} km")
        print(f"📝 Description: {session['description']}")
    print("\n=====================================")

def print_profile(profile):
    """Pretty print the athlete profile"""
    print("\n=== Profil de l'athlète ===")
    print(f"🎯 Objectif: {profile['objectif_principal']}")
    print(f"⏱️  Chrono cible: {profile['chrono_cible']}")
    print(f"📊 Performances actuelles:")
    print(f"   - 5km: {profile['temps_actuel_5km']}")
    print(f"   - 10km: {profile['temps_actuel_10km']}")
    print(f"📅 Disponibilités: {profile['jours_disponibles_par_semaine']} fois par semaine")
    print(f"🗓️  Jour sortie longue: {profile['jour_sortie_longue']}")
    print("==========================\n")

def main():
    if os.path.exists("program.json"):
        print("📂 Chargement du programme d'entraînement existant...")
    else:
        print("👟 Aucun programme d'entraînement trouvé. Création d'un nouveau programme...")
        # Generate initial program
        try:
            program, explanation, _ = generate_training_program(profile_data)
            if program:
                # Save the program
                create_program(profile_data, program)
                
                # Display initial program
                print_profile(profile_data)
                if explanation:
                    print("💡 Note du coach:", explanation)
                print_program(get_sorted_sessions())
                
            else:
                print("❌ Erreur lors de la génération du programme initial.")
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ Erreur: {str(e)}")
            sys.exit(1)

    # Interactive chat loop
    print("\n🗣️  Vous pouvez maintenant discuter avec votre coach.")
    print("💡 Exemples de questions:")
    print("   - Peux-tu déplacer ma séance de demain à 18h ?")
    print("   - Je suis fatigué, peux-tu alléger ma séance de jeudi ?")
    print("   - Peux-tu ajouter une séance mercredi matin ?")
    print("\n📝 Tapez 'exit' pour quitter, 'program' pour voir le programme actuel")
    
    while True:
        try:
            user_input = input("\n👤 Vous: ").strip()
            
            if user_input.lower() == 'exit':
                print("👋 Au revoir !")
                break
                
            if user_input.lower() == 'program':
                print_program(get_sorted_sessions())
                continue
            
            if not user_input:
                continue
                
            # Process the request
            json_objects, explanation, response = process_llm_request(
                user_input, 
                context_program=get_sorted_sessions()
            )
            
            if json_objects:
                # Apply the changes
                apply_changes(json_objects)
                
                # Show the explanation and updated program
                if explanation:
                    print("\n🏃 Coach:", explanation)

            else:
                print("\n🏃 Coach:", response)
                
        except KeyboardInterrupt:
            print("\n👋 Au revoir !")
            break
            
        except Exception as e:
            print(f"\n❌ Erreur: {str(e)}")
            continue

if __name__ == "__main__":
    main()