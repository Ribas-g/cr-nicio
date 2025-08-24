"""
Lógica aprimorada da Mosqueteira com comportamento inteligente.
A Mosqueteira atua como suporte versátil, tanto em ataque quanto em defesa.
"""

from clashroyalebuildabot import Cards
from ..core.enhanced_action import EnhancedAction
from ..core.card_roles import CardRole
from ..core.game_state import GameStateInfo, ThreatLevel


class EnhancedMusketeerAction(EnhancedAction):
    """Ação aprimorada da Mosqueteira com inteligência contextual"""
    
    CARD = Cards.MUSKETEER
    
    def calculate_score(self, state):
        """Cálculo de score aprimorado para a Mosqueteira"""
        
        # Score base: Mosqueteira é versátil
        if state.numbers.elixir.number < 4:
            return [0.0]
        
        # Usar sistema aprimorado se disponível
        if self.game_state_analyzer:
            return self._calculate_intelligent_score(state)
        
        # Fallback para lógica melhorada
        return self._calculate_improved_basic_score(state)
    
    def _calculate_intelligent_score(self, state):
        """Cálculo inteligente usando análise de contexto"""
        
        game_state = self.game_state_analyzer.analyze_state(state)
        
        # Score baseado no papel atual (defesa vs ataque)
        role_score = self._get_role_based_score(game_state, state)
        
        # Score baseado em ameaças aéreas
        air_defense_score = self._get_air_defense_score(game_state, state)
        
        # Score baseado em oportunidades de combo
        combo_score = self._get_combo_support_score(game_state, state)
        
        # Score baseado no posicionamento tático
        tactical_score = self._get_tactical_score(game_state, state)
        
        # Combinar scores
        final_score = max(role_score, air_defense_score) * combo_score * tactical_score
        
        # Informação de posicionamento
        position_info = self._get_position_priority(game_state, state)
        
        return [final_score, position_info]
    
    def _get_role_based_score(self, game_state: GameStateInfo, state) -> float:
        """Score baseado no papel atual (defesa ou suporte)"""
        
        base_score = 0.4
        
        # PAPEL DEFENSIVO: Responder a ameaças
        if game_state.should_defend:
            primary_threat = game_state.get_primary_threat()
            if primary_threat:
                # Mosqueteira é excelente contra tropas de médio HP
                medium_hp_threats = ['wizard', 'musketeer', 'electro_wizard', 'witch']
                if any(threat in primary_threat.card_name.lower() for threat in medium_hp_threats):
                    base_score += 0.5
                
                # Boa contra grupos se posicionada corretamente
                if primary_threat.threat_level == ThreatLevel.MEDIUM:
                    base_score += 0.3
        
        # PAPEL DE SUPORTE: Apoiar push
        elif game_state.should_attack:
            # Verificar se há tanque aliado no campo para apoiar
            # (implementação simplificada)
            base_score += 0.4
        
        return min(1.0, base_score)
    
    def _get_air_defense_score(self, game_state: GameStateInfo, state) -> float:
        """Score específico para defesa aérea"""
        
        air_threats = []
        air_threat_names = ['balloon', 'lava_hound', 'baby_dragon', 'minion', 'minion_horde']
        
        for threat in game_state.threats:
            if any(air_name in threat.card_name.lower() for air_name in air_threat_names):
                air_threats.append(threat)
        
        if not air_threats:
            return 0.3  # Score base baixo se não há ameaças aéreas
        
        # Score alto para ameaças aéreas críticas
        critical_air_threats = [t for t in air_threats if t.threat_level.value >= 3]
        if critical_air_threats:
            return 1.2  # Score muito alto
        
        # Score moderado para ameaças aéreas normais
        return 0.8
    
    def _get_combo_support_score(self, game_state: GameStateInfo, state) -> float:
        """Score baseado em oportunidades de combo como suporte"""
        
        if not self.combo_manager:
            return 1.0
        
        # Boost se faz parte de combo ativo
        combo_boost = self.combo_manager.get_combo_priority_boost(self.CARD)
        if combo_boost > 1.0:
            return combo_boost
        
        # Verificar se há tanque no campo que precisa de suporte
        # (implementação simplificada - em implementação real, verificar tropas aliadas)
        
        # Se temos elixir para combo e há oportunidade
        if state.numbers.elixir.number >= 7 and game_state.should_attack:
            return 1.3
        
        return 1.0
    
    def _get_tactical_score(self, game_state: GameStateInfo, state) -> float:
        """Score baseado em considerações táticas"""
        
        # Mosqueteira é melhor quando pode ficar protegida
        if len(game_state.threats) >= 3:  # Muitas ameaças = perigoso
            return 0.7
        
        # Boa quando temos vantagem de elixir
        if game_state.enemy_elixir_deficit >= 2:
            return 1.2
        
        # Timing baseado na fase do jogo
        if game_state.phase.value == 'early':
            return 0.9  # Menos prioritária no início
        elif game_state.phase.value in ['mid', 'late']:
            return 1.1  # Mais útil no meio/final
        
        return 1.0
    
    def _get_position_priority(self, game_state: GameStateInfo, state) -> float:
        """Determina prioridade de posicionamento"""
        
        # Se há ameaça aérea, posicionar para interceptar
        air_threats = [t for t in game_state.threats 
                      if any(air in t.card_name.lower() 
                            for air in ['balloon', 'minion', 'dragon'])]
        
        if air_threats:
            primary_air_threat = air_threats[0]
            threat_x = primary_air_threat.position[0]
            
            if threat_x <= 9:
                return -1.0  # Posicionar à esquerda
            else:
                return 1.0   # Posicionar à direita
        
        # Se há combo ativo, seguir posicionamento do combo
        if self.combo_manager and self.combo_manager.has_active_combo():
            return 0.0  # Posição será determinada pelo combo
        
        # Posicionamento baseado em ameaças terrestres
        ground_threats = [t for t in game_state.threats if t.threat_level.value >= 2]
        if ground_threats:
            primary_threat = ground_threats[0]
            threat_x = primary_threat.position[0]
            
            # Posicionar no lado oposto para flanquear
            if threat_x <= 9:
                return 1.0   # Ameaça à esquerda, Mosqueteira à direita
            else:
                return -1.0  # Ameaça à direita, Mosqueteira à esquerda
        
        return 0.0  # Sem preferência
    
    def _calculate_improved_basic_score(self, state):
        """Versão melhorada da lógica básica"""
        
        base_score = 0.4
        
        # Priorizar se há ameaças aéreas
        air_enemies = 0
        ground_enemies = 0
        
        for enemy in state.enemies:
            # Simplificado: assumir que inimigos em Y alto são aéreos
            if enemy.position.tile_y <= 10:
                air_enemies += 1
            else:
                ground_enemies += 1
        
        # Boost para ameaças aéreas
        if air_enemies > 0:
            base_score += 0.4
        
        # Boost moderado para ameaças terrestres
        if ground_enemies > 0:
            base_score += 0.2
        
        # Penalizar se muitos inimigos (perigoso para Mosqueteira)
        if len(state.enemies) >= 3:
            base_score *= 0.7
        
        # Boost se temos bastante elixir
        if state.numbers.elixir.number >= 7:
            base_score += 0.2
        
        return [max(0.0, min(1.0, base_score)), 0.0]
    
    def get_optimal_position(self, game_state: GameStateInfo, state):
        """Posicionamento ótimo da Mosqueteira"""
        
        # Se faz parte de combo, usar posição do combo
        if self.combo_manager and self.combo_manager.has_active_combo():
            combo_action = self.combo_manager.get_next_combo_action(0.0)
            if combo_action and combo_action[0] == self.CARD:
                return combo_action[2]
        
        if not game_state:
            return (9, 8)  # Posição padrão
        
        # MODO DEFENSIVO: Posicionar para interceptar ameaças
        if game_state.should_defend:
            primary_threat = game_state.get_primary_threat()
            if primary_threat:
                threat_x, threat_y = primary_threat.position
                
                # Contra ameaças aéreas: posicionar diretamente
                air_threats = ['balloon', 'minion', 'dragon', 'lava']
                if any(air in primary_threat.card_name.lower() for air in air_threats):
                    if threat_x <= 9:
                        return (7, 10)  # Interceptar à esquerda
                    else:
                        return (11, 10)  # Interceptar à direita
                
                # Contra ameaças terrestres: posicionar para flanquear
                else:
                    if threat_x <= 9:
                        return (11, 9)  # Flanquear pela direita
                    else:
                        return (7, 9)   # Flanquear pela esquerda
        
        # MODO OFENSIVO: Posicionar para suporte
        elif game_state.should_attack:
            # Posicionar atrás de tanques aliados (simplificado)
            return (9, 6)  # Posição de suporte padrão
        
        # MODO NEUTRO: Posição versátil
        return (9, 8)
    
    def should_prioritize_air_defense(self, game_state: GameStateInfo) -> bool:
        """Determina se deve priorizar defesa aérea"""
        
        air_threats = [t for t in game_state.threats 
                      if any(air in t.card_name.lower() 
                            for air in ['balloon', 'minion', 'dragon', 'lava'])]
        
        # Priorizar se há ameaças aéreas críticas
        critical_air_threats = [t for t in air_threats if t.threat_level.value >= 3]
        return len(critical_air_threats) > 0
    
    def get_support_effectiveness(self, game_state: GameStateInfo) -> float:
        """Calcula efetividade como carta de suporte"""
        
        base_effectiveness = 0.7
        
        # Mais efetiva quando há tanque para apoiar
        # (implementação simplificada)
        
        # Menos efetiva se há muitas ameaças (vulnerável)
        if len(game_state.threats) >= 3:
            base_effectiveness -= 0.2
        
        # Mais efetiva com vantagem de elixir
        if game_state.enemy_elixir_deficit >= 2:
            base_effectiveness += 0.2
        
        return min(1.0, base_effectiveness)

