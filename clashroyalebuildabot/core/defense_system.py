"""
Sistema de defesa aprimorado com priorização inteligente de ameaças
e coordenação de múltiplas cartas defensivas.
"""

from typing import List, Dict, Optional, Tuple, Set
from enum import Enum
from dataclasses import dataclass
from clashroyalebuildabot import Cards
from .card_roles import CardRole, CardRoleDatabase
from .game_state import GameStateInfo, ThreatInfo, ThreatLevel


class DefenseType(Enum):
    """Tipos de defesa disponíveis"""
    SINGLE_TARGET = "single_target"      # Contra uma unidade específica
    AREA_DAMAGE = "area_damage"          # Contra grupos/swarm
    AIR_DEFENSE = "air_defense"          # Contra tropas aéreas
    TANK_KILLER = "tank_killer"          # Contra tanques pesados
    BUILDING_DEFENSE = "building_defense" # Construções defensivas
    SPELL_DEFENSE = "spell_defense"       # Feitiços defensivos


@dataclass
class DefenseResponse:
    """Resposta defensiva recomendada"""
    primary_card: Cards
    secondary_cards: List[Cards]
    positioning: Dict[Cards, Tuple[int, int]]
    timing_sequence: List[Tuple[Cards, float]]  # (carta, delay em segundos)
    expected_effectiveness: float
    elixir_cost: int


class ThreatAnalyzer:
    """Analisa ameaças específicas e determina respostas adequadas"""
    
    # Mapeamento de cartas inimigas para tipos de ameaça
    THREAT_CLASSIFICATIONS = {
        # Tanques pesados
        'giant': {'type': 'heavy_tank', 'priority': 8, 'hp': 'high'},
        'golem': {'type': 'heavy_tank', 'priority': 9, 'hp': 'very_high'},
        'pekka': {'type': 'heavy_tank', 'priority': 8, 'hp': 'very_high'},
        'mega_knight': {'type': 'heavy_tank', 'priority': 7, 'hp': 'high'},
        'electro_giant': {'type': 'heavy_tank', 'priority': 8, 'hp': 'very_high'},
        
        # Win conditions rápidas
        'hog_rider': {'type': 'fast_win_condition', 'priority': 9, 'hp': 'medium'},
        'ram_rider': {'type': 'fast_win_condition', 'priority': 8, 'hp': 'medium'},
        'balloon': {'type': 'air_win_condition', 'priority': 9, 'hp': 'medium'},
        
        # Swarm/Grupos
        'skeleton_army': {'type': 'ground_swarm', 'priority': 6, 'hp': 'low'},
        'minion_horde': {'type': 'air_swarm', 'priority': 7, 'hp': 'low'},
        'barbarians': {'type': 'ground_swarm', 'priority': 6, 'hp': 'medium'},
        'goblin_gang': {'type': 'ground_swarm', 'priority': 5, 'hp': 'low'},
        
        # Suporte
        'musketeer': {'type': 'ranged_support', 'priority': 6, 'hp': 'medium'},
        'wizard': {'type': 'splash_support', 'priority': 7, 'hp': 'medium'},
        'electro_wizard': {'type': 'ranged_support', 'priority': 7, 'hp': 'medium'},
        
        # Aéreo
        'lava_hound': {'type': 'air_tank', 'priority': 8, 'hp': 'very_high'},
        'baby_dragon': {'type': 'air_support', 'priority': 6, 'hp': 'medium'},
    }
    
    @classmethod
    def analyze_threat(cls, threat: ThreatInfo) -> Dict:
        """Analisa uma ameaça específica e retorna informações detalhadas"""
        card_name = threat.card_name.lower().replace(' ', '_')
        
        # Buscar classificação da carta
        classification = cls.THREAT_CLASSIFICATIONS.get(card_name, {
            'type': 'unknown',
            'priority': 5,
            'hp': 'medium'
        })
        
        # Ajustar prioridade baseada na distância
        distance_modifier = 1.0
        if threat.distance_to_tower <= 3:
            distance_modifier = 1.5
        elif threat.distance_to_tower <= 6:
            distance_modifier = 1.2
        elif threat.distance_to_tower >= 12:
            distance_modifier = 0.7
        
        adjusted_priority = min(10, classification['priority'] * distance_modifier)
        
        return {
            'type': classification['type'],
            'priority': adjusted_priority,
            'hp_level': classification['hp'],
            'requires_immediate_response': adjusted_priority >= 8,
            'recommended_defense_type': cls._get_recommended_defense_type(classification['type'])
        }
    
    @classmethod
    def _get_recommended_defense_type(cls, threat_type: str) -> DefenseType:
        """Retorna tipo de defesa recomendado para um tipo de ameaça"""
        defense_mapping = {
            'heavy_tank': DefenseType.TANK_KILLER,
            'fast_win_condition': DefenseType.BUILDING_DEFENSE,
            'air_win_condition': DefenseType.AIR_DEFENSE,
            'ground_swarm': DefenseType.AREA_DAMAGE,
            'air_swarm': DefenseType.AIR_DEFENSE,
            'ranged_support': DefenseType.SINGLE_TARGET,
            'splash_support': DefenseType.SINGLE_TARGET,
            'air_tank': DefenseType.AIR_DEFENSE,
            'air_support': DefenseType.AIR_DEFENSE,
        }
        return defense_mapping.get(threat_type, DefenseType.SINGLE_TARGET)


