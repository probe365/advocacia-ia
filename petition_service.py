import os

from .models import db, Petition

class PetitionService:
    @staticmethod
    def _require_tenant_id(tenant_id):
        normalized = (str(tenant_id).strip() if tenant_id is not None else "")
        if not normalized or normalized.lower() == "none":
            normalized = os.getenv("DEFAULT_TENANT_ID", "public").strip()
        if not normalized:
            raise ValueError("tenant_id obrigatório")
        return normalized

    @staticmethod
    def create_petition(data, tenant_id, user_id):
        tenant_id = PetitionService._require_tenant_id(tenant_id)
        petition = Petition(
            tenant_id=tenant_id,
            user_id=user_id,
            cliente_id=data.get('cliente_id'),
            process_id=data.get('process_id'),
            petition_type=data['petition_type'],
            content=data.get('content', {}),
            status=data.get('status', 'draft')
        )
        db.session.add(petition)
        db.session.commit()
        return petition

    @staticmethod
    def get_petitions(tenant_id):
        tenant_id = PetitionService._require_tenant_id(tenant_id)
        return Petition.query.filter_by(tenant_id=tenant_id).all()

    @staticmethod
    def get_petition(petition_id, tenant_id):
        tenant_id = PetitionService._require_tenant_id(tenant_id)
        return Petition.query.filter_by(id=petition_id, tenant_id=tenant_id).first()

    @staticmethod
    def update_petition(petition_id, tenant_id, data):
        tenant_id = PetitionService._require_tenant_id(tenant_id)
        petition = Petition.query.filter_by(id=petition_id, tenant_id=tenant_id).first()
        if not petition:
            return None
        for key, value in data.items():
            setattr(petition, key, value)
        db.session.commit()
        return petition

    @staticmethod
    def delete_petition(petition_id, tenant_id):
        tenant_id = PetitionService._require_tenant_id(tenant_id)
        petition = Petition.query.filter_by(id=petition_id, tenant_id=tenant_id).first()
        if not petition:
            return False
        db.session.delete(petition)
        db.session.commit()
        return True