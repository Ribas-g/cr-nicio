"""
Sistema de Defesa Proativa
=========================

Sistema que antecipa ataques inimigos e prepara defesas antes mesmo
das ameaças aparecerem no campo.
"""

from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
from dataclasses import dataclass, field
import time
import math

from clashroyalebuildabot.namespaces.cards import Cards


class ThreatLevel(Enum):
    """Níveis de ameaça"""
    MINIMAL = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5


class DefenseType(Enum):
    """Tipos de defesa"""
    BUILDING = "building"           # Construções defensivas
    TROOP = "troop"                # Tropas defensivas
    SPELL = "spell"                # Feitiços defensivos
    SWARM = "swarm"                # Tropas em grupo
    TANK_KILLER = "tank_killer"    # Anti-tanque
    AIR_DEFENSE = "air_defense"    # Defesa aérea


class AttackPattern(Enum):
    """Padrões de ataque identificados"""
    BEATDOWN = "beatdown"           # Push pesado com tanque
    BRIDGE_SPAM = "bridge_spam"     # Spam na ponte
    SIEGE = "siege"                 # Ataque de cerco
    CYCLE = "cycle"                 # Ciclo rápido
    SPELL_BAIT = "spell_bait"       # Isca de feitiços
    AIR_ATTACK = "air_attack"       # Ataque aéreo
    SPLIT_PUSH = "split_push"       # Push dividido


@dataclass
class ThreatPrediction:
    """Predição de ameaça específica"""
    threat_card: Cards
    confidence: float
    expected_time: float
    expected_position: Tuple[int, int]
    threat_level: ThreatLevel
    recommended_counters: List[Cards]
    preparation_time: float  # Tempo necessário para preparar defesa


@dataclass
class DefensePreparation:
    """Preparação defensiva"""
    defense_cards: List[Cards]
    positions: List[Tuple[int, int]]
    timing: float
    cost: int
    effectiveness: float
    backup_options: List[Cards] = field(default_factory=list)


