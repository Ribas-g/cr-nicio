"""
Sistema de análise do estado do jogo para tomada de decisões estratégicas.
Interpreta o estado bruto do jogo e fornece informações de alto nível.
"""

from typing import List, Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from .card_roles import DeckAnalyzer, CardRole, CardRoleDatabase


class GamePhase(Enum):
    """Fases do jogo"""
    EARLY = "early"      # 0-1 minuto
    MID = "mid"          # 1-2 minutos  
    LATE = "late"        # 2+ minutos
    OVERTIME = "overtime" # Tempo extra


class ThreatLevel(Enum):
    """Níveis de ameaça"""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ThreatInfo:
    """Informações sobre uma ameaça"""
    card_name: str
    position: Tuple[int, int]
    threat_level: ThreatLevel
    distance_to_tower: float
    is_targeting_tower: bool
    requires_immediate_response: bool


@dataclass
class OpportunityInfo:
    """Informações sobre uma oportunidade de ataque"""
    lane: str  # "left" ou "right"
    enemy_elixir_deficit: int
    enemy_defenses_down: bool
    recommended_cards: List[str]
    confidence: float


class GameStateAnalyzer:
    """Analisa o estado atual do jogo e fornece insights estratégicos"""
    
    def __init__(self, deck_analyzer: DeckAnalyzer):
        self.deck_analyzer = deck_analyzer
        self.last_enemy_elixir_spent = 0
        self.enemy_cycle_tracking = []
        
    def analyze_state(self, state) -> 'GameStateInfo':
        """Analisa o estado atual e retorna informações estratégicas"""
        
        # Determinar fase do jogo (assumindo que temos acesso ao tempo)
        game_phase = self._determine_game_phase(state)
        
        # Analisar ameaças
        threats = self._analyze_threats(state)
        
        # Analisar oportunidades
        opportunities = self._analyze_opportunities(state)
        
        # Determinar modo de jogo
        game_mode = self._determine_game_mode(state, threats, opportunities)
        
        # Calcular déficit de elixir do inimigo
        enemy_elixir_deficit = self._estimate_enemy_elixir_deficit(state)
        
        return GameStateInfo(
            phase=game_phase,
            threats=threats,
            opportunities=opportunities,
            game_mode=game_mode,
            our_elixir=state.numbers.elixir.number,
            enemy_elixir_deficit=enemy_elixir_deficit,
            should_defend=len([t for t in threats if t.threat_level.value >= 2]) > 0,
            should_attack=len(opportunities) > 0 and enemy_elixir_deficit >= 3,
            recommended_strategy=self._get_recommended_strategy(threats, opportunities, state)
        )
    
    def _determine_game_phase(self, state) -> GamePhase:
        """Determina a fase atual do jogo"""
        # Por enquanto, usar elixir como proxy para tempo
        # Em implementação real, usaria o tempo de jogo
        elixir = state.numbers.elixir.number
        
        if elixir <= 6:
            return GamePhase.EARLY
        elif elixir <= 8:
            return GamePhase.MID
        else:
            return GamePhase.LATE
    
    def _analyze_threats(self, state) -> List[ThreatInfo]:
        """Analisa ameaças inimigas no campo"""
        threats = []
        
        for enemy in state.enemies:
            threat_level = self._calculate_threat_level(enemy)
            
            if threat_level != ThreatLevel.NONE:
                threats.append(ThreatInfo(
                    card_name=getattr(enemy, 'name', 'Unknown'),
                    position=(enemy.position.tile_x, enemy.position.tile_y),
                    threat_level=threat_level,
                    distance_to_tower=self._calculate_distance_to_tower(enemy.position),
                    is_targeting_tower=self._is_targeting_tower(enemy),
                    requires_immediate_response=threat_level.value >= 3
                ))
        
        # Ordenar por nível de ameaça
        threats.sort(key=lambda t: t.threat_level.value, reverse=True)
        return threats
    
    def _calculate_threat_level(self, enemy) -> ThreatLevel:
        """Calcula o nível de ameaça de uma unidade inimiga"""
        # Distância da torre
        distance = self._calculate_distance_to_tower(enemy.position)
        
        # Cartas de alta prioridade (tanques, win conditions)
        high_priority_cards = ['giant', 'golem', 'hog_rider', 'royal_giant', 'pekka']
        card_name = getattr(enemy, 'name', '').lower()
        
        if distance <= 3:
            if any(card in card_name for card in high_priority_cards):
                return ThreatLevel.CRITICAL
            else:
                return ThreatLevel.HIGH
        elif distance <= 6:
            if any(card in card_name for card in high_priority_cards):
                return ThreatLevel.HIGH
            else:
                return ThreatLevel.MEDIUM
        elif distance <= 10:
            if any(card in card_name for card in high_priority_cards):
                return ThreatLevel.MEDIUM
            else:
                return ThreatLevel.LOW
        else:
            return ThreatLevel.NONE
    
    def _calculate_distance_to_tower(self, position) -> float:
        """Calcula distância até a torre mais próxima"""
        # Torres estão aproximadamente em (3, 14) e (15, 14)
        left_tower_dist = ((position.tile_x - 3) ** 2 + (position.tile_y - 14) ** 2) ** 0.5
        right_tower_dist = ((position.tile_x - 15) ** 2 + (position.tile_y - 14) ** 2) ** 0.5
        
        return min(left_tower_dist, right_tower_dist)
    
    def _is_targeting_tower(self, enemy) -> bool:
        """Verifica se a unidade está se dirigindo para uma torre"""
        # Simplificado: se está na metade inferior do campo
        return enemy.position.tile_y >= 10
    
    def _analyze_opportunities(self, state) -> List[OpportunityInfo]:
        """Analisa oportunidades de ataque"""
        opportunities = []
        
        # Verificar se inimigo gastou muito elixir
        enemy_deficit = self._estimate_enemy_elixir_deficit(state)
        
        if enemy_deficit >= 4:
            # Oportunidade de contra-ataque
            primary_win_condition = self.deck_analyzer.get_primary_win_condition()
            
            if primary_win_condition:
                opportunities.append(OpportunityInfo(
                    lane="right" if len(state.enemies) == 0 or 
                         any(e.position.tile_x <= 9 for e in state.enemies) else "left",
                    enemy_elixir_deficit=enemy_deficit,
                    enemy_defenses_down=len(state.enemies) == 0,
                    recommended_cards=[primary_win_condition.name],
                    confidence=min(0.9, enemy_deficit / 6.0)
                ))
        
        return opportunities
    
    def _estimate_enemy_elixir_deficit(self, state) -> int:
        """Estima quanto elixir o inimigo gastou recentemente"""
        # Simplificado: baseado no número de unidades inimigas no campo
        enemy_count = len(state.enemies)
        
        if enemy_count == 0:
            return 6  # Provavelmente gastou tudo
        elif enemy_count == 1:
            return 3
        elif enemy_count >= 2:
            return 1
        else:
            return 0
    
    def _determine_game_mode(self, state, threats: List[ThreatInfo], 
                           opportunities: List[OpportunityInfo]) -> str:
        """Determina o modo de jogo atual"""
        critical_threats = [t for t in threats if t.threat_level == ThreatLevel.CRITICAL]
        high_threats = [t for t in threats if t.threat_level == ThreatLevel.HIGH]
        
        if critical_threats:
            return "EMERGENCY_DEFENSE"
        elif high_threats:
            return "ACTIVE_DEFENSE"
        elif opportunities and state.numbers.elixir.number >= 6:
            return "ATTACK"
        elif state.numbers.elixir.number >= 9:
            return "FORCED_ATTACK"
        else:
            return "NEUTRAL"
    
    def _get_recommended_strategy(self, threats: List[ThreatInfo], 
                                opportunities: List[OpportunityInfo], state) -> str:
        """Retorna a estratégia recomendada baseada no estado atual"""
        
        if threats and threats[0].threat_level.value >= 3:
            return f"DEFEND_AGAINST_{threats[0].card_name.upper()}"
        
        if opportunities and state.numbers.elixir.number >= 7:
            return f"ATTACK_{opportunities[0].lane.upper()}_LANE"
        
        if state.numbers.elixir.number >= 9:
            return "CYCLE_CARDS"
        
        return "WAIT_AND_REACT"


@dataclass
class GameStateInfo:
    """Informações consolidadas sobre o estado do jogo"""
    phase: GamePhase
    threats: List[ThreatInfo]
    opportunities: List[OpportunityInfo]
    game_mode: str
    our_elixir: int
    enemy_elixir_deficit: int
    should_defend: bool
    should_attack: bool
    recommended_strategy: str
    
    def get_primary_threat(self) -> Optional[ThreatInfo]:
        """Retorna a ameaça mais crítica"""
        return self.threats[0] if self.threats else None
    
    def get_best_opportunity(self) -> Optional[OpportunityInfo]:
        """Retorna a melhor oportunidade de ataque"""
        if not self.opportunities:
            return None
        return max(self.opportunities, key=lambda o: o.confidence)

