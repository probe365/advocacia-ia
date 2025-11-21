# utils/tipo_parte_helpers.py
"""
Utilidades para gerenciar o tipo de parte (papel do cliente no processo judicial).
Define constantes e funções de formatação para tipo_parte.
"""

# Mapeamento de valores tipo_parte para rótulos em português
TIPO_PARTE_LABELS = {
    'autor': 'Autor',
    'reu': 'Réu',
    'terceiro': 'Terceiro',
    'reclamante': 'Reclamante',
    'reclamada': 'Reclamada',
}

# Mapeamento para descrições mais detalhadas
TIPO_PARTE_DESCRIPTIONS = {
    'autor': 'Aquele que ajuíza a ação (pessoa ou entidade que promove a ação judicial)',
    'reu': 'Aquele contra quem a ação é proposta (pessoa ou entidade acusada)',
    'terceiro': 'Pessoa ou entidade envolvida no processo, mas não como autor ou réu principal',
    'reclamante': 'Aquele que faz a reclamação (em processos trabalhistas)',
    'reclamada': 'Aquela contra quem a reclamação é feita (em processos trabalhistas)',
}

# Valores válidos
VALID_TIPOS_PARTE = set(TIPO_PARTE_LABELS.keys())

def get_tipo_parte_label(tipo_parte: str | None) -> str:
    """Retorna rótulo em português para tipo_parte."""
    if not tipo_parte:
        return '-'
    return TIPO_PARTE_LABELS.get(tipo_parte.lower(), tipo_parte)

def get_tipo_parte_description(tipo_parte: str | None) -> str:
    """Retorna descrição detalhada para tipo_parte."""
    if not tipo_parte:
        return ''
    return TIPO_PARTE_DESCRIPTIONS.get(tipo_parte.lower(), '')

def get_tipo_parte_badge_class(tipo_parte: str | None) -> str:
    """Retorna classe CSS Bootstrap para o badge do tipo_parte."""
    if not tipo_parte:
        return 'badge-secondary'
    
    badge_classes = {
        'autor': 'badge-primary',      # Azul
        'reu': 'badge-danger',          # Vermelho
        'terceiro': 'badge-warning',    # Amarelo
        'reclamante': 'badge-info',     # Ciano
        'reclamada': 'badge-success',   # Verde
    }
    return badge_classes.get(tipo_parte.lower(), 'badge-secondary')

def get_tipo_parte_icon(tipo_parte: str | None) -> str:
    """Retorna ícone Font Awesome para tipo_parte."""
    if not tipo_parte:
        return 'fa-circle-question'
    
    icon_map = {
        'autor': 'fa-gavel',           # Martelo do juiz
        'reu': 'fa-shield-alt',        # Escudo de defesa
        'terceiro': 'fa-person-circle', # Pessoa
        'reclamante': 'fa-hand-paper', # Mão levantada
        'reclamada': 'fa-briefcase',   # Mala (empresa)
    }
    return icon_map.get(tipo_parte.lower(), 'fa-circle-question')

def validate_tipo_parte(tipo_parte: str | None) -> bool:
    """Valida se tipo_parte é um valor válido."""
    if not tipo_parte:
        return True  # Opcional
    return tipo_parte.lower() in VALID_TIPOS_PARTE

def format_tipo_parte_for_display(tipo_parte: str | None) -> str:
    """Formata tipo_parte para exibição em templates (label + badge)."""
    if not tipo_parte:
        return ''
    
    label = get_tipo_parte_label(tipo_parte)
    badge_class = get_tipo_parte_badge_class(tipo_parte)
    icon = get_tipo_parte_icon(tipo_parte)
    
    return f'<span class="badge {badge_class}"><i class="fas {icon}"></i> {label}</span>'

# Mapeamento inverso para facilitar filtros
TIPO_PARTE_BY_CATEGORY = {
    'civil': ['autor', 'reu', 'terceiro'],
    'trabalhista': ['reclamante', 'reclamada'],
    'todas': ['autor', 'reu', 'terceiro', 'reclamante', 'reclamada'],
}

def get_tipos_parte_by_category(category: str) -> list:
    """Retorna lista de tipos_parte válidos para uma categoria de processo."""
    return TIPO_PARTE_BY_CATEGORY.get(category, [])
