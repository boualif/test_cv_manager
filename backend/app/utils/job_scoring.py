import json
from typing import Dict, Any

class JobScoring:
    @staticmethod
    def get_prompt_template(job_type: str) -> str:
        """Retourne le modèle de réponse attendu en fonction du type de poste"""
        base_instruction = """
                            Lors de l'évaluation des candidats, priorisez l'expérience pertinente dans le domaine requis (80% de poids) par rapport aux compétences listées (20% de poids).
                            L'évaluation de l'expérience doit se concentrer sur:
                            - L'expérience directe dans le même domaine/industrie
                            - Les contextes et responsabilités similaires
                            - La profondeur et la récence de l'expérience pertinente
                            - Le leadership et l'étendue du projet dans le domaine pertinent
                            """
        # Normaliser le type de poste pour éviter les problèmes de casse
        normalized_job_type = job_type.lower().strip()
        
        if normalized_job_type == "technique":
            return base_instruction + """
            {
                "general_score": "Calculer le pourcentage de correspondance global",
                "skills_score": "Calculer en fonction de la correspondance des compétences techniques (20% de poids)",
                "job_title_and_experience_score": "Calculer en fonction de la correspondance du titre et de l'expérience (80% de poids)",
                "skills_gaps": [
                    "Lister chaque compétence technique manquante",
                    "Lister chaque compétence technique insuffisante"
                ],
                "job_title_and_experience_gaps": [
                    "Détailler les non-correspondances de titre",
                    "Détailler les lacunes d'expérience"
                ],
                "other_gaps": [
                    "Lister toute autre exigence manquante"
                ],
                "skills_match": [
                    "Lister chaque compétence technique correspondante",
                    "Lister chaque compétence validée"
                ],
                "job_title_and_experience_match": [
                    "Détailler les titres correspondants",
                    "Détailler l'expérience pertinente"
                ],
                "candidate_name": "Extraire le nom complet",
                "general_strengths": [
                    "Écrire les points forts détaillés du candidat concernant le poste"
                ],
                "general_weaknesses": [
                    "Écrire les points faibles détaillés du candidat concernant le poste"
                ],
                "estimated_age": "Estimer en fonction de la chronologie de carrière",
                "location": "Extraire l'emplacement du candidat",
                "years_of_experience": "Estimer le nombre total d'années d'expérience, sans compter les stages, TOUJOURS retourner years_of_experience sous forme de NOMBRE + "year" ou "years" (ex: "5 years", "1 year")",
                "email": "Extraire l'email",
                "phone": "Extraire le téléphone"
            }
            """
        elif normalized_job_type == "fonctionnel":
            return base_instruction + """
            {
                "general_score": "Calculer le pourcentage de correspondance global",
                "skills_score": "Calculer en fonction de la correspondance des compétences fonctionnelles (20% de poids)",
                "job_title_and_experience_score": "Calculer en fonction de la correspondance du titre et de l'expérience (80% de poids)",
                "skills_gaps": [
                    "Lister chaque compétence fonctionnelle manquante",
                    "Lister chaque compétence de processus métier insuffisante",
                    "Lister chaque connaissance méthodologique manquante"
                ],
                "job_title_and_experience_gaps": [
                    "Détailler les non-correspondances de titre fonctionnel",
                    "Détailler les lacunes d'expérience fonctionnelle",
                    "Détailler les lacunes d'expérience requise"
                ],
                "other_gaps": [
                    "Lister toute autre exigence manquante",
                    "Lister les lacunes en compétences douces",
                    "Lister les lacunes en connaissance du domaine"
                ],
                "skills_match": [
                    "Lister chaque compétence fonctionnelle correspondante",
                    "Lister chaque compétence de processus métier validée",
                    "Lister chaque expertise méthodologique validée"
                ],
                "job_title_and_experience_match": [
                    "Détailler les titres fonctionnels correspondants",
                    "Détailler l'expérience requise pertinente",
                    "Détailler l'expérience pertinente en gestion de projet"
                ],
                "candidate_name": "Extraire le nom complet",
                "general_strengths": [
                    "Écrire les points forts détaillés en matière fonctionnelle et de processus métier",
                    "Écrire les points forts détaillés en matière de projet et de méthodologie"
                ],
                "general_weaknesses": [
                    "Écrire les points faibles détaillés en matière fonctionnelle et de processus métier",
                    "Écrire les points faibles détaillés en matière de projet et de méthodologie"
                ],
                "estimated_age": "Estimer en fonction de la chronologie de carrière",
                "location": "Extraire l'emplacement du candidat",
                "years_of_experience": "Estimer le nombre total d'années d'expérience, sans compter les stages, TOUJOURS retourner years_of_experience sous forme de NOMBRE + "year" ou "years" (ex: "5 years", "1 year")",
                "email": "Extraire l'email",
                "phone": "Extraire le téléphone"
            }
            """
        else:  # technico-fonctionnel ou autre
            return base_instruction + """
            {
                "general_score": "Calculer le pourcentage de correspondance global",
                "skills_score": "Calculer en fonction de la correspondance des compétences techniques et fonctionnelles combinées (20% de poids)",
                "job_title_and_experience_score": "Calculer en fonction de la correspondance du titre et de l'expérience (80% de poids)",
                "skills_gaps": [
                    "Lister chaque compétence technique manquante",
                    "Lister chaque compétence fonctionnelle manquante",
                    "Lister chaque compétence hybride insuffisante"
                ],
                "job_title_and_experience_gaps": [
                    "Détailler les non-correspondances de titre de rôle hybride",
                    "Détailler les lacunes d'expérience technique",
                    "Détailler les lacunes d'expérience fonctionnelle"
                ],
                "other_gaps": [
                    "Lister les capacités de liaison technique-métier manquantes",
                    "Lister les exigences de gestion de projet manquantes",
                    "Lister toute compétence requise manquante"
                ],
                "skills_match": [
                    "Lister chaque compétence technique correspondante",
                    "Lister chaque compétence fonctionnelle correspondante",
                    "Lister chaque compétence hybride validée"
                ],
                "job_title_and_experience_match": [
                    "Détailler les titres de rôle hybride correspondants",
                    "Détailler l'expérience technique-fonctionnelle pertinente",
                    "Détailler l'expérience pertinente de pont entre projets"
                ],
                "candidate_name": "Extraire le nom complet",
                "general_strengths": [
                    "Écrire les points forts techniques détaillés",
                    "Écrire les points forts fonctionnels détaillés",
                    "Écrire les points forts détaillés en matière de rôle hybride"
                ],
                "general_weaknesses": [
                    "Écrire les points faibles techniques détaillés",
                    "Écrire les points faibles fonctionnels détaillés",
                    "Écrire les points faibles détaillés en matière de rôle hybride"
                ],
                "estimated_age": "Estimer en fonction de la chronologie de carrière",
                "location": "Extraire l'emplacement du candidat",
                "years_of_experience": "Estimer le nombre total d'années d'expérience, sans compter les stages, TOUJOURS retourner years_of_experience sous forme de NOMBRE + "year" ou "years" (ex: "5 years", "1 year")",
                "email": "Extraire l'email",
                "phone": "Extraire le téléphone"
            }
            """

    @staticmethod
    def validate_analysis(analysis: Dict[str, Any]) -> bool:
        """Valider la structure d'analyse"""
        required_fields = [
            "general_score", "skills_score", "job_title_and_experience_score",
            "skills_gaps", "job_title_and_experience_gaps", "skills_match",
            "job_title_and_experience_match", "candidate_name"
        ]
        
        # Vérifier que tous les champs requis sont présents
        for field in required_fields:
            if field not in analysis:
                return False
                
        # Vérifier que les scores contiennent des pourcentages
        if not any(c.isdigit() for c in analysis["general_score"]) or "%" not in analysis["general_score"]:
            return False
            
        if not any(c.isdigit() for c in analysis["skills_score"]) or "%" not in analysis["skills_score"]:
            return False
            
        if not any(c.isdigit() for c in analysis["job_title_and_experience_score"]) or "%" not in analysis["job_title_and_experience_score"]:
            return False
            
        # Vérifier que les champs de liste sont bien des listes
        if not isinstance(analysis["skills_gaps"], list) or not isinstance(analysis["job_title_and_experience_gaps"], list):
            return False
            
        if not isinstance(analysis["skills_match"], list) or not isinstance(analysis["job_title_and_experience_match"], list):
            return False
            
        return True

    @staticmethod
    def calculate_final_score(analysis: Dict[str, Any], elastic_score: int, job_type: str) -> int:
        """Calculer le score final en combinant l'analyse LLM et le score Elasticsearch"""
        # Extraire le pourcentage numérique du score général
        try:
            general_score = int(analysis["general_score"].replace("%", "").strip())
        except (ValueError, AttributeError):
            general_score = 0
            
        # Normaliser le type de poste
        normalized_job_type = job_type.lower().strip()
            
        # Donner plus de poids au score général de l'analyse (80%) qu'au score Elasticsearch (20%)
        # pour les postes techniques
        if normalized_job_type == "technique":
            final_score = int(general_score * 0.8 + elastic_score * 0.2)
        # pour les postes fonctionnels et technico-fonctionnels
        else:
            final_score = int(general_score * 0.7 + elastic_score * 0.3)
            
        # S'assurer que le score est entre 0 et 100
        return max(0, min(100, final_score))

    @staticmethod
    def determine_match_quality(final_score: int, job_type: str) -> str:
        """Déterminer la qualité de la correspondance"""
        # Normaliser le type de poste
        normalized_job_type = job_type.lower().strip()
        
        # Définir les seuils pour les différents types de postes
        if normalized_job_type == "technique":
            if final_score >= 80:
                return "Excellent"
            elif final_score >= 70:
                return "Très bon"
            elif final_score >= 60:
                return "Bon"
            elif final_score >= 50:
                return "Moyen"
            else:
                return "Faible"
        elif normalized_job_type == "fonctionnel":
            if final_score >= 75:
                return "Excellent"
            elif final_score >= 65:
                return "Très bon"
            elif final_score >= 55:
                return "Bon"
            elif final_score >= 45:
                return "Moyen"
            else:
                return "Faible"
        else:  # technico-fonctionnel ou autre
            if final_score >= 75:
                return "Excellent"
            elif final_score >= 65:
                return "Très bon"
            elif final_score >= 55:
                return "Bon"
            elif final_score >= 45:
                return "Moyen"
            else:
                return "Faible"