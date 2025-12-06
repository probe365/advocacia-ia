from flask import Blueprint, jsonify, request, render_template, session
from typing import Dict, List
from pipeline import Pipeline
from cadastro_manager import CadastroManager
from flask import g
import logging

bp = Blueprint('chat', __name__)
logger = logging.getLogger(__name__)

def _manager():
    return CadastroManager(getattr(g, 'tenant_id', None))

@bp.route('/api/v1/processos/<id_processo>/chat', methods=['POST'])
def chat_with_case(id_processo: str):
    dados = request.get_json()
    if not dados or not dados.get('query'):
        return jsonify({'erro':'query obrigatória'}), 400
    try:
        query = dados['query']
        history_dict = dados.get('history', [])
        history: List[Dict[str, str]] = []
        for msg in history_dict:
            if not isinstance(msg, dict):
                continue
            history.append({
                'role': str(msg.get('role') or 'user'),
                'content': str(msg.get('content') or ''),
            })
        pipeline = Pipeline(case_id=id_processo)
        resp = pipeline.chat(query, history)
        # persist turns
        _manager().save_chat_turn(id_processo, 'user', query)
        _manager().save_chat_turn(id_processo, 'assistant', resp.get('output',''))
        return jsonify(resp)
    except Exception as e:
        logger.exception('Erro chat')
        return jsonify({'erro':f'interno: {e}'}), 500

@bp.route('/processos/ui/<id_processo>/chat', methods=['POST'])
def ui_chat_with_case(id_processo):
    try:
        query = request.form.get('query')
        session_key = f'chat_history_{id_processo}'
        if session_key not in session:
            session[session_key] = []
        session[session_key].append({'role':'user','content':query})
        history_for_api = session[session_key][:-1]
        payload = {'query': query, 'history': history_for_api}
        # call internal function directly (avoid HTTP)
        api_resp = chat_with_case(id_processo)
        if api_resp.status_code == 200:
            data = api_resp.get_json()
            session[session_key].append({'role':'assistant','content':data.get('output','')})
        return render_template('_conversa_chat.html', chat_history=session[session_key])
    except Exception as e:
        logger.exception('Erro chat UI')
        return f"<div class='alert alert-danger'>Erro no chat: {e}</div>"
