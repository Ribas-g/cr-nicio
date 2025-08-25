"""
Sistema de Posicionamento Inteligente
===================================

Sistema que calcula posições ótimas para cartas baseado em múltiplos fatores:
- Posição de tropas inimigas e aliadas
- Alcance e características das cartas
- Objetivos táticos (ataque, defesa, suporte)
- Terreno e obstáculos
"""

from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
from dataclasses import dataclass, field
import math
import numpy as np

from clashroyalebuildabot.namespaces.cards import Cards


class PositionType(Enum):
    """Tipos de posicionamento"""
    OFFENSIVE = "offensive"           # Posição ofensiva
    DEFENSIVE = "defensive"           # Posição defensiva
    SUPPORT = "support"              # Posição de suporte
    FLANKING = "flanking"            # Posição de flanqueamento
    BLOCKING = "blocking"            # Posição de bloqueio
    KITING = "kiting"                # Posição para atrair tropas
    SPLIT_PUSH = "split_push"        # Posição para push dividido


class TerrainFeature(Enum):
    """Características do terreno"""
    BRIDGE = "bridge"                # Ponte
    RIVER = "river"                  # Rio
    TOWER_RANGE = "tower_range"      # Alcance da torre
    KING_TOWER = "king_tower"        # Torre do rei
    PRINCESS_TOWER = "princess_tower" # Torre da princesa
    SPAWN_AREA = "spawn_area"        # Área de spawn


@dataclass
class Position:
    """Posição no campo"""
    x: int
    y: int
    
    def distance_to(self, other: 'Position') -> float:
        """Calcula distância para outra posição"""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def is_within_range(self, other: 'Position', range_tiles: float) -> bool:
        """Verifica se está dentro do alcance"""
        return self.distance_to(other) <= range_tiles


@dataclass
class PositionScore:
    """Score de uma posição"""
    position: Position
    total_score: float
    component_scores: Dict[str, float] = field(default_factory=dict)
    reasoning: List[str] = field(default_factory=list)


@dataclass
class UnitInfo:
    """Informações de uma unidade no campo"""
    card: Cards
    position: Position
    hp_percentage: float
    is_enemy: bool
    target_type: str  # "ground", "air", "buildings"
    movement_speed: float
    range_tiles: float


