from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.postgresql import get_db
from app.models.user import User, UserActivity
from app.utils.auth import get_admin_user, get_recruiter_user, get_sales_user, get_hr_user
from sqlalchemy import func
from app.models.candidate import Candidate, Resume
from typing import Dict, List, Any
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/admin/dashboard")
async def get_admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)  # Admins uniquement
):
    # Nombre total d'utilisateurs par rôle
    user_counts = db.query(
        User.role, 
        func.count(User.id)
    ).group_by(User.role).all()
    
    user_stats = {role: count for role, count in user_counts}
    
    # Activités récentes
    recent_activities = db.query(UserActivity)\
        .order_by(UserActivity.timestamp.desc())\
        .limit(10)\
        .all()
    
    # Nombre total de candidats
    candidate_count = db.query(func.count(Candidate.id)).scalar()
    
    # Candidats récemment ajoutés
    recent_candidates = db.query(Candidate)\
        .order_by(Candidate.created_at.desc())\
        .limit(5)\
        .all()
    
    # Activité par jour (7 derniers jours)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    activity_by_day = db.query(
        func.date_trunc('day', UserActivity.timestamp).label('day'),
        func.count(UserActivity.id)
    ).filter(UserActivity.timestamp >= seven_days_ago)\
        .group_by('day')\
        .order_by('day')\
        .all()
    
    return {
        "user_stats": user_stats,
        "recent_activities": [
            {
                "id": activity.id,
                "user_id": activity.user_id,
                "activity_type": activity.activity_type,
                "description": activity.description,
                "timestamp": activity.timestamp
            } for activity in recent_activities
        ],
        "candidate_count": candidate_count,
        "recent_candidates": [
            {
                "id": candidate.id,
                "name": candidate.name,
                "email": candidate.email,
                "job_title": candidate.job_title,
                "created_at": candidate.created_at
            } for candidate in recent_candidates
        ],
        "activity_by_day": [
            {
                "day": day.strftime("%Y-%m-%d"),
                "count": count
            } for day, count in activity_by_day
        ]
    }

@router.get("/recruiter/dashboard")
async def get_recruiter_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_recruiter_user)  # Recruteurs uniquement
):
    # Nombre de CV uploadés par l'utilisateur actuel
    user_uploads = db.query(UserActivity)\
        .filter(
            UserActivity.user_id == current_user.id,
            UserActivity.activity_type == "UPLOAD_CV"
        ).count()
    
    # Candidats récemment ajoutés
    recent_candidates = db.query(Candidate)\
        .order_by(Candidate.created_at.desc())\
        .limit(10)\
        .all()
    
    # Top compétences parmi les candidats
    # Note: Cette partie est complexe car nécessite d'extraire des données JSON
    # Simplification pour l'exemple
    
    return {
        "user_uploads": user_uploads,
        "recent_candidates": [
            {
                "id": candidate.id,
                "name": candidate.name,
                "email": candidate.email,
                "job_title": candidate.job_title,
                "created_at": candidate.created_at
            } for candidate in recent_candidates
        ],
    }

@router.get("/sales/dashboard")
async def get_sales_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_sales_user)  # Sales uniquement
):
    # Statistiques spécifiques pour le rôle commercial
    # Exemple: Candidats potentiels pour des postes commerciaux
    
    sales_candidates = db.query(Candidate)\
        .filter(Candidate.job_title.ilike("%sales%"))\
        .all()
    
    return {
        "sales_candidate_count": len(sales_candidates),
        "sales_candidates": [
            {
                "id": candidate.id,
                "name": candidate.name,
                "email": candidate.email,
                "job_title": candidate.job_title
            } for candidate in sales_candidates
        ]
    }

@router.get("/hr/dashboard")
async def get_hr_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hr_user)  # HR uniquement
):
    # Statistiques pour les RH
    # Total des candidats
    candidate_count = db.query(func.count(Candidate.id)).scalar()
    
    # Candidats par niveau d'expérience (approximation basée sur le titre du poste)
    junior_count = db.query(Candidate)\
        .filter(Candidate.job_title.ilike("%junior%"))\
        .count()
    
    senior_count = db.query(Candidate)\
        .filter(Candidate.job_title.ilike("%senior%"))\
        .count()
    
    manager_count = db.query(Candidate)\
        .filter(Candidate.job_title.ilike("%manager%"))\
        .count()
    
    # Candidats récents
    recent_candidates = db.query(Candidate)\
        .order_by(Candidate.created_at.desc())\
        .limit(5)\
        .all()
    
    return {
        "candidate_count": candidate_count,
        "experience_levels": {
            "junior": junior_count,
            "senior": senior_count,
            "manager": manager_count,
            "other": candidate_count - (junior_count + senior_count + manager_count)
        },
        "recent_candidates": [
            {
                "id": candidate.id,
                "name": candidate.name,
                "email": candidate.email,"job_title": candidate.job_title,
                "created_at": candidate.created_at
            } for candidate in recent_candidates
        ]
    }

# Ajouter une route pour récupérer l'activité des utilisateurs (pour l'admin)
@router.get("/admin/user-activities")
async def get_user_activities(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)  # Admins uniquement
):
    activities = db.query(UserActivity)\
        .order_by(UserActivity.timestamp.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    # Récupérer les noms d'utilisateurs
    user_ids = {activity.user_id for activity in activities}
    users = db.query(User.id, User.username).filter(User.id.in_(user_ids)).all()
    user_map = {user_id: username for user_id, username in users}
    
    return [
        {
            "id": activity.id,
            "user_id": activity.user_id,
            "username": user_map.get(activity.user_id, "Unknown"),
            "activity_type": activity.activity_type,
            "description": activity.description,
            "timestamp": activity.timestamp
        } for activity in activities
    ]