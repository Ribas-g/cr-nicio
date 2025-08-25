"""
Sistema Avançado de Predição de Cartas Inimigas
===============================================

Sistema que rastreia cartas inimigas jogadas e prediz o deck completo do oponente.
Permite antecipar ataques e preparar defesas específicas.
"""

from typing import Dict, List, Set, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
import time
import math

from clashroyalebuildabot.namespaces.cards import Cards


class PredictionConfidence(Enum):
    """Níveis de confiança da predição"""
    VERY_LOW = 0.2
    LOW = 0.4
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.95


@dataclass
class CardPrediction:
    """Predição de uma carta específica"""
    card: Cards
    confidence: float
    last_seen: float
    cycle_position: int
    expected_next_play: float
    play_frequency: float
    context_patterns: List[str] = field(default_factory=list)


@dataclass
class DeckPrediction:
    """Predição completa do deck inimigo"""
    confirmed_cards: Set[Cards] = field(default_factory=set)
    predicted_cards: Dict[Cards, float] = field(default_factory=dict)
    deck_archetype: str = "unknown"
    confidence: float = 0.0
    missing_cards_count: int = 8
    average_elixir: float = 4.0


class EnemyCardTracker:
    """Rastreia cartas inimigas jogadas e padrões"""
    
    def __init__(self):
        # Rastreamento básico
        self.cards_seen: Set[Cards] = set()
        self.card_play_history: List[Tuple[Cards, float, Tuple[int, int]]] = []
        self.card_frequencies: Dict[Cards, int] = defaultdict(int)
        self.card_last_seen: Dict[Cards, float] = {}
        
        # Análise de ciclo
        self.cycle_tracking: deque = deque(maxlen=8)  # Últimas 8 cartas
        self.cycle_patterns: List[List[Cards]] = []
        self.estimated_cycle_position: int = 0
        
        # Análise contextual
        self.context_plays: Dict[str, List[Cards]] = defaultdict(list)
        self.combo_patterns: Dict[Cards, List[Cards]] = defaultdict(list)
        self.defensive_responses: Dict[str, List[Cards]] = defaultdict(list)
        
        # Timing e elixir
        self.elixir_tracking: List[Tuple[float, int]] = []  # (tempo, elixir_gasto)
        self.play_timing_patterns: Dict[Cards, List[float]] = defaultdict(list)
        
        # Metadados
        self.game_start_time: float = time.time()
        self.total_cards_played: int = 0
        
    def register_enemy_card(self, card: Cards, position: Tuple[int, int], 
                          our_last_play: Optional[Cards] = None,
                          game_context: str = "neutral"):
        """Registra uma carta inimiga jogada"""
        
        current_time = time.time()
        
        # Rastreamento básico
        self.cards_seen.add(card)
        self.card_play_history.append((card, current_time, position))
        self.card_frequencies[card] += 1
        self.card_last_seen[card] = current_time
        self.total_cards_played += 1
        
        # Análise de ciclo
        self.cycle_tracking.append(card)
        self._analyze_cycle_patterns()
        
        # Análise contextual
        if our_last_play:
            self.defensive_responses[our_last_play.name].append(card)
        
        self.context_plays[game_context].append(card)
        
        # Análise de combos (cartas jogadas em sequência)
        if len(self.card_play_history) >= 2:
            prev_card = self.card_play_history[-2][0]
            time_diff = current_time - self.card_play_history[-2][1]
            
            if time_diff <= 5.0:  # Combo se jogadas em até 5 segundos
                self.combo_patterns[prev_card].append(card)
        
        # Timing patterns
        game_time = current_time - self.game_start_time
        self.play_timing_patterns[card].append(game_time)
        
        # Estimativa de elixir gasto
        estimated_cost = self._estimate_card_cost(card)
        self.elixir_tracking.append((current_time, estimated_cost))
    
    def _analyze_cycle_patterns(self):
        """Analisa padrões de ciclo das cartas"""
        
        if len(self.cycle_tracking) >= 8:
            # Verificar se completou um ciclo
            cycle_list = list(self.cycle_tracking)
            
            # Procurar por repetições que indicam ciclo completo
            for i in range(1, 5):  # Verificar últimas 4 cartas
                if len(cycle_list) >= i * 2:
                    recent = cycle_list[-i:]
                    previous = cycle_list[-i*2:-i]
                    
                    if recent == previous:
                        # Encontrou padrão de repetição
                        self.cycle_patterns.append(cycle_list[-8:])
                        break
    
    def _estimate_card_cost(self, card: Cards) -> int:
        """Estima custo de elixir de uma carta"""
        
        # Mapeamento básico de custos conhecidos
        cost_mapping = {
            # Cartas baratas (1-3)
            'skeleton_army': 3, 'goblins': 2, 'archers': 3, 'knight': 3,
            'ice_spirit': 1, 'skeletons': 1, 'bats': 2, 'spear_goblins': 2,
            
            # Cartas médias (4-5)
            'musketeer': 4, 'minipekka': 4, 'valkyrie': 4, 'hog_rider': 4,
            'giant': 5, 'wizard': 5, 'bomber': 3, 'cannon': 3,
            
            # Cartas caras (6+)
            'pekka': 7, 'golem': 8, 'electro_giant': 8, 'mega_knight': 7,
            'lava_hound': 7, 'balloon': 5,
            
            # Feitiços
            'arrows': 3, 'fireball': 4, 'zap': 2, 'lightning': 6,
            'rocket': 6, 'freeze': 4, 'rage': 2, 'poison': 4
        }
        
        card_name = card.name.lower()
        return cost_mapping.get(card_name, 4)  # Default 4
    
    def get_missing_cards_predictions(self) -> List[CardPrediction]:
        """Prediz cartas que ainda não foram vistas"""
        
        predictions = []
        
        # Analisar arquétipo baseado nas cartas vistas
        archetype = self._identify_deck_archetype()
        
        # Cartas comuns por arquétipo
        archetype_cards = {
            'giant_beatdown': [Cards.GIANT, Cards.MUSKETEER, Cards.BOMBER, Cards.ARROWS],
            'hog_cycle': [Cards.HOG_RIDER, Cards.ICE_SPIRIT, Cards.CANNON, Cards.ARCHERS],
            'golem_beatdown': [Cards.GOLEM, Cards.NIGHT_WITCH, Cards.BABY_DRAGON, Cards.LIGHTNING],
            'pekka_bridge_spam': [Cards.PEKKA, Cards.BATTLE_RAM, Cards.BANDIT, Cards.ZAP],
            'lava_hound': [Cards.LAVA_HOUND, Cards.BALLOON, Cards.MINIONS, Cards.TOMBSTONE],
            'spell_bait': [Cards.GOBLIN_BARREL, Cards.PRINCESS, Cards.KNIGHT, Cards.ROCKET],
            'x_bow': [Cards.X_BOW, Cards.TESLA, Cards.ARCHERS, Cards.THE_LOG],
        }
        
        # Predizer cartas baseado no arquétipo
        if archetype in archetype_cards:
            for card in archetype_cards[archetype]:
                if card not in self.cards_seen:
                    confidence = self._calculate_prediction_confidence(card, archetype)
                    
                    prediction = CardPrediction(
                        card=card,
                        confidence=confidence,
                        last_seen=0.0,
                        cycle_position=self._estimate_cycle_position(card),
                        expected_next_play=self._estimate_next_play_time(card),
                        play_frequency=0.0,
                        context_patterns=self._get_context_patterns(card, archetype)
                    )
                    predictions.append(prediction)
        
        # Ordenar por confiança
        predictions.sort(key=lambda p: p.confidence, reverse=True)
        return predictions[:8-len(self.cards_seen)]  # Máximo cartas faltantes
    
    def _identify_deck_archetype(self) -> str:
        """Identifica arquétipo do deck baseado nas cartas vistas"""
        
        # Cartas indicadoras de arquétipos
        archetype_indicators = {
            'giant_beatdown': [Cards.GIANT, Cards.MUSKETEER, Cards.BOMBER],
            'hog_cycle': [Cards.HOG_RIDER, Cards.ICE_SPIRIT, Cards.CANNON],
            'golem_beatdown': [Cards.GOLEM, Cards.NIGHT_WITCH, Cards.BABY_DRAGON],
            'pekka_bridge_spam': [Cards.PEKKA, Cards.BATTLE_RAM, Cards.BANDIT],
            'lava_hound': [Cards.LAVA_HOUND, Cards.BALLOON, Cards.MINIONS],
            'spell_bait': [Cards.GOBLIN_BARREL, Cards.PRINCESS, Cards.KNIGHT],
            'x_bow': [Cards.X_BOW, Cards.TESLA, Cards.ARCHERS],
        }
        
        best_match = "unknown"
        best_score = 0
        
        for archetype, indicators in archetype_indicators.items():
            score = sum(1 for card in indicators if card in self.cards_seen)
            if score > best_score:
                best_score = score
                best_match = archetype
        
        return best_match if best_score >= 2 else "unknown"
    
    def _calculate_prediction_confidence(self, card: Cards, archetype: str) -> float:
        """Calcula confiança da predição de uma carta"""
        
        base_confidence = 0.3
        
        # Boost baseado no arquétipo
        if archetype != "unknown":
            base_confidence += 0.3
        
        # Boost baseado no número de cartas vistas
        cards_seen_ratio = len(self.cards_seen) / 8.0
        base_confidence += cards_seen_ratio * 0.2
        
        # Boost baseado em padrões de combo
        for seen_card in self.cards_seen:
            if card in self.combo_patterns.get(seen_card, []):
                base_confidence += 0.2
                break
        
        return min(0.95, base_confidence)
    
    def _estimate_cycle_position(self, card: Cards) -> int:
        """Estima posição da carta no ciclo"""
        
        # Análise simplificada baseada em padrões
        if len(self.cycle_patterns) > 0:
            # Usar último padrão conhecido
            last_pattern = self.cycle_patterns[-1]
            if card in last_pattern:
                return last_pattern.index(card)
        
        return -1  # Posição desconhecida
    
    def _estimate_next_play_time(self, card: Cards) -> float:
        """Estima quando a carta será jogada novamente"""
        
        current_time = time.time()
        
        # Se carta já foi vista, usar padrões históricos
        if card in self.card_last_seen:
            last_seen = self.card_last_seen[card]
            
            # Estimar baseado na frequência de jogo
            frequency = self.card_frequencies[card]
            game_duration = current_time - self.game_start_time
            
            if frequency > 1 and game_duration > 0:
                avg_interval = game_duration / frequency
                return current_time + avg_interval
        
        # Estimativa baseada no ciclo médio (assumindo 8 cartas)
        avg_cycle_time = 30.0  # 30 segundos por ciclo completo
        return current_time + avg_cycle_time
    
    def _get_context_patterns(self, card: Cards, archetype: str) -> List[str]:
        """Retorna padrões de contexto para uma carta"""
        
        patterns = []
        
        # Padrões baseados no arquétipo
        archetype_patterns = {
            'giant_beatdown': ['behind_king_tower', 'with_support'],
            'hog_cycle': ['bridge_spam', 'counter_attack'],
            'golem_beatdown': ['back_of_king', 'heavy_push'],
            'spell_bait': ['bait_spells', 'punish_spell_use'],
        }
        
        if archetype in archetype_patterns:
            patterns.extend(archetype_patterns[archetype])
        
        return patterns


class EnemyElixirTracker:
    """Rastreia e prediz elixir do oponente"""
    
    def __init__(self):
        self.enemy_elixir_history: List[Tuple[float, int]] = []
        self.estimated_current_elixir: int = 5  # Estimativa inicial
        self.last_update_time: float = time.time()
        self.elixir_generation_rate: float = 1.0  # 1 elixir por segundo
        
        # Padrões de gasto
        self.spending_patterns: Dict[str, List[int]] = defaultdict(list)
        self.average_spending_per_push: float = 8.0
        
        # Detecção de vantagem/desvantagem
        self.elixir_advantages: List[Tuple[float, int]] = []  # (tempo, vantagem)
    
    def update_enemy_elixir(self, cards_played: List[Cards], 
                          context: str = "neutral"):
        """Atualiza estimativa de elixir inimigo baseado nas cartas jogadas"""
        
        current_time = time.time()
        time_diff = current_time - self.last_update_time
        
        # Regeneração natural de elixir
        elixir_generated = min(10, time_diff * self.elixir_generation_rate)
        self.estimated_current_elixir = min(10, self.estimated_current_elixir + elixir_generated)
        
        # Subtrair elixir gasto
        total_spent = 0
        for card in cards_played:
            cost = self._estimate_card_cost(card)
            total_spent += cost
            self.estimated_current_elixir = max(0, self.estimated_current_elixir - cost)
        
        # Registrar padrão de gasto
        if total_spent > 0:
            self.spending_patterns[context].append(total_spent)
            self.enemy_elixir_history.append((current_time, self.estimated_current_elixir))
        
        self.last_update_time = current_time
    
    def _estimate_card_cost(self, card: Cards) -> int:
        """Estima custo de elixir (mesmo método do tracker)"""
        cost_mapping = {
            'skeleton_army': 3, 'goblins': 2, 'archers': 3, 'knight': 3,
            'musketeer': 4, 'minipekka': 4, 'valkyrie': 4, 'hog_rider': 4,
            'giant': 5, 'wizard': 5, 'pekka': 7, 'golem': 8,
            'arrows': 3, 'fireball': 4, 'zap': 2, 'lightning': 6,
        }
        return cost_mapping.get(card.name.lower(), 4)
    
    def get_elixir_advantage(self, our_elixir: int) -> int:
        """Calcula vantagem/desvantagem de elixir"""
        
        advantage = our_elixir - self.estimated_current_elixir
        
        # Registrar para análise histórica
        current_time = time.time()
        self.elixir_advantages.append((current_time, advantage))
        
        return advantage
    
    def predict_enemy_next_play(self) -> Tuple[str, float]:
        """Prediz próxima jogada do inimigo baseada no elixir"""
        
        if self.estimated_current_elixir <= 2:
            return ("forced_wait", 0.8)  # Deve esperar elixir
        elif self.estimated_current_elixir <= 4:
            return ("cheap_card", 0.7)   # Carta barata
        elif self.estimated_current_elixir <= 6:
            return ("medium_card", 0.6)  # Carta média
        elif self.estimated_current_elixir >= 8:
            return ("expensive_combo", 0.8)  # Combo caro
        else:
            return ("unknown", 0.3)
    
    def is_good_counter_attack_moment(self) -> Tuple[bool, float]:
        """Determina se é bom momento para contra-ataque"""
        
        # Bom momento se inimigo tem pouco elixir
        if self.estimated_current_elixir <= 3:
            confidence = 0.9
        elif self.estimated_current_elixir <= 5:
            confidence = 0.7
        else:
            confidence = 0.3
        
        return (self.estimated_current_elixir <= 5, confidence)