class IntelligentPositioning:
    """Sistema principal de posicionamento inteligente"""
    
    def __init__(self):
        # Mapa do campo (18x32 tiles aproximadamente)
        self.field_width = 18
        self.field_height = 32
        
        # Características das cartas
        self.card_characteristics = self._initialize_card_characteristics()
        
        # Posições importantes do mapa
        self.important_positions = self._initialize_important_positions()
        
        # Histórico de posicionamentos
        self.positioning_history: List[Tuple[Cards, Position, float]] = []  # carta, posição, sucesso
        
        # Análise de terreno
        self.terrain_analysis = self._initialize_terrain_analysis()
        
        # Padrões aprendidos
        self.learned_patterns: Dict[str, List[Position]] = {}
        
    def _initialize_card_characteristics(self) -> Dict[Cards, Dict[str, any]]:
        """Inicializa características das cartas para posicionamento"""
        
        characteristics = {
            # Tanques
            Cards.GIANT: {
                "role": "tank",
                "range": 1.0,
                "speed": "slow",
                "target": "buildings",
                "optimal_positions": ["behind_king", "bridge_support"],
                "avoid_positions": ["tower_range_early"]
            },
            
            Cards.GOLEM: {
                "role": "heavy_tank", 
                "range": 1.0,
                "speed": "very_slow",
                "target": "buildings",
                "optimal_positions": ["back_of_king", "single_lane"],
                "avoid_positions": ["bridge", "split_lane"]
            },
            
            # Suporte
            Cards.MUSKETEER: {
                "role": "ranged_support",
                "range": 6.0,
                "speed": "medium",
                "target": "air_ground",
                "optimal_positions": ["behind_tank", "defensive_center", "flanking"],
                "avoid_positions": ["front_line", "spell_range"]
            },
            
            Cards.WIZARD: {
                "role": "splash_support",
                "range": 5.0,
                "speed": "medium", 
                "target": "air_ground",
                "optimal_positions": ["behind_tank", "anti_swarm"],
                "avoid_positions": ["front_line", "fireball_range"]
            },
            
            # Win Conditions
            Cards.HOG_RIDER: {
                "role": "fast_attacker",
                "range": 1.0,
                "speed": "very_fast",
                "target": "buildings",
                "optimal_positions": ["bridge", "bypass_defenses"],
                "avoid_positions": ["defensive_buildings"]
            },
            
            Cards.BALLOON: {
                "role": "air_attacker",
                "range": 1.0,
                "speed": "medium",
                "target": "buildings",
                "optimal_positions": ["behind_tank", "avoid_air_defense"],
                "avoid_positions": ["musketeer_range", "tesla_range"]
            },
            
            # Defesas
            Cards.CANNON: {
                "role": "defensive_building",
                "range": 5.5,
                "speed": "static",
                "target": "ground",
                "optimal_positions": ["pull_center", "defensive_center"],
                "avoid_positions": ["spell_range", "too_forward"]
            },
            
            Cards.TESLA: {
                "role": "defensive_building",
                "range": 5.5,
                "speed": "static",
                "target": "air_ground",
                "optimal_positions": ["center_defense", "anti_air"],
                "avoid_positions": ["corner", "too_back"]
            },
            
            # Feitiços
            Cards.FIREBALL: {
                "role": "spell",
                "range": 2.5,  # Raio de dano
                "speed": "instant",
                "target": "area",
                "optimal_positions": ["troop_clusters", "tower_damage"],
                "avoid_positions": ["single_targets", "low_value"]
            },
            
            Cards.ZAP: {
                "role": "spell",
                "range": 2.5,
                "speed": "instant", 
                "target": "area",
                "optimal_positions": ["swarm_clear", "reset_targets"],
                "avoid_positions": ["high_hp_targets"]
            }
        }
        
        return characteristics
    
    def _initialize_important_positions(self) -> Dict[str, Position]:
        """Inicializa posições importantes do mapa"""
        
        positions = {
            # Torres
            "our_king_tower": Position(9, 2),
            "our_left_princess": Position(3, 6),
            "our_right_princess": Position(15, 6),
            "enemy_king_tower": Position(9, 30),
            "enemy_left_princess": Position(3, 26),
            "enemy_right_princess": Position(15, 26),
            
            # Pontes
            "left_bridge": Position(3, 16),
            "right_bridge": Position(15, 16),
            
            # Posições defensivas
            "center_defense": Position(9, 10),
            "left_defense": Position(6, 12),
            "right_defense": Position(12, 12),
            
            # Posições ofensivas
            "behind_king": Position(9, 8),
            "left_lane_start": Position(3, 14),
            "right_lane_start": Position(15, 14),
            
            # Posições de suporte
            "left_support": Position(5, 18),
            "right_support": Position(13, 18),
            "center_support": Position(9, 18)
        }
        
        return positions
    
    def _initialize_terrain_analysis(self) -> Dict[str, List[Position]]:
        """Inicializa análise de terreno"""
        
        terrain = {
            "safe_zones": [  # Zonas seguras (fora do alcance das torres)
                Position(x, y) for x in range(0, 18) for y in range(0, 12)
            ],
            "danger_zones": [  # Zonas perigosas (alcance das torres)
                Position(x, y) for x in range(6, 12) for y in range(20, 32)
            ],
            "bridge_areas": [  # Áreas das pontes
                Position(x, y) for x in range(2, 5) for y in range(15, 17)
            ] + [
                Position(x, y) for x in range(14, 17) for y in range(15, 17)
            ],
            "river_line": [  # Linha do rio
                Position(x, 16) for x in range(0, 18)
            ]
        }
        
        return terrain
    
    def calculate_optimal_position(self, 
                                 card: Cards,
                                 position_type: PositionType,
                                 current_units: List[UnitInfo],
                                 target_position: Optional[Position] = None,
                                 constraints: List[str] = None) -> PositionScore:
        """Calcula posição ótima para uma carta"""
        
        if constraints is None:
            constraints = []
        
        # Gerar candidatos de posição
        candidate_positions = self._generate_position_candidates(
            card, position_type, current_units, constraints
        )
        
        # Avaliar cada posição
        best_position = None
        best_score = -float('inf')
        
        for position in candidate_positions:
            score = self._evaluate_position(
                card, position, position_type, current_units, target_position
            )
            
            if score.total_score > best_score:
                best_score = score.total_score
                best_position = score
        
        return best_position if best_position else PositionScore(
            Position(9, 16), 0.0, {}, ["No valid position found"]
        )
    
    def _generate_position_candidates(self, 
                                    card: Cards,
                                    position_type: PositionType,
                                    current_units: List[UnitInfo],
                                    constraints: List[str]) -> List[Position]:
        """Gera candidatos de posição baseado no tipo"""
        
        candidates = []
        
        if position_type == PositionType.OFFENSIVE:
            candidates.extend(self._get_offensive_positions(card))
        elif position_type == PositionType.DEFENSIVE:
            candidates.extend(self._get_defensive_positions(card, current_units))
        elif position_type == PositionType.SUPPORT:
            candidates.extend(self._get_support_positions(card, current_units))
        elif position_type == PositionType.FLANKING:
            candidates.extend(self._get_flanking_positions(card, current_units))
        elif position_type == PositionType.BLOCKING:
            candidates.extend(self._get_blocking_positions(card, current_units))
        
        # Aplicar restrições
        filtered_candidates = []
        for pos in candidates:
            if self._position_meets_constraints(pos, constraints):
                filtered_candidates.append(pos)
        
        return filtered_candidates
    
    def _get_offensive_positions(self, card: Cards) -> List[Position]:
        """Retorna posições ofensivas para uma carta"""
        
        positions = []
        
        if card in self.card_characteristics:
            char = self.card_characteristics[card]
            
            if char["role"] in ["tank", "heavy_tank"]:
                # Tanques: atrás da torre do rei ou nas lanes
                positions.extend([
                    self.important_positions["behind_king"],
                    self.important_positions["left_lane_start"],
                    self.important_positions["right_lane_start"]
                ])
            
            elif char["role"] == "fast_attacker":
                # Atacantes rápidos: ponte
                positions.extend([
                    self.important_positions["left_bridge"],
                    self.important_positions["right_bridge"]
                ])
            
            elif char["role"] in ["ranged_support", "splash_support"]:
                # Suporte: atrás de tanques ou posições de suporte
                positions.extend([
                    self.important_positions["left_support"],
                    self.important_positions["right_support"],
                    self.important_positions["center_support"]
                ])
        
        return positions
    
    def _get_defensive_positions(self, card: Cards, current_units: List[UnitInfo]) -> List[Position]:
        """Retorna posições defensivas"""
        
        positions = []
        
        # Identificar ameaças inimigas
        enemy_threats = [unit for unit in current_units if unit.is_enemy]
        
        if not enemy_threats:
            # Posições defensivas padrão
            positions.extend([
                self.important_positions["center_defense"],
                self.important_positions["left_defense"],
                self.important_positions["right_defense"]
            ])
        else:
            # Posições baseadas nas ameaças
            for threat in enemy_threats:
                defensive_pos = self._calculate_counter_position(card, threat)
                if defensive_pos:
                    positions.append(defensive_pos)
        
        return positions
    
    def _get_support_positions(self, card: Cards, current_units: List[UnitInfo]) -> List[Position]:
        """Retorna posições de suporte"""
        
        positions = []
        
        # Encontrar tropas aliadas para apoiar
        allied_units = [unit for unit in current_units if not unit.is_enemy]
        
        for ally in allied_units:
            if ally.card in self.card_characteristics:
                ally_char = self.card_characteristics[ally.card]
                
                if ally_char["role"] in ["tank", "heavy_tank"]:
                    # Posicionar atrás de tanques
                    support_pos = Position(
                        ally.position.x,
                        max(0, ally.position.y - 2)  # 2 tiles atrás
                    )
                    positions.append(support_pos)
        
        return positions
    
    def _get_flanking_positions(self, card: Cards, current_units: List[UnitInfo]) -> List[Position]:
        """Retorna posições de flanqueamento"""
        
        positions = []
        
        # Identificar tropas inimigas para flanquear
        enemy_units = [unit for unit in current_units if unit.is_enemy]
        
        for enemy in enemy_units:
            # Posições nas laterais do inimigo
            left_flank = Position(max(0, enemy.position.x - 3), enemy.position.y)
            right_flank = Position(min(17, enemy.position.x + 3), enemy.position.y)
            
            positions.extend([left_flank, right_flank])
        
        return positions
    
    def _get_blocking_positions(self, card: Cards, current_units: List[UnitInfo]) -> List[Position]:
        """Retorna posições de bloqueio"""
        
        positions = []
        
        # Identificar tropas inimigas que se movem em direção às nossas torres
        enemy_attackers = [unit for unit in current_units 
                          if unit.is_enemy and unit.position.y < 20]
        
        for attacker in enemy_attackers:
            # Calcular posição de bloqueio entre o atacante e nossa torre
            our_tower = self.important_positions["our_king_tower"]
            
            # Posição no caminho do atacante
            block_x = attacker.position.x
            block_y = (attacker.position.y + our_tower.y) // 2
            
            positions.append(Position(block_x, block_y))
        
        return positions
    
    def _calculate_counter_position(self, our_card: Cards, enemy_unit: UnitInfo) -> Optional[Position]:
        """Calcula posição para contrariar uma unidade inimiga"""
        
        if our_card not in self.card_characteristics:
            return None
        
        our_char = self.card_characteristics[our_card]
        our_range = our_char["range"]
        
        # Se temos alcance maior, posicionar fora do alcance do inimigo
        if our_range > enemy_unit.range_tiles:
            # Calcular posição que mantém distância segura
            safe_distance = enemy_unit.range_tiles + 1
            
            # Posicionar entre o inimigo e nossa torre
            our_tower = self.important_positions["our_king_tower"]
            
            # Vetor do inimigo para nossa torre
            dx = our_tower.x - enemy_unit.position.x
            dy = our_tower.y - enemy_unit.position.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance > 0:
                # Normalizar vetor
                dx /= distance
                dy /= distance
                
                # Posicionar na distância segura
                counter_x = int(enemy_unit.position.x + dx * safe_distance)
                counter_y = int(enemy_unit.position.y + dy * safe_distance)
                
                return Position(
                    max(0, min(17, counter_x)),
                    max(0, min(31, counter_y))
                )
        
        return None
    
    def _evaluate_position(self, 
                          card: Cards,
                          position: Position,
                          position_type: PositionType,
                          current_units: List[UnitInfo],
                          target_position: Optional[Position]) -> PositionScore:
        """Avalia uma posição específica"""
        
        score_components = {}
        reasoning = []
        
        # 1. Segurança da posição
        safety_score = self._calculate_safety_score(position, current_units)
        score_components["safety"] = safety_score
        
        if safety_score > 0.7:
            reasoning.append("Safe position")
        elif safety_score < 0.3:
            reasoning.append("Dangerous position")
        
        # 2. Efetividade tática
        tactical_score = self._calculate_tactical_score(
            card, position, position_type, current_units
        )
        score_components["tactical"] = tactical_score
        
        # 3. Alcance e cobertura
        coverage_score = self._calculate_coverage_score(card, position, current_units)
        score_components["coverage"] = coverage_score
        
        # 4. Sinergia com outras tropas
        synergy_score = self._calculate_synergy_score(card, position, current_units)
        score_components["synergy"] = synergy_score
        
        # 5. Distância ao objetivo
        objective_score = 0.5  # Score neutro por padrão
        if target_position:
            objective_score = self._calculate_objective_score(position, target_position)
            score_components["objective"] = objective_score
        
        # 6. Histórico de sucesso
        historical_score = self._calculate_historical_score(card, position)
        score_components["historical"] = historical_score
        
        # Pesos para diferentes componentes
        weights = {
            "safety": 0.25,
            "tactical": 0.30,
            "coverage": 0.20,
            "synergy": 0.15,
            "objective": 0.05,
            "historical": 0.05
        }
        
        # Calcular score total
        total_score = sum(score_components[component] * weights[component] 
                         for component in score_components)
        
        return PositionScore(
            position=position,
            total_score=total_score,
            component_scores=score_components,
            reasoning=reasoning
        )
    
    def _calculate_safety_score(self, position: Position, current_units: List[UnitInfo]) -> float:
        """Calcula score de segurança da posição"""
        
        safety = 1.0
        
        # Verificar proximidade de torres inimigas
        enemy_towers = [
            self.important_positions["enemy_king_tower"],
            self.important_positions["enemy_left_princess"],
            self.important_positions["enemy_right_princess"]
        ]
        
        for tower in enemy_towers:
            distance = position.distance_to(tower)
            if distance < 7:  # Alcance da torre
                safety -= (7 - distance) / 7 * 0.4
        
        # Verificar proximidade de unidades inimigas perigosas
        enemy_units = [unit for unit in current_units if unit.is_enemy]
        
        for enemy in enemy_units:
            distance = position.distance_to(enemy.position)
            if distance < enemy.range_tiles + 2:
                threat_level = 0.3 if enemy.card in [Cards.PEKKA, Cards.MEGA_KNIGHT] else 0.1
                safety -= threat_level
        
        return max(0.0, min(1.0, safety))
    
    def _calculate_tactical_score(self, 
                                card: Cards,
                                position: Position,
                                position_type: PositionType,
                                current_units: List[UnitInfo]) -> float:
        """Calcula score tático da posição"""
        
        if card not in self.card_characteristics:
            return 0.5
        
        char = self.card_characteristics[card]
        score = 0.5
        
        # Avaliar baseado no tipo de posicionamento
        if position_type == PositionType.OFFENSIVE:
            # Para ofensiva, proximidade ao objetivo é importante
            enemy_towers = [
                self.important_positions["enemy_left_princess"],
                self.important_positions["enemy_right_princess"]
            ]
            
            min_distance = min(position.distance_to(tower) for tower in enemy_towers)
            score += (32 - min_distance) / 32 * 0.5  # Mais próximo = melhor
        
        elif position_type == PositionType.DEFENSIVE:
            # Para defensiva, posição central é melhor
            center = self.important_positions["center_defense"]
            distance_to_center = position.distance_to(center)
            score += (10 - min(10, distance_to_center)) / 10 * 0.5
        
        elif position_type == PositionType.SUPPORT:
            # Para suporte, proximidade a aliados é importante
            allied_units = [unit for unit in current_units if not unit.is_enemy]
            if allied_units:
                min_ally_distance = min(position.distance_to(ally.position) 
                                      for ally in allied_units)
                score += (5 - min(5, min_ally_distance)) / 5 * 0.3
        
        return max(0.0, min(1.0, score))
    
    def _calculate_coverage_score(self, card: Cards, position: Position, 
                                current_units: List[UnitInfo]) -> float:
        """Calcula score de cobertura/alcance"""
        
        if card not in self.card_characteristics:
            return 0.5
        
        char = self.card_characteristics[card]
        card_range = char["range"]
        
        if card_range <= 1:  # Unidades corpo a corpo
            return 0.5  # Score neutro
        
        # Para unidades de alcance, calcular quantos alvos podem atingir
        enemy_units = [unit for unit in current_units if unit.is_enemy]
        targets_in_range = 0
        
        for enemy in enemy_units:
            if position.distance_to(enemy.position) <= card_range:
                targets_in_range += 1
        
        # Normalizar baseado no número de inimigos
        if enemy_units:
            coverage_ratio = targets_in_range / len(enemy_units)
            return min(1.0, coverage_ratio * 2)  # Multiplicar por 2 para dar mais peso
        
        return 0.5
    
    def _calculate_synergy_score(self, card: Cards, position: Position,
                               current_units: List[UnitInfo]) -> float:
        """Calcula score de sinergia com outras tropas"""
        
        if card not in self.card_characteristics:
            return 0.5
        
        char = self.card_characteristics[card]
        score = 0.5
        
        allied_units = [unit for unit in current_units if not unit.is_enemy]
        
        for ally in allied_units:
            if ally.card in self.card_characteristics:
                ally_char = self.card_characteristics[ally.card]
                distance = position.distance_to(ally.position)
                
                # Sinergia tanque + suporte
                if (char["role"] in ["ranged_support", "splash_support"] and
                    ally_char["role"] in ["tank", "heavy_tank"] and
                    2 <= distance <= 4):
                    score += 0.3
                
                # Sinergia suporte + suporte (cobertura mútua)
                elif (char["role"] in ["ranged_support", "splash_support"] and
                      ally_char["role"] in ["ranged_support", "splash_support"] and
                      3 <= distance <= 6):
                    score += 0.2
                
                # Evitar sobreposição
                elif distance < 2:
                    score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _calculate_objective_score(self, position: Position, target: Position) -> float:
        """Calcula score baseado na proximidade ao objetivo"""
        
        distance = position.distance_to(target)
        max_distance = 32  # Distância máxima no campo
        
        # Score inversamente proporcional à distância
        return max(0.0, (max_distance - distance) / max_distance)
    
    def _calculate_historical_score(self, card: Cards, position: Position) -> float:
        """Calcula score baseado no histórico de sucesso"""
        
        # Buscar posicionamentos similares no histórico
        similar_positions = []
        
        for hist_card, hist_pos, success in self.positioning_history:
            if (hist_card == card and 
                position.distance_to(hist_pos) <= 3):  # Posições próximas
                similar_positions.append(success)
        
        if similar_positions:
            return sum(similar_positions) / len(similar_positions)
        
        return 0.5  # Score neutro se não há histórico
    
    def _position_meets_constraints(self, position: Position, constraints: List[str]) -> bool:
        """Verifica se posição atende às restrições"""
        
        for constraint in constraints:
            if constraint == "avoid_tower_range":
                enemy_towers = [
                    self.important_positions["enemy_king_tower"],
                    self.important_positions["enemy_left_princess"],
                    self.important_positions["enemy_right_princess"]
                ]
                
                for tower in enemy_towers:
                    if position.distance_to(tower) < 7:
                        return False
            
            elif constraint == "stay_in_safe_zone":
                if position in self.terrain_analysis["danger_zones"]:
                    return False
            
            elif constraint == "bridge_only":
                if position not in self.terrain_analysis["bridge_areas"]:
                    return False
        
        return True
    
    def record_positioning_outcome(self, card: Cards, position: Position, success: bool):
        """Registra resultado de posicionamento para aprendizado"""
        
        self.positioning_history.append((card, position, success))
        
        # Manter apenas últimos 100 registros
        if len(self.positioning_history) > 100:
            self.positioning_history = self.positioning_history[-100:]
        
        # Atualizar padrões aprendidos
        pattern_key = f"{card.name}_{success}"
        if pattern_key not in self.learned_patterns:
            self.learned_patterns[pattern_key] = []
        
        self.learned_patterns[pattern_key].append(position)
        
        # Manter apenas últimas 20 posições por padrão
        if len(self.learned_patterns[pattern_key]) > 20:
            self.learned_patterns[pattern_key] = self.learned_patterns[pattern_key][-20:]
    
    def get_positioning_recommendations(self, 
                                      card: Cards,
                                      current_units: List[UnitInfo],
                                      game_context: str = "neutral") -> Dict[str, any]:
        """Retorna recomendações de posicionamento"""
        
        recommendations = {
            "primary_position": None,
            "alternative_positions": [],
            "reasoning": [],
            "tactical_advice": []
        }
        
        # Determinar tipo de posicionamento baseado no contexto
        position_type = self._determine_position_type(card, game_context, current_units)
        
        # Calcular posição ótima
        optimal_position = self.calculate_optimal_position(
            card, position_type, current_units
        )
        
        recommendations["primary_position"] = {
            "x": optimal_position.position.x,
            "y": optimal_position.position.y,
            "score": optimal_position.total_score,
            "type": position_type.value
        }
        
        recommendations["reasoning"] = optimal_position.reasoning
        
        # Gerar alternativas
        alternatives = self._generate_alternative_positions(
            card, position_type, current_units, optimal_position.position
        )
        
        for alt_pos in alternatives[:3]:  # Top 3 alternativas
            recommendations["alternative_positions"].append({
                "x": alt_pos.position.x,
                "y": alt_pos.position.y,
                "score": alt_pos.total_score,
                "reason": alt_pos.reasoning[0] if alt_pos.reasoning else "Alternative option"
            })
        
        # Conselhos táticos
        recommendations["tactical_advice"] = self._generate_tactical_advice(
            card, optimal_position.position, current_units
        )
        
        return recommendations
    
    def _determine_position_type(self, card: Cards, context: str, 
                               current_units: List[UnitInfo]) -> PositionType:
        """Determina tipo de posicionamento baseado no contexto"""
        
        # Verificar se há ameaças inimigas próximas
        enemy_threats = [unit for unit in current_units 
                        if unit.is_enemy and unit.position.y < 20]
        
        if enemy_threats:
            return PositionType.DEFENSIVE
        
        # Verificar contexto do jogo
        if context in ["attack", "counter_attack"]:
            return PositionType.OFFENSIVE
        elif context == "defense":
            return PositionType.DEFENSIVE
        
        # Baseado no papel da carta
        if card in self.card_characteristics:
            char = self.card_characteristics[card]
            
            if char["role"] in ["tank", "heavy_tank", "fast_attacker"]:
                return PositionType.OFFENSIVE
            elif char["role"] in ["ranged_support", "splash_support"]:
                return PositionType.SUPPORT
            elif char["role"] == "defensive_building":
                return PositionType.DEFENSIVE
        
        return PositionType.SUPPORT  # Default
    
    def _generate_alternative_positions(self, 
                                      card: Cards,
                                      position_type: PositionType,
                                      current_units: List[UnitInfo],
                                      primary_position: Position) -> List[PositionScore]:
        """Gera posições alternativas"""
        
        alternatives = []
        
        # Gerar candidatos em área próxima à posição primária
        for dx in [-2, -1, 1, 2]:
            for dy in [-2, -1, 1, 2]:
                alt_x = max(0, min(17, primary_position.x + dx))
                alt_y = max(0, min(31, primary_position.y + dy))
                alt_pos = Position(alt_x, alt_y)
                
                # Avaliar posição alternativa
                score = self._evaluate_position(
                    card, alt_pos, position_type, current_units, None
                )
                
                alternatives.append(score)
        
        # Ordenar por score
        alternatives.sort(key=lambda x: x.total_score, reverse=True)
        
        return alternatives
    
    def _generate_tactical_advice(self, 
                                card: Cards,
                                position: Position,
                                current_units: List[UnitInfo]) -> List[str]:
        """Gera conselhos táticos"""
        
        advice = []
        
        if card in self.card_characteristics:
            char = self.card_characteristics[card]
            
            # Conselhos baseados no papel da carta
            if char["role"] == "tank":
                advice.append("Use tank to absorb damage and protect support troops")
                
                # Verificar se há suporte próximo
                allied_support = [unit for unit in current_units 
                                if not unit.is_enemy and 
                                unit.card in self.card_characteristics and
                                self.card_characteristics[unit.card]["role"] in ["ranged_support", "splash_support"]]
                
                if not allied_support:
                    advice.append("Consider adding support troops behind tank")
            
            elif char["role"] == "ranged_support":
                advice.append("Maintain safe distance and provide cover fire")
                
                # Verificar ameaças próximas
                nearby_enemies = [unit for unit in current_units 
                                if unit.is_enemy and 
                                position.distance_to(unit.position) < 4]
                
                if nearby_enemies:
                    advice.append("Watch for enemy threats - consider repositioning")
            
            elif char["role"] == "fast_attacker":
                advice.append("Strike quickly and avoid defensive buildings")
                
                # Verificar defesas inimigas
                enemy_defenses = [unit for unit in current_units 
                                if unit.is_enemy and 
                                unit.card in [Cards.CANNON, Cards.TESLA, Cards.INFERNO_TOWER]]
                
                if enemy_defenses:
                    advice.append("Enemy defenses detected - consider alternative approach")
        
        return advice