class ProactiveDefenseManager:
    """Gerenciador principal de defesa proativa"""
    
    def __init__(self):
        # Mapeamento de contadores
        self.counter_database = self._initialize_counter_database()
        
        # Padrões de ataque identificados
        self.identified_patterns: List[AttackPattern] = []
        self.pattern_confidence: Dict[AttackPattern, float] = {}
        
        # Predições ativas
        self.active_threats: List[ThreatPrediction] = []
        self.prepared_defenses: List[DefensePreparation] = []
        
        # Histórico de ataques inimigos
        self.enemy_attack_history: List[Tuple[float, Cards, Tuple[int, int]]] = []
        self.attack_patterns_seen: Dict[str, int] = {}
        
        # Análise de timing
        self.enemy_attack_timing: Dict[Cards, List[float]] = {}
        self.average_attack_intervals: Dict[Cards, float] = {}
        
        # Estado das defesas
        self.active_defenses: Dict[Tuple[int, int], Cards] = {}
        self.defense_cooldowns: Dict[Cards, float] = {}
        
        # Aprendizado adaptativo
        self.defense_success_rates: Dict[str, float] = {}  # combo_defesa -> taxa_sucesso
        self.adaptation_weights: Dict[AttackPattern, float] = {}
    
    def _initialize_counter_database(self) -> Dict[Cards, List[Tuple[Cards, float]]]:
        """Inicializa base de dados de contadores"""
        
        counters = {
            # Tanques terrestres
            Cards.GIANT: [
                (Cards.INFERNO_TOWER, 0.9),
                (Cards.MINIPEKKA, 0.8),
                (Cards.PEKKA, 0.85),
                (Cards.CANNON, 0.6),
                (Cards.TESLA, 0.7)
            ],
            
            Cards.GOLEM: [
                (Cards.INFERNO_TOWER, 0.95),
                (Cards.PEKKA, 0.9),
                (Cards.MINIPEKKA, 0.7),
                (Cards.INFERNO_DRAGON, 0.8)
            ],
            
            Cards.PEKKA: [
                (Cards.SKELETON_ARMY, 0.8),
                (Cards.MINION_HORDE, 0.85),
                (Cards.INFERNO_TOWER, 0.9),
                (Cards.INFERNO_DRAGON, 0.8)
            ],
            
            # Win conditions rápidas
            Cards.HOG_RIDER: [
                (Cards.CANNON, 0.9),
                (Cards.TESLA, 0.85),
                (Cards.TOMBSTONE, 0.8),
                (Cards.MINIPEKKA, 0.7),
                (Cards.VALKYRIE, 0.6)
            ],
            
            Cards.BALLOON: [
                (Cards.MUSKETEER, 0.9),
                (Cards.ARCHERS, 0.8),
                (Cards.TESLA, 0.85),
                (Cards.INFERNO_TOWER, 0.7),
                (Cards.MINIONS, 0.75)
            ],
            
            # Tropas aéreas
            Cards.LAVA_HOUND: [
                (Cards.MUSKETEER, 0.8),
                (Cards.ARCHERS, 0.7),
                (Cards.TESLA, 0.75),
                (Cards.INFERNO_DRAGON, 0.6)
            ],
            
            Cards.MINION_HORDE: [
                (Cards.ARROWS, 0.95),
                (Cards.ZAP, 0.8),
                (Cards.FIREBALL, 0.9),
                (Cards.WIZARD, 0.85)
            ],
            
            # Swarm
            Cards.SKELETON_ARMY: [
                (Cards.ZAP, 0.95),
                (Cards.THE_LOG, 0.9),
                (Cards.ARROWS, 0.85),
                (Cards.VALKYRIE, 0.8)
            ],
            
            Cards.GOBLIN_GANG: [
                (Cards.ZAP, 0.9),
                (Cards.THE_LOG, 0.95),
                (Cards.ARROWS, 0.8),
                (Cards.VALKYRIE, 0.75)
            ],
            
            # Siege
            Cards.X_BOW: [
                (Cards.ROCKET, 0.9),
                (Cards.LIGHTNING, 0.85),
                (Cards.GIANT, 0.8),
                (Cards.GOLEM, 0.75)
            ],
            
            Cards.MORTAR: [
                (Cards.ROCKET, 0.85),
                (Cards.MINER, 0.8),
                (Cards.HOG_RIDER, 0.75)
            ]
        }
        
        return counters
    
    def analyze_enemy_pattern(self, recent_plays: List[Tuple[Cards, Tuple[int, int], float]]):
        """Analisa padrão de ataque do inimigo"""
        
        # Verificar se é uma lista de cartas simples ou de tuples
        if not recent_plays:
            return
            
        if not isinstance(recent_plays[0], tuple):
            # É uma lista de cartas simples
            return  # Não podemos analisar padrões sem posição e timestamp
        
        if len(recent_plays) < 3:
            return
        
        # Adicionar ao histórico
        for card, position, timestamp in recent_plays:
            self.enemy_attack_history.append((timestamp, card, position))
        
        # Identificar padrões
        self._identify_attack_patterns(recent_plays)
        self._analyze_timing_patterns(recent_plays)
        self._predict_next_moves()
    
    def _identify_attack_patterns(self, recent_plays: List[Tuple[Cards, Tuple[int, int], float]]):
        """Identifica padrões de ataque específicos"""
        
        cards_played = [play[0] for play in recent_plays]
        positions = [play[1] for play in recent_plays]
        
        # Detectar Beatdown
        heavy_tanks = [Cards.GOLEM, Cards.GIANT, Cards.PEKKA, Cards.ELECTRO_GIANT]
        support_cards = [Cards.MUSKETEER, Cards.WIZARD, Cards.NIGHT_WITCH, Cards.BABY_DRAGON]
        
        if any(tank in cards_played for tank in heavy_tanks):
            if any(support in cards_played for support in support_cards):
                self._update_pattern_confidence(AttackPattern.BEATDOWN, 0.8)
        
        # Detectar Bridge Spam
        bridge_cards = [Cards.BATTLE_RAM, Cards.BANDIT, Cards.ROYAL_GHOST]
        if any(card in cards_played for card in bridge_cards):
            # Verificar se jogadas foram na ponte
            bridge_positions = [(14, 9), (14, 23)]  # Posições aproximadas da ponte
            for pos in positions:
                if any(abs(pos[0] - bp[0]) < 3 and abs(pos[1] - bp[1]) < 3 
                      for bp in bridge_positions):
                    self._update_pattern_confidence(AttackPattern.BRIDGE_SPAM, 0.7)
                    break
        
        # Detectar Cycle
        cheap_cards = [Cards.ICE_SPIRIT, Cards.SKELETONS, Cards.BATS, Cards.ICE_GOLEM]
        if sum(1 for card in cards_played if card in cheap_cards) >= 2:
            self._update_pattern_confidence(AttackPattern.CYCLE, 0.6)
        
        # Detectar Air Attack
        air_cards = [Cards.LAVA_HOUND, Cards.BALLOON, Cards.MINION_HORDE, Cards.BABY_DRAGON]
        if sum(1 for card in cards_played if card in air_cards) >= 2:
            self._update_pattern_confidence(AttackPattern.AIR_ATTACK, 0.7)
        
        # Detectar Siege
        siege_cards = [Cards.X_BOW, Cards.MORTAR]
        if any(card in cards_played for card in siege_cards):
            self._update_pattern_confidence(AttackPattern.SIEGE, 0.9)
        
        # Detectar Spell Bait
        bait_cards = [Cards.GOBLIN_BARREL, Cards.PRINCESS, Cards.SKELETON_ARMY, Cards.GOBLIN_GANG]
        if sum(1 for card in cards_played if card in bait_cards) >= 2:
            self._update_pattern_confidence(AttackPattern.SPELL_BAIT, 0.7)
    
    def _update_pattern_confidence(self, pattern: AttackPattern, confidence: float):
        """Atualiza confiança de um padrão identificado"""
        
        if pattern in self.pattern_confidence:
            # Média ponderada com histórico
            current = self.pattern_confidence[pattern]
            self.pattern_confidence[pattern] = (current * 0.7) + (confidence * 0.3)
        else:
            self.pattern_confidence[pattern] = confidence
        
        # Adicionar à lista se confiança for alta
        if (self.pattern_confidence[pattern] > 0.6 and 
            pattern not in self.identified_patterns):
            self.identified_patterns.append(pattern)
    
    def _analyze_timing_patterns(self, recent_plays: List[Tuple[Cards, Tuple[int, int], float]]):
        """Analisa padrões de timing dos ataques"""
        
        for card, position, timestamp in recent_plays:
            if card not in self.enemy_attack_timing:
                self.enemy_attack_timing[card] = []
            
            self.enemy_attack_timing[card].append(timestamp)
            
            # Calcular intervalo médio se temos múltiplas jogadas
            if len(self.enemy_attack_timing[card]) >= 2:
                intervals = []
                times = self.enemy_attack_timing[card]
                
                for i in range(1, len(times)):
                    intervals.append(times[i] - times[i-1])
                
                self.average_attack_intervals[card] = sum(intervals) / len(intervals)
    
    def _predict_next_moves(self):
        """Prediz próximos movimentos do inimigo"""
        
        self.active_threats = []
        current_time = time.time()
        
        # Predições baseadas em padrões identificados
        for pattern in self.identified_patterns:
            confidence = self.pattern_confidence[pattern]
            
            if pattern == AttackPattern.BEATDOWN:
                self._predict_beatdown_threats(current_time, confidence)
            elif pattern == AttackPattern.BRIDGE_SPAM:
                self._predict_bridge_spam_threats(current_time, confidence)
            elif pattern == AttackPattern.AIR_ATTACK:
                self._predict_air_threats(current_time, confidence)
            elif pattern == AttackPattern.SIEGE:
                self._predict_siege_threats(current_time, confidence)
            elif pattern == AttackPattern.SPELL_BAIT:
                self._predict_spell_bait_threats(current_time, confidence)
        
        # Predições baseadas em timing histórico
        self._predict_timing_based_threats(current_time)
    
    def _predict_beatdown_threats(self, current_time: float, base_confidence: float):
        """Prediz ameaças de beatdown"""
        
        # Tanques principais
        tank_threats = [Cards.GOLEM, Cards.GIANT, Cards.PEKKA]
        support_threats = [Cards.MUSKETEER, Cards.WIZARD, Cards.NIGHT_WITCH]
        
        for tank in tank_threats:
            if tank in self.average_attack_intervals:
                next_expected = current_time + self.average_attack_intervals[tank]
                
                threat = ThreatPrediction(
                    threat_card=tank,
                    confidence=base_confidence * 0.8,
                    expected_time=next_expected,
                    expected_position=(7, 32),  # Atrás da torre do rei
                    threat_level=ThreatLevel.HIGH,
                    recommended_counters=[counter[0] for counter in self.counter_database.get(tank, [])],
                    preparation_time=5.0
                )
                self.active_threats.append(threat)
        
        # Suporte após tanque
        for support in support_threats:
            threat = ThreatPrediction(
                threat_card=support,
                confidence=base_confidence * 0.6,
                expected_time=current_time + 8.0,  # Após tanque
                expected_position=(10, 28),
                threat_level=ThreatLevel.MEDIUM,
                recommended_counters=[counter[0] for counter in self.counter_database.get(support, [])],
                preparation_time=3.0
            )
            self.active_threats.append(threat)
    
    def _predict_bridge_spam_threats(self, current_time: float, base_confidence: float):
        """Prediz ameaças de bridge spam"""
        
        spam_cards = [Cards.BATTLE_RAM, Cards.BANDIT, Cards.ROYAL_GHOST, Cards.HOG_RIDER]
        
        for card in spam_cards:
            threat = ThreatPrediction(
                threat_card=card,
                confidence=base_confidence * 0.7,
                expected_time=current_time + 3.0,  # Rápido
                expected_position=(14, 15),  # Ponte
                threat_level=ThreatLevel.HIGH,
                recommended_counters=[counter[0] for counter in self.counter_database.get(card, [])],
                preparation_time=1.0  # Pouco tempo para preparar
            )
            self.active_threats.append(threat)
    
    def _predict_air_threats(self, current_time: float, base_confidence: float):
        """Prediz ameaças aéreas"""
        
        air_cards = [Cards.LAVA_HOUND, Cards.BALLOON, Cards.MINION_HORDE]
        
        for card in air_cards:
            threat = ThreatPrediction(
                threat_card=card,
                confidence=base_confidence * 0.75,
                expected_time=current_time + 5.0,
                expected_position=(7, 30),
                threat_level=ThreatLevel.HIGH if card == Cards.BALLOON else ThreatLevel.MEDIUM,
                recommended_counters=[counter[0] for counter in self.counter_database.get(card, [])],
                preparation_time=3.0
            )
            self.active_threats.append(threat)
    
    def _predict_siege_threats(self, current_time: float, base_confidence: float):
        """Prediz ameaças de siege"""
        
        siege_cards = [Cards.X_BOW, Cards.MORTAR]
        
        for card in siege_cards:
            threat = ThreatPrediction(
                threat_card=card,
                confidence=base_confidence * 0.9,
                expected_time=current_time + 10.0,  # Mais lento para configurar
                expected_position=(14, 20),  # Centro do campo
                threat_level=ThreatLevel.CRITICAL,
                recommended_counters=[counter[0] for counter in self.counter_database.get(card, [])],
                preparation_time=8.0
            )
            self.active_threats.append(threat)
    
    def _predict_spell_bait_threats(self, current_time: float, base_confidence: float):
        """Prediz ameaças de spell bait"""
        
        bait_cards = [Cards.GOBLIN_BARREL, Cards.PRINCESS, Cards.SKELETON_ARMY]
        
        for card in bait_cards:
            threat = ThreatPrediction(
                threat_card=card,
                confidence=base_confidence * 0.6,
                expected_time=current_time + 4.0,
                expected_position=(16, 10),  # Perto da torre
                threat_level=ThreatLevel.MEDIUM,
                recommended_counters=[counter[0] for counter in self.counter_database.get(card, [])],
                preparation_time=2.0
            )
            self.active_threats.append(threat)
    
    def _predict_timing_based_threats(self, current_time: float):
        """Prediz ameaças baseadas em padrões de timing"""
        
        for card, avg_interval in self.average_attack_intervals.items():
            if card in self.enemy_attack_timing:
                last_play = self.enemy_attack_timing[card][-1]
                expected_next = last_play + avg_interval
                
                if expected_next <= current_time + 15.0:  # Próximos 15 segundos
                    confidence = 0.7 if expected_next <= current_time + 5.0 else 0.5
                    
                    threat = ThreatPrediction(
                        threat_card=card,
                        confidence=confidence,
                        expected_time=expected_next,
                        expected_position=(10, 25),  # Posição genérica
                        threat_level=self._assess_threat_level(card),
                        recommended_counters=[counter[0] for counter in self.counter_database.get(card, [])],
                        preparation_time=max(1.0, expected_next - current_time - 2.0)
                    )
                    self.active_threats.append(threat)
    
    def _assess_threat_level(self, card: Cards) -> ThreatLevel:
        """Avalia nível de ameaça de uma carta"""
        
        high_threat_cards = [Cards.GOLEM, Cards.PEKKA, Cards.BALLOON, Cards.HOG_RIDER]
        medium_threat_cards = [Cards.GIANT, Cards.MUSKETEER, Cards.WIZARD]
        low_threat_cards = [Cards.ARCHERS, Cards.KNIGHT, Cards.GOBLINS]
        
        if card in high_threat_cards:
            return ThreatLevel.HIGH
        elif card in medium_threat_cards:
            return ThreatLevel.MEDIUM
        elif card in low_threat_cards:
            return ThreatLevel.LOW
        else:
            return ThreatLevel.MEDIUM  # Default
    
    def prepare_defenses(self, available_cards: List[Cards], our_elixir: int) -> List[DefensePreparation]:
        """Prepara defesas para ameaças preditas"""
        
        preparations = []
        current_time = time.time()
        
        # Ordenar ameaças por prioridade (nível + confiança + proximidade)
        sorted_threats = sorted(
            self.active_threats,
            key=lambda t: (t.threat_level.value * t.confidence * (1.0 / max(1.0, t.expected_time - current_time))),
            reverse=True
        )
        
        elixir_budget = our_elixir
        
        for threat in sorted_threats[:3]:  # Top 3 ameaças
            if threat.expected_time - current_time <= threat.preparation_time:
                # Encontrar melhor defesa disponível
                best_defense = self._find_best_defense(threat, available_cards, elixir_budget)
                
                if best_defense:
                    preparations.append(best_defense)
                    elixir_budget -= best_defense.cost
                    
                    if elixir_budget <= 0:
                        break
        
        self.prepared_defenses = preparations
        return preparations
    
    def _find_best_defense(self, threat: ThreatPrediction, 
                          available_cards: List[Cards], 
                          elixir_budget: int) -> Optional[DefensePreparation]:
        """Encontra melhor defesa para uma ameaça específica"""
        
        best_defense = None
        best_score = 0.0
        
        for counter_card, effectiveness in self.counter_database.get(threat.threat_card, []):
            if counter_card in available_cards:
                card_cost = self._estimate_card_cost(counter_card)
                
                if card_cost <= elixir_budget:
                    # Calcular posição ótima
                    optimal_position = self._calculate_optimal_defense_position(
                        threat.expected_position, counter_card
                    )
                    
                    # Score baseado em efetividade, custo e disponibilidade
                    score = effectiveness * (1.0 - (card_cost / 10.0)) * threat.confidence
                    
                    if score > best_score:
                        best_score = score
                        best_defense = DefensePreparation(
                            defense_cards=[counter_card],
                            positions=[optimal_position],
                            timing=threat.expected_time - 1.0,  # Um pouco antes
                            cost=card_cost,
                            effectiveness=effectiveness,
                            backup_options=self._get_backup_options(threat, available_cards)
                        )
        
        return best_defense
    
    def _calculate_optimal_defense_position(self, threat_position: Tuple[int, int], 
                                          defense_card: Cards) -> Tuple[int, int]:
        """Calcula posição ótima para defesa"""
        
        # Posições defensivas padrão
        left_defense = (10, 15)
        right_defense = (10, 25)
        center_defense = (8, 20)
        
        # Escolher baseado na posição da ameaça
        threat_x, threat_y = threat_position
        
        if threat_y < 20:  # Lado esquerdo
            return left_defense
        elif threat_y > 20:  # Lado direito
            return right_defense
        else:  # Centro
            return center_defense
    
    def _get_backup_options(self, threat: ThreatPrediction, 
                           available_cards: List[Cards]) -> List[Cards]:
        """Retorna opções de backup para defesa"""
        
        backup_options = []
        
        for counter_card, effectiveness in self.counter_database.get(threat.threat_card, []):
            if (counter_card in available_cards and 
                effectiveness >= 0.6 and 
                len(backup_options) < 3):
                backup_options.append(counter_card)
        
        return backup_options
    
    def _estimate_card_cost(self, card: Cards) -> int:
        """Estima custo de elixir de uma carta"""
        cost_mapping = {
            'skeleton_army': 3, 'goblins': 2, 'archers': 3, 'knight': 3,
            'musketeer': 4, 'minipekka': 4, 'valkyrie': 4, 'hog_rider': 4,
            'giant': 5, 'wizard': 5, 'pekka': 7, 'golem': 8,
            'arrows': 3, 'fireball': 4, 'zap': 2, 'lightning': 6,
            'cannon': 3, 'tesla': 4, 'inferno_tower': 5, 'tombstone': 3
        }
        return cost_mapping.get(card.name.lower(), 4)
    
    def should_execute_defense_now(self, preparation: DefensePreparation) -> bool:
        """Determina se deve executar defesa agora"""
        
        current_time = time.time()
        
        # Executar se estamos próximos do timing planejado
        if abs(current_time - preparation.timing) <= 1.0:
            return True
        
        # Executar se ameaça iminente foi detectada
        for threat in self.active_threats:
            if (threat.expected_time - current_time <= 2.0 and 
                threat.threat_level.value >= 4):
                return True
        
        return False
    
    def adapt_defenses_based_on_success(self, defense_used: Cards, 
                                      threat_faced: Cards, 
                                      success: bool):
        """Adapta defesas baseado no sucesso"""
        
        combo_key = f"{defense_used.name}_vs_{threat_faced.name}"
        
        if combo_key not in self.defense_success_rates:
            self.defense_success_rates[combo_key] = []
        
        self.defense_success_rates[combo_key].append(success)
        
        # Manter apenas últimos 10 resultados
        if len(self.defense_success_rates[combo_key]) > 10:
            self.defense_success_rates[combo_key] = \
                self.defense_success_rates[combo_key][-10:]
        
        # Ajustar efetividade no banco de dados
        if threat_faced in self.counter_database:
            for i, (counter, effectiveness) in enumerate(self.counter_database[threat_faced]):
                if counter == defense_used:
                    success_rate = sum(self.defense_success_rates[combo_key]) / len(self.defense_success_rates[combo_key])
                    
                    # Ajustar efetividade baseado na taxa de sucesso
                    new_effectiveness = (effectiveness * 0.8) + (success_rate * 0.2)
                    self.counter_database[threat_faced][i] = (counter, new_effectiveness)
                    break
    
    def get_defense_recommendations(self) -> Dict[str, any]:
        """Retorna recomendações defensivas atuais"""
        
        recommendations = {
            "immediate_threats": [],
            "predicted_threats": [],
            "recommended_preparations": [],
            "pattern_analysis": {},
            "adaptation_suggestions": []
        }
        
        current_time = time.time()
        
        # Ameaças imediatas (próximos 5 segundos)
        for threat in self.active_threats:
            if threat.expected_time - current_time <= 5.0:
                recommendations["immediate_threats"].append({
                    "card": threat.threat_card.name,
                    "confidence": threat.confidence,
                    "time_to_threat": threat.expected_time - current_time,
                    "threat_level": threat.threat_level.name,
                    "recommended_counters": [c.name for c in threat.recommended_counters[:3]]
                })
        
        # Ameaças preditas (próximos 15 segundos)
        for threat in self.active_threats:
            if 5.0 < threat.expected_time - current_time <= 15.0:
                recommendations["predicted_threats"].append({
                    "card": threat.threat_card.name,
                    "confidence": threat.confidence,
                    "expected_time": threat.expected_time,
                    "preparation_time": threat.preparation_time
                })
        
        # Preparações recomendadas
        for prep in self.prepared_defenses:
            recommendations["recommended_preparations"].append({
                "defense_cards": [c.name for c in prep.defense_cards],
                "cost": prep.cost,
                "effectiveness": prep.effectiveness,
                "timing": prep.timing
            })
        
        # Análise de padrões
        recommendations["pattern_analysis"] = {
            "identified_patterns": [p.value for p in self.identified_patterns],
            "pattern_confidence": {p.value: conf for p, conf in self.pattern_confidence.items()},
            "most_likely_pattern": max(self.pattern_confidence.items(), 
                                     key=lambda x: x[1])[0].value if self.pattern_confidence else "unknown"
        }
        
        return recommendations

