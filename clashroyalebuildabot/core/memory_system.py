"""
Sistema de memória para rastrear cartas inimigas e padrões de jogo.
Permite ao bot "lembrar" e adaptar-se ao estilo do oponente.
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import time
from clashroyalebuildabot import Cards


class PlayStyle(Enum):
    """Estilos de jogo identificados"""
    AGGRESSIVE = "aggressive"      # Joga muitas cartas rapidamente
    DEFENSIVE = "defensive"        # Foca em defesa e contra-ataque
    CYCLE = "cycle"               # Cicla cartas rapidamente
    HEAVY = "heavy"               # Usa cartas caras
    SPELL_BAIT = "spell_bait"     # Força uso de feitiços
    UNKNOWN = "unknown"           # Ainda não identificado


@dataclass
class CardPlay:
    """Registro de uma carta jogada pelo inimigo"""
    card: Cards
    timestamp: float
    position: Tuple[int, int]
    lane: str  # "left", "right", "center"
    elixir_spent: int
    context: str  # "attack", "defense", "counter"


@dataclass
class EnemyPattern:
    """Padrão identificado no jogo do inimigo"""
    name: str
    cards_sequence: List[Cards]
    frequency: int
    success_rate: float
    typical_timing: float
    counter_strategy: str


@dataclass
class EnemyMemory:
    """Memória completa do inimigo"""
    cards_seen: Set[Cards] = field(default_factory=set)
    cards_not_seen: Set[Cards] = field(default_factory=set)
    play_style: PlayStyle = PlayStyle.UNKNOWN
    card_plays: List[CardPlay] = field(default_factory=list)
    patterns: List[EnemyPattern] = field(default_factory=list)
    cycle_length: Optional[int] = None
    last_play_time: float = 0.0
    elixir_spending_pattern: List[int] = field(default_factory=list)
    
    # Estatísticas
    total_plays: int = 0
    aggressive_plays: int = 0
    defensive_plays: int = 0
    average_elixir_per_play: float = 0.0


@dataclass
class OurMemory:
    """Memória das nossas próprias jogadas e estratégias"""
    cards_played: List[Cards] = field(default_factory=list)
    play_timestamps: List[float] = field(default_factory=list)
    cycle_position: int = 0
    last_cycle_start: float = 0.0
    deck_rotation: List[Cards] = field(default_factory=list)
    strategy_effectiveness: Dict[str, float] = field(default_factory=dict)
    elixir_efficiency: List[Tuple[float, int]] = field(default_factory=list)  # (timestamp, elixir_spent)


class MemorySystem:
    """Sistema principal de memória"""
    
    def __init__(self):
        self.enemy_memory = EnemyMemory()
        self.our_memory = OurMemory()
        self.game_start_time = time.time()
        self.last_analysis_time = 0.0
        self.analysis_interval = 10.0  # Analisar a cada 10 segundos
        
        # Inicializar cartas não vistas do inimigo (todas as cartas do namespace)
        self.enemy_memory.cards_not_seen = set()
        for attr_name in dir(Cards):
            if not attr_name.startswith('_') and attr_name.isupper():
                card = getattr(Cards, attr_name)
                if hasattr(card, 'name'):  # Verificar se é uma Card válida
                    self.enemy_memory.cards_not_seen.add(card)
    
    def record_enemy_play(self, card: Cards, position: Tuple[int, int], 
                         lane: str, elixir_spent: int, context: str):
        """Registra uma jogada do inimigo"""
        
        current_time = time.time()
        
        # Registrar a jogada
        play = CardPlay(
            card=card,
            timestamp=current_time,
            position=position,
            lane=lane,
            elixir_spent=elixir_spent,
            context=context
        )
        
        self.enemy_memory.card_plays.append(play)
        self.enemy_memory.cards_seen.add(card)
        self.enemy_memory.cards_not_seen.discard(card)
        self.enemy_memory.total_plays += 1
        self.enemy_memory.last_play_time = current_time
        self.enemy_memory.elixir_spending_pattern.append(elixir_spent)
        
        # Atualizar estatísticas
        self._update_play_style_stats(play)
        
        # Analisar padrões periodicamente
        if current_time - self.last_analysis_time > self.analysis_interval:
            self._analyze_patterns()
            self.last_analysis_time = current_time
    
    def _update_play_style_stats(self, play: CardPlay):
        """Atualiza estatísticas de estilo de jogo"""
        
        # Classificar jogada
        if play.context == "attack":
            self.enemy_memory.aggressive_plays += 1
        elif play.context == "defense":
            self.enemy_memory.defensive_plays += 1
        
        # Calcular elixir médio
        total_elixir = sum(self.enemy_memory.elixir_spending_pattern)
        self.enemy_memory.average_elixir_per_play = total_elixir / len(self.enemy_memory.elixir_spending_pattern)
        
        # Determinar estilo de jogo
        self._determine_play_style()
    
    def _determine_play_style(self):
        """Determina o estilo de jogo do inimigo"""
        
        if self.enemy_memory.total_plays < 5:
            return  # Muito cedo para determinar
        
        aggressive_ratio = self.enemy_memory.aggressive_plays / self.enemy_memory.total_plays
        avg_elixir = self.enemy_memory.average_elixir_per_play
        
        if aggressive_ratio > 0.7:
            self.enemy_memory.play_style = PlayStyle.AGGRESSIVE
        elif aggressive_ratio < 0.3:
            self.enemy_memory.play_style = PlayStyle.DEFENSIVE
        elif avg_elixir > 4.5:
            self.enemy_memory.play_style = PlayStyle.HEAVY
        elif avg_elixir < 3.0:
            self.enemy_memory.play_style = PlayStyle.CYCLE
        else:
            self.enemy_memory.play_style = PlayStyle.UNKNOWN
    
    def _analyze_patterns(self):
        """Analisa padrões nas jogadas do inimigo"""
        
        if len(self.enemy_memory.card_plays) < 3:
            return
        
        # Analisar sequências de cartas
        sequences = self._find_card_sequences()
        
        for sequence in sequences:
            pattern = self._create_pattern_from_sequence(sequence)
            if pattern:
                self.enemy_memory.patterns.append(pattern)
        
        # Calcular ciclo de cartas
        self._calculate_cycle_length()
    
    def _find_card_sequences(self) -> List[List[CardPlay]]:
        """Encontra sequências repetidas de cartas"""
        
        sequences = []
        plays = self.enemy_memory.card_plays
        
        # Procurar sequências de 2-4 cartas
        for length in range(2, 5):
            for i in range(len(plays) - length + 1):
                sequence = plays[i:i+length]
                sequences.append(sequence)
        
        return sequences
    
    def _create_pattern_from_sequence(self, sequence: List[CardPlay]) -> Optional[EnemyPattern]:
        """Cria um padrão a partir de uma sequência"""
        
        if len(sequence) < 2:
            return None
        
        # Verificar se esta sequência se repete
        cards = [play.card for play in sequence]
        pattern_name = " -> ".join([card.name for card in cards])
        
        # Calcular timing típico
        timing = sequence[-1].timestamp - sequence[0].timestamp
        
        return EnemyPattern(
            name=pattern_name,
            cards_sequence=cards,
            frequency=1,  # Será atualizado se encontrado novamente
            success_rate=0.5,  # Placeholder
            typical_timing=timing,
            counter_strategy=self._get_counter_strategy(cards)
        )
    
    def _get_counter_strategy(self, cards: List[Cards]) -> str:
        """Determina estratégia de contra-ataque para um padrão"""
        
        # Análise básica - pode ser expandida
        if any(card.name.lower() in ['giant', 'golem', 'pekka'] for card in cards):
            return "heavy_defense"
        elif any(card.name.lower() in ['hog_rider', 'ram_rider'] for card in cards):
            return "fast_counter"
        elif any(card.name.lower() in ['balloon', 'lava_hound'] for card in cards):
            return "air_defense"
        else:
            return "balanced_response"
    
    def _calculate_cycle_length(self):
        """Calcula o comprimento do ciclo de cartas do inimigo"""
        
        if len(self.enemy_memory.cards_seen) < 4:
            return
        
        # Análise simplificada - pode ser melhorada
        recent_plays = self.enemy_memory.card_plays[-10:]  # Últimas 10 jogadas
        
        # Contar cartas únicas
        unique_cards = set(play.card for play in recent_plays)
        
        if len(unique_cards) >= 4:
            self.enemy_memory.cycle_length = len(unique_cards)
    
    def get_strategic_insights(self) -> Dict:
        """Retorna insights estratégicos baseados na memória"""
        
        insights = {
            'play_style': self.enemy_memory.play_style.value,
            'cards_seen': len(self.enemy_memory.cards_seen),
            'cards_not_seen': len(self.enemy_memory.cards_not_seen),
            'cycle_length': self.enemy_memory.cycle_length,
            'average_elixir': self.enemy_memory.average_elixir_per_play,
            'aggressive_ratio': (self.enemy_memory.aggressive_plays / 
                               max(1, self.enemy_memory.total_plays)),
            'patterns_found': len(self.enemy_memory.patterns),
            'recommended_strategy': self._get_recommended_strategy()
        }
        
        return insights
    
    def _get_recommended_strategy(self) -> str:
        """Recomenda estratégia baseada no estilo do inimigo"""
        
        style = self.enemy_memory.play_style
        
        if style == PlayStyle.AGGRESSIVE:
            return "defensive_counter"
        elif style == PlayStyle.DEFENSIVE:
            return "aggressive_pressure"
        elif style == PlayStyle.HEAVY:
            return "cycle_pressure"
        elif style == PlayStyle.CYCLE:
            return "heavy_push"
        else:
            return "balanced"
    
    def predict_next_cards(self, num_predictions: int = 3) -> List[Cards]:
        """Prediz as próximas cartas do inimigo"""
        
        predictions = []
        
        # Baseado no ciclo
        if self.enemy_memory.cycle_length:
            recent_cards = [play.card for play in self.enemy_memory.card_plays[-self.enemy_memory.cycle_length:]]
            predictions.extend(recent_cards[:num_predictions])
        
        # Baseado em padrões
        for pattern in self.enemy_memory.patterns:
            if len(predictions) < num_predictions:
                predictions.extend(pattern.cards_sequence[:num_predictions - len(predictions)])
        
        # Preencher com cartas não vistas
        while len(predictions) < num_predictions and self.enemy_memory.cards_not_seen:
            predictions.append(next(iter(self.enemy_memory.cards_not_seen)))
        
        return predictions[:num_predictions]
    
    def should_expect_card(self, card: Cards, time_window: float = 5.0) -> bool:
        """Verifica se devemos esperar uma carta específica"""
        
        current_time = time.time()
        
        # Verificar se a carta foi jogada recentemente
        for play in reversed(self.enemy_memory.card_plays):
            if play.card == card:
                time_since_play = current_time - play.timestamp
                return time_since_play > time_window
        
        return False
    
    def get_memory_summary(self) -> str:
        """Retorna resumo da memória para logging"""
        
        insights = self.get_strategic_insights()
        
        summary = f"🧠 Memória do Inimigo:\n"
        summary += f"   Estilo: {insights['play_style']}\n"
        summary += f"   Cartas vistas: {insights['cards_seen']}/8\n"
        summary += f"   Elixir médio: {insights['average_elixir']:.1f}\n"
        summary += f"   Padrões: {insights['patterns_found']}\n"
        summary += f"   Estratégia: {insights['recommended_strategy']}\n\n"
        
        # Adicionar resumo da nossa memória
        summary += self.get_our_memory_summary()
        
        return summary
    
    def get_seen_cards(self) -> List[Cards]:
        """Retorna lista de cartas vistas do inimigo"""
        return list(self.enemy_memory.cards_seen)
    
    def get_recent_plays(self) -> List[Tuple[Cards, Tuple[int, int], float]]:
        """Retorna jogadas recentes do inimigo"""
        recent_plays = []
        current_time = time.time()
        
        # Últimas 5 jogadas
        for play in self.enemy_memory.card_plays[-5:]:
            recent_plays.append((
                play.card,
                play.position,
                current_time - play.timestamp
            ))
        
        return recent_plays
    
    def record_our_play(self, card: Cards, elixir_spent: int, strategy: str = "neutral"):
        """Registra uma jogada nossa"""
        
        current_time = time.time()
        
        # Registrar a jogada
        self.our_memory.cards_played.append(card)
        self.our_memory.play_timestamps.append(current_time)
        self.our_memory.elixir_efficiency.append((current_time, elixir_spent))
        
        # Atualizar ciclo
        self._update_our_cycle()
        
        # Atualizar eficiência da estratégia
        self._update_strategy_effectiveness(strategy, elixir_spent)
    
    def _update_our_cycle(self):
        """Atualiza posição no ciclo do nosso deck"""
        
        # Se temos 4 cartas únicas jogadas, começamos um novo ciclo
        unique_cards = set(self.our_memory.cards_played[-4:])
        if len(unique_cards) == 4:
            self.our_memory.cycle_position = 0
            self.our_memory.last_cycle_start = time.time()
        else:
            self.our_memory.cycle_position = len(unique_cards)
    
    def _update_strategy_effectiveness(self, strategy: str, elixir_spent: int):
        """Atualiza eficiência de uma estratégia"""
        
        if strategy not in self.our_memory.strategy_effectiveness:
            self.our_memory.strategy_effectiveness[strategy] = 0.5  # Eficiência neutra
        
        # Ajustar baseado no gasto de elixir (menor é melhor)
        efficiency = max(0, 1.0 - (elixir_spent - 4.0) / 4.0)
        
        # Média ponderada com histórico
        current = self.our_memory.strategy_effectiveness[strategy]
        self.our_memory.strategy_effectiveness[strategy] = (current * 0.8) + (efficiency * 0.2)
    
    def get_our_cycle_info(self) -> Dict:
        """Retorna informações sobre nosso ciclo de cartas"""
        
        return {
            'cycle_position': self.our_memory.cycle_position,
            'cards_played_this_cycle': len(set(self.our_memory.cards_played[-4:])),
            'time_since_cycle_start': time.time() - self.our_memory.last_cycle_start,
            'last_4_cards': self.our_memory.cards_played[-4:] if self.our_memory.cards_played else [],
            'strategy_effectiveness': self.our_memory.strategy_effectiveness.copy()
        }
    
    def get_our_memory_summary(self) -> str:
        """Retorna resumo da nossa memória para logging"""
        
        cycle_info = self.get_our_cycle_info()
        
        summary = f"🎯 Nossa Estratégia:\n"
        summary += f"   Ciclo: {cycle_info['cycle_position']}/4\n"
        summary += f"   Cartas jogadas: {len(self.our_memory.cards_played)}\n"
        summary += f"   Tempo desde início do ciclo: {cycle_info['time_since_cycle_start']:.1f}s\n"
        
        if cycle_info['strategy_effectiveness']:
            best_strategy = max(cycle_info['strategy_effectiveness'].items(), key=lambda x: x[1])
            summary += f"   Melhor estratégia: {best_strategy[0]} ({best_strategy[1]:.1%})"
        
        return summary