class DefenseManager:
    """Gerencia estratégias defensivas e coordena múltiplas cartas"""
    
    def __init__(self, deck: List[Cards]):
        self.deck = deck
        self.available_defenses = self._categorize_defensive_cards()
        self.active_defenses: List[Dict] = []
        
    def _categorize_defensive_cards(self) -> Dict[DefenseType, List[Cards]]:
        """Categoriza cartas defensivas por tipo"""
        categories = {defense_type: [] for defense_type in DefenseType}
        
        for card in self.deck:
            if CardRoleDatabase.has_role(card, CardRole.DEFENSE):
                # Classificar carta por tipo de defesa
                defense_types = self._get_card_defense_types(card)
                for defense_type in defense_types:
                    categories[defense_type].append(card)
        
        return categories
    
    def _get_card_defense_types(self, card: Cards) -> List[DefenseType]:
        """Retorna tipos de defesa que uma carta pode executar"""
        card_name = card.name.lower()
        
        # Mapeamento específico de cartas para tipos de defesa
        defense_mappings = {
            # Tank killers
            'inferno_tower': [DefenseType.TANK_KILLER, DefenseType.BUILDING_DEFENSE],
            'inferno_dragon': [DefenseType.TANK_KILLER, DefenseType.AIR_DEFENSE],
            'mini_pekka': [DefenseType.TANK_KILLER, DefenseType.SINGLE_TARGET],
            
            # Area damage
            'bomber': [DefenseType.AREA_DAMAGE],
            'wizard': [DefenseType.AREA_DAMAGE, DefenseType.AIR_DEFENSE],
            'valkyrie': [DefenseType.AREA_DAMAGE],
            'baby_dragon': [DefenseType.AREA_DAMAGE, DefenseType.AIR_DEFENSE],
            
            # Air defense
            'musketeer': [DefenseType.AIR_DEFENSE, DefenseType.SINGLE_TARGET],
            'archers': [DefenseType.AIR_DEFENSE, DefenseType.SINGLE_TARGET],
            'tesla': [DefenseType.AIR_DEFENSE, DefenseType.BUILDING_DEFENSE],
            
            # Building defense
            'cannon': [DefenseType.BUILDING_DEFENSE],
            'bomb_tower': [DefenseType.BUILDING_DEFENSE, DefenseType.AREA_DAMAGE],
            'tombstone': [DefenseType.BUILDING_DEFENSE],
            
            # Spell defense
            'arrows': [DefenseType.SPELL_DEFENSE, DefenseType.AIR_DEFENSE],
            'fireball': [DefenseType.SPELL_DEFENSE, DefenseType.AREA_DAMAGE],
            'zap': [DefenseType.SPELL_DEFENSE],
            'the_log': [DefenseType.SPELL_DEFENSE, DefenseType.AREA_DAMAGE],
        }
        
        return defense_mappings.get(card_name, [DefenseType.SINGLE_TARGET])
    
    def plan_defense(self, threats: List[ThreatInfo], 
                    available_cards: List[Cards], 
                    current_elixir: int) -> Optional[DefenseResponse]:
        """Planeja resposta defensiva para as ameaças atuais"""
        
        if not threats:
            return None
        
        # Analisar ameaça principal
        primary_threat = threats[0]
        threat_analysis = ThreatAnalyzer.analyze_threat(primary_threat)
        
        # Encontrar cartas adequadas
        suitable_cards = self._find_suitable_defense_cards(
            threat_analysis, available_cards, current_elixir
        )
        
        if not suitable_cards:
            return None
        
        # Criar resposta defensiva
        return self._create_defense_response(
            primary_threat, threat_analysis, suitable_cards, threats
        )
    
    def _find_suitable_defense_cards(self, threat_analysis: Dict, 
                                   available_cards: List[Cards], 
                                   current_elixir: int) -> List[Cards]:
        """Encontra cartas adequadas para defender contra a ameaça"""
        
        recommended_type = threat_analysis['recommended_defense_type']
        suitable_cards = []
        
        # Buscar cartas do tipo recomendado
        for card in self.available_defenses.get(recommended_type, []):
            if card in available_cards:
                suitable_cards.append(card)
        
        # Se não encontrou cartas específicas, buscar alternativas
        if not suitable_cards:
            for defense_type, cards in self.available_defenses.items():
                for card in cards:
                    if card in available_cards:
                        suitable_cards.append(card)
        
        # Filtrar por custo de elixir
        affordable_cards = [card for card in suitable_cards 
                          if self._get_card_elixir_cost(card) <= current_elixir]
        
        return affordable_cards[:3]  # Máximo 3 cartas
    
    def _get_card_elixir_cost(self, card: Cards) -> int:
        """Retorna custo de elixir estimado da carta"""
        # Mapeamento simplificado de custos
        costs = {
            'skeleton_army': 3, 'goblins': 2, 'archers': 3, 'knight': 3,
            'musketeer': 4, 'wizard': 5, 'mini_pekka': 4, 'valkyrie': 4,
            'cannon': 3, 'tesla': 4, 'inferno_tower': 5, 'bomb_tower': 4,
            'arrows': 3, 'fireball': 4, 'zap': 2, 'the_log': 2,
            'giant': 5, 'golem': 8, 'pekka': 7, 'hog_rider': 4,
        }
        return costs.get(card.name.lower(), 4)  # Default 4
    
    def _create_defense_response(self, primary_threat: ThreatInfo, 
                               threat_analysis: Dict, 
                               suitable_cards: List[Cards],
                               all_threats: List[ThreatInfo]) -> DefenseResponse:
        """Cria resposta defensiva coordenada"""
        
        if not suitable_cards:
            return None
        
        primary_card = suitable_cards[0]
        secondary_cards = suitable_cards[1:2]  # Máximo 1 carta secundária
        
        # Calcular posicionamento
        positioning = self._calculate_defensive_positioning(
            primary_threat, primary_card, secondary_cards
        )
        
        # Calcular sequência de timing
        timing_sequence = self._calculate_timing_sequence(
            primary_card, secondary_cards, threat_analysis
        )
        
        # Estimar efetividade
        effectiveness = self._estimate_effectiveness(
            threat_analysis, primary_card, secondary_cards
        )
        
        # Calcular custo total
        total_cost = sum(self._get_card_elixir_cost(card) 
                        for card in [primary_card] + secondary_cards)
        
        return DefenseResponse(
            primary_card=primary_card,
            secondary_cards=secondary_cards,
            positioning=positioning,
            timing_sequence=timing_sequence,
            expected_effectiveness=effectiveness,
            elixir_cost=total_cost
        )
    
    def _calculate_defensive_positioning(self, threat: ThreatInfo, 
                                       primary_card: Cards, 
                                       secondary_cards: List[Cards]) -> Dict[Cards, Tuple[int, int]]:
        """Calcula posicionamento ótimo para cartas defensivas"""
        positioning = {}
        
        threat_x, threat_y = threat.position
        
        # Posicionamento da carta principal
        if CardRoleDatabase.has_role(primary_card, CardRole.BUILDING):
            # Construções: posição que atrai a ameaça
            if threat_x <= 9:  # Lado esquerdo
                positioning[primary_card] = (6, 9)
            else:  # Lado direito
                positioning[primary_card] = (12, 9)
        else:
            # Tropas: posição que intercepta a ameaça
            if threat_x <= 9:  # Lado esquerdo
                positioning[primary_card] = (7, 11)
            else:  # Lado direito
                positioning[primary_card] = (11, 11)
        
        # Posicionamento de cartas secundárias
        for i, card in enumerate(secondary_cards):
            if threat_x <= 9:  # Lado esquerdo
                positioning[card] = (8 + i, 10)
            else:  # Lado direito
                positioning[card] = (10 - i, 10)
        
        return positioning
    
    def _calculate_timing_sequence(self, primary_card: Cards, 
                                 secondary_cards: List[Cards], 
                                 threat_analysis: Dict) -> List[Tuple[Cards, float]]:
        """Calcula sequência de timing para as cartas"""
        sequence = [(primary_card, 0.0)]  # Carta principal imediatamente
        
        # Cartas secundárias com delay baseado no tipo de ameaça
        base_delay = 1.0 if threat_analysis['requires_immediate_response'] else 2.0
        
        for i, card in enumerate(secondary_cards):
            delay = base_delay + (i * 0.5)
            sequence.append((card, delay))
        
        return sequence
    
    def _estimate_effectiveness(self, threat_analysis: Dict, 
                              primary_card: Cards, 
                              secondary_cards: List[Cards]) -> float:
        """Estima efetividade da resposta defensiva"""
        base_effectiveness = 0.6
        
        # Bonus por carta adequada ao tipo de ameaça
        recommended_type = threat_analysis['recommended_defense_type']
        primary_types = self._get_card_defense_types(primary_card)
        
        if recommended_type in primary_types:
            base_effectiveness += 0.3
        
        # Bonus por cartas secundárias
        base_effectiveness += len(secondary_cards) * 0.1
        
        # Penalty por ameaças de alta prioridade
        if threat_analysis['priority'] >= 9:
            base_effectiveness -= 0.1
        
        return min(1.0, base_effectiveness)
    
    def should_use_spell_defense(self, threats: List[ThreatInfo]) -> bool:
        """Determina se deve usar feitiço defensivo"""
        
        # Usar feitiço se há múltiplas ameaças pequenas
        small_threats = [t for t in threats if t.threat_level.value <= 2]
        if len(small_threats) >= 3:
            return True
        
        # Usar feitiço contra swarm
        swarm_indicators = ['skeleton', 'goblin', 'minion', 'bat']
        for threat in threats:
            if any(indicator in threat.card_name.lower() for indicator in swarm_indicators):
                return True
        
        return False
    
    def get_counter_attack_opportunity(self, successful_defense: bool, 
                                     remaining_elixir: int) -> Optional[Cards]:
        """Identifica oportunidade de contra-ataque após defesa"""
        
        if not successful_defense or remaining_elixir < 4:
            return None
        
        # Buscar win conditions no deck
        win_conditions = [card for card in self.deck 
                         if CardRoleDatabase.has_role(card, CardRole.WIN_CONDITION)]
        
        # Priorizar win conditions de baixo custo
        affordable_win_conditions = [card for card in win_conditions 
                                   if self._get_card_elixir_cost(card) <= remaining_elixir]
        
        if affordable_win_conditions:
            # Retornar a mais barata
            return min(affordable_win_conditions, 
                      key=lambda c: self._get_card_elixir_cost(c))
        
        return None