class AdvancedEnemyPredictor:
    """Sistema principal de predição avançada"""
    
    def __init__(self):
        self.card_tracker = EnemyCardTracker()
        self.elixir_tracker = EnemyElixirTracker()
        
        # Predições consolidadas
        self.current_deck_prediction: Optional[DeckPrediction] = None
        self.next_card_predictions: List[CardPrediction] = []
        
        # Análise de padrões
        self.behavioral_patterns: Dict[str, float] = {}
        self.adaptation_level: float = 0.0
    
    def update_enemy_plays(self, recent_enemy_plays: List[Tuple[Cards, Tuple[int, int], float]]):
        """Atualiza com jogadas recentes do inimigo"""
        
        # Verificar se é uma lista de cartas simples ou de tuples
        if recent_enemy_plays and not isinstance(recent_enemy_plays[0], tuple):
            # É uma lista de cartas simples
            for card in recent_enemy_plays:
                self.process_enemy_play(
                    card=card,
                    position=(0, 0),  # Posição padrão
                    our_last_play=None,
                    our_elixir=5,
                    game_context="neutral"
                )
            return
        
        # É uma lista de tuples
        for card, position, time_since_play in recent_enemy_plays:
            # Converter tempo relativo para timestamp absoluto
            current_time = time.time()
            play_time = current_time - time_since_play
            
            # Processar a jogada
            self.process_enemy_play(
                card=card,
                position=position,
                our_last_play=None,  # Não temos contexto do nosso último play aqui
                our_elixir=5,  # Placeholder
                game_context="neutral"
                         )
    
    def get_known_enemy_cards(self) -> List[Cards]:
        """Retorna lista de cartas inimigas conhecidas"""
        return list(self.card_tracker.cards_seen)
     
    def process_enemy_play(self, card: Cards, position: Tuple[int, int],
                         our_last_play: Optional[Cards] = None,
                         our_elixir: int = 5,
                         game_context: str = "neutral"):
        """Processa uma jogada inimiga e atualiza predições"""
        
        # Atualizar trackers
        self.card_tracker.register_enemy_card(card, position, our_last_play, game_context)
        self.elixir_tracker.update_enemy_elixir([card], game_context)
        
        # Atualizar predições
        self._update_deck_prediction()
        self._update_next_card_predictions()
        self._analyze_behavioral_patterns()
    
    def _update_deck_prediction(self):
        """Atualiza predição completa do deck"""
        
        confirmed_cards = self.card_tracker.cards_seen
        predicted_cards = {}
        
        # Obter predições de cartas faltantes
        missing_predictions = self.card_tracker.get_missing_cards_predictions()
        for pred in missing_predictions:
            predicted_cards[pred.card] = pred.confidence
        
        # Identificar arquétipo
        archetype = self.card_tracker._identify_deck_archetype()
        
        # Calcular confiança geral
        cards_seen_ratio = len(confirmed_cards) / 8.0
        confidence = cards_seen_ratio * 0.7 + (0.3 if archetype != "unknown" else 0.0)
        
        # Calcular elixir médio
        total_cost = sum(self.card_tracker._estimate_card_cost(card) for card in confirmed_cards)
        avg_elixir = total_cost / len(confirmed_cards) if confirmed_cards else 4.0
        
        self.current_deck_prediction = DeckPrediction(
            confirmed_cards=confirmed_cards,
            predicted_cards=predicted_cards,
            deck_archetype=archetype,
            confidence=confidence,
            missing_cards_count=8 - len(confirmed_cards),
            average_elixir=avg_elixir
        )
    
    def _update_next_card_predictions(self):
        """Atualiza predições da próxima carta"""
        
        self.next_card_predictions = []
        
        # Predições baseadas no ciclo
        if len(self.card_tracker.cycle_tracking) > 0:
            recent_cards = list(self.card_tracker.cycle_tracking)
            
            # Predizer próximas cartas do ciclo
            for card in self.card_tracker.cards_seen:
                if card not in recent_cards[-4:]:  # Não jogada recentemente
                    confidence = self._calculate_next_play_confidence(card)
                    
                    prediction = CardPrediction(
                        card=card,
                        confidence=confidence,
                        last_seen=self.card_tracker.card_last_seen.get(card, 0),
                        cycle_position=self.card_tracker._estimate_cycle_position(card),
                        expected_next_play=self.card_tracker._estimate_next_play_time(card),
                        play_frequency=self.card_tracker.card_frequencies[card]
                    )
                    self.next_card_predictions.append(prediction)
        
        # Ordenar por probabilidade
        self.next_card_predictions.sort(key=lambda p: p.confidence, reverse=True)
    
    def _calculate_next_play_confidence(self, card: Cards) -> float:
        """Calcula confiança de que uma carta será jogada em breve"""
        
        base_confidence = 0.3
        
        # Boost baseado na frequência de uso
        frequency = self.card_tracker.card_frequencies[card]
        total_plays = self.card_tracker.total_cards_played
        
        if total_plays > 0:
            usage_rate = frequency / total_plays
            base_confidence += usage_rate * 0.4
        
        # Boost baseado no tempo desde última jogada
        if card in self.card_tracker.card_last_seen:
            time_since_last = time.time() - self.card_tracker.card_last_seen[card]
            if time_since_last > 20:  # Não jogada há 20+ segundos
                base_confidence += 0.3
        
        # Boost baseado no elixir disponível
        card_cost = self.card_tracker._estimate_card_cost(card)
        if self.elixir_tracker.estimated_current_elixir >= card_cost:
            base_confidence += 0.2
        
        return min(0.95, base_confidence)
    
    def _analyze_behavioral_patterns(self):
        """Analisa padrões comportamentais do oponente"""
        
        # Agressividade
        aggressive_plays = len([p for p in self.card_tracker.context_plays["attack"]])
        total_plays = self.card_tracker.total_cards_played
        
        if total_plays > 0:
            self.behavioral_patterns["aggressiveness"] = aggressive_plays / total_plays
        
        # Paciência (tempo entre jogadas)
        if len(self.card_tracker.card_play_history) >= 2:
            time_intervals = []
            for i in range(1, len(self.card_tracker.card_play_history)):
                prev_time = self.card_tracker.card_play_history[i-1][1]
                curr_time = self.card_tracker.card_play_history[i][1]
                time_intervals.append(curr_time - prev_time)
            
            avg_interval = sum(time_intervals) / len(time_intervals)
            self.behavioral_patterns["patience"] = min(1.0, avg_interval / 10.0)
        
        # Adaptação (mudança de padrões)
        self.adaptation_level = self._calculate_adaptation_level()
    
    def _calculate_adaptation_level(self) -> float:
        """Calcula nível de adaptação do oponente"""
        
        if len(self.card_tracker.card_play_history) < 10:
            return 0.0
        
        # Comparar padrões da primeira e segunda metade do jogo
        mid_point = len(self.card_tracker.card_play_history) // 2
        first_half = self.card_tracker.card_play_history[:mid_point]
        second_half = self.card_tracker.card_play_history[mid_point:]
        
        # Calcular diferença nos padrões de cartas
        first_cards = set(play[0] for play in first_half)
        second_cards = set(play[0] for play in second_half)
        
        overlap = len(first_cards.intersection(second_cards))
        total_unique = len(first_cards.union(second_cards))
        
        if total_unique > 0:
            similarity = overlap / total_unique
            return 1.0 - similarity  # Menos similaridade = mais adaptação
        
        return 0.0
    
    def get_counter_strategy_recommendations(self) -> Dict[str, any]:
        """Retorna recomendações de contra-estratégia"""
        
        recommendations = {
            "immediate_threats": [],
            "predicted_next_moves": [],
            "counter_cards": [],
            "timing_recommendations": {},
            "elixir_strategy": {}
        }
        
        # Ameaças imediatas baseadas em predições
        for pred in self.next_card_predictions[:3]:
            if pred.confidence > 0.7:
                recommendations["immediate_threats"].append({
                    "card": pred.card.name,
                    "confidence": pred.confidence,
                    "expected_time": pred.expected_next_play
                })
        
        # Estratégia de elixir
        is_good_moment, confidence = self.elixir_tracker.is_good_counter_attack_moment()
        recommendations["elixir_strategy"] = {
            "counter_attack_opportunity": is_good_moment,
            "confidence": confidence,
            "enemy_elixir": self.elixir_tracker.estimated_current_elixir,
            "recommended_action": "attack" if is_good_moment else "defend"
        }
        
        # Recomendações de timing
        enemy_next_play, play_confidence = self.elixir_tracker.predict_enemy_next_play()
        recommendations["timing_recommendations"] = {
            "enemy_next_play_type": enemy_next_play,
            "confidence": play_confidence,
            "recommended_response": self._get_response_for_play_type(enemy_next_play)
        }
        
        return recommendations
    
    def _get_response_for_play_type(self, play_type: str) -> str:
        """Retorna resposta recomendada para tipo de jogada"""
        
        responses = {
            "forced_wait": "aggressive_push",
            "cheap_card": "prepare_defense",
            "medium_card": "counter_attack",
            "expensive_combo": "defend_and_counter",
            "unknown": "wait_and_react"
        }
        
        return responses.get(play_type, "wait_and_react")
    
    def get_prediction_summary(self) -> Dict[str, any]:
        """Retorna resumo das predições atuais"""
        
        summary = {
            "deck_prediction": {
                "archetype": self.current_deck_prediction.deck_archetype if self.current_deck_prediction else "unknown",
                "confidence": self.current_deck_prediction.confidence if self.current_deck_prediction else 0.0,
                "cards_seen": len(self.card_tracker.cards_seen),
                "cards_missing": 8 - len(self.card_tracker.cards_seen)
            },
            "next_card_predictions": [
                {
                    "card": pred.card.name,
                    "confidence": pred.confidence,
                    "expected_time": pred.expected_next_play
                }
                for pred in self.next_card_predictions[:3]
            ],
            "elixir_tracking": {
                "estimated_enemy_elixir": self.elixir_tracker.estimated_current_elixir,
                "elixir_advantage": self.elixir_tracker.get_elixir_advantage(5),  # Assumindo 5 nosso
                "counter_attack_opportunity": self.elixir_tracker.is_good_counter_attack_moment()[0]
            },
            "behavioral_analysis": {
                "aggressiveness": self.behavioral_patterns.get("aggressiveness", 0.0),
                "patience": self.behavioral_patterns.get("patience", 0.0),
                "adaptation_level": self.adaptation_level
            }
        }
        
        return summary

