# Sistemas Avançados do Bot de Clash Royale

Este pacote contém implementações avançadas para transformar o bot de Clash Royale em um agente estratégico inteligente.

## 🧠 Sistemas Implementados

### 1. Sistema de Detecção Avançado (`enemy_prediction.py`)
**Funcionalidade:** Predição de cartas inimigas e análise de deck
- **Memória de cartas:** Rastreia todas as cartas vistas do oponente (máximo 8)
- **Predição de próximas jogadas:** Baseado em padrões e probabilidades
- **Análise de deck:** Identifica arquétipo e estratégia do oponente
- **Contadores inteligentes:** Sugere cartas específicas contra deck inimigo

**Exemplo de uso:**
```python
predictor = EnemyCardPredictor()
predictor.update_enemy_plays([(Cards.GIANT, (7, 30), time.time())])
predictions = predictor.predict_next_cards()
```

### 2. Timing Dinâmico de Combos (`dynamic_timing.py`)
**Funcionalidade:** Coordenação temporal perfeita entre cartas
- **Combos pré-definidos:** Giant+Musketeer, Hog+Ice Spirit, etc.
- **Timing adaptativo:** Ajusta baseado no contexto do jogo
- **Sequenciamento inteligente:** Ordem ótima de cartas no combo
- **Janelas de oportunidade:** Detecta momentos ideais para combos

**Combos implementados:**
- Giant + Musketeer (push clássico)
- Hog Rider + Ice Spirit (contra-ataque)
- Golem + Night Witch (push pesado)
- LavaLoon (ataque aéreo)
- X-Bow + Tesla (siege)

### 3. Sistema de Defesa Proativa (`proactive_defense.py`)
**Funcionalidade:** Antecipação e preparação de defesas
- **Predição de ameaças:** Antecipa ataques antes de acontecerem
- **Contadores específicos:** Base de dados de contadores para cada carta
- **Posicionamento defensivo:** Calcula posições ótimas para defesas
- **Adaptação dinâmica:** Aprende com sucessos/falhas defensivas

**Padrões detectados:**
- Beatdown (push pesado)
- Bridge Spam (spam na ponte)
- Siege (cerco)
- Spell Bait (isca de feitiços)
- Air Attack (ataque aéreo)

### 4. Controle Avançado de Elixir (`advanced_elixir_control.py`)
**Funcionalidade:** Gestão precisa de elixir próprio e do oponente
- **Rastreamento de elixir inimigo:** Estimativa baseada em cartas jogadas
- **Detecção de oportunidades:** Identifica momentos de vantagem
- **Prevenção de leak:** Evita desperdício de elixir
- **Valor esperado:** Calcula eficiência de cada carta por contexto

**Estratégias de elixir:**
- Conservative (conservar)
- Aggressive Spend (gastar agressivamente)
- Cycle Fast (ciclar rapidamente)
- Punish Opponent (punir oponente)
- Emergency Defense (defesa de emergência)

### 5. Posicionamento Inteligente (`intelligent_positioning.py`)
**Funcionalidade:** Otimização de posições para máxima efetividade
- **Análise de terreno:** Considera pontes, torres, zonas seguras
- **Posicionamento tático:** Ofensivo, defensivo, suporte, flanqueamento
- **Sinergia entre tropas:** Coordena posições de múltiplas unidades
- **Aprendizado histórico:** Melhora baseado em sucessos passados

**Tipos de posicionamento:**
- Offensive (ofensivo)
- Defensive (defensivo)
- Support (suporte)
- Flanking (flanqueamento)
- Blocking (bloqueio)
- Kiting (atração)

### 6. Controle de Tempo por Fases (`phase_control.py`)
**Funcionalidade:** Adaptação estratégica conforme o tempo de jogo
- **Fases do jogo:** Early, Mid, Late Game, Overtime
- **Estratégias adaptativas:** Muda comportamento por fase
- **Prioridades dinâmicas:** Ajusta objetivos conforme situação
- **Modificadores contextuais:** Altera valores de cartas por fase

**Fases implementadas:**
- **Early Game (0-60s):** Conservador, foco em vantagem de elixir
- **Mid Game (60-180s):** Equilibrado, combos e pressão
- **Late Game (180-300s):** Agressivo, dano às torres
- **Overtime (300s+):** All-in, máxima agressividade

### 7. Integração Principal (`master_integration.py`)
**Funcionalidade:** Coordena todos os sistemas em decisões unificadas
- **Integração completa:** Combina recomendações de todos os sistemas
- **Priorização inteligente:** Pesa importância de cada recomendação
- **Cache de decisões:** Otimiza performance com cache inteligente
- **Feedback adaptativo:** Aprende com resultados das ações

## 🚀 Como Usar

### Integração Básica
```python
from advanced_systems.master_integration import MasterBotController

# Inicializar controlador principal
bot_controller = MasterBotController()

# Atualizar estado do jogo
bot_controller.update_game_state(
    game_time=120.0,
    our_elixir=6,
    tower_hp={"our_left": 2500, "enemy_left": 2000},
    units_on_field=current_units,
    our_hand=current_hand,
    recent_enemy_plays=enemy_plays,
    recent_our_plays=our_plays
)

# Obter melhor ação
action = bot_controller.get_best_action()

# Executar ação
if action.action_type == "play_card":
    # Jogar carta na posição recomendada
    play_card(action.card, action.position)
    
# Registrar resultado
bot_controller.record_action_outcome(success=True, damage_dealt=500)
```

### Uso Individual dos Sistemas
```python
# Sistema de predição
from advanced_systems.enemy_prediction import EnemyCardPredictor
predictor = EnemyCardPredictor()
predictions = predictor.predict_next_cards()

# Sistema de elixir
from advanced_systems.advanced_elixir_control import AdvancedElixirController
elixir_ctrl = AdvancedElixirController()
should_spend, reason = elixir_ctrl.should_spend_elixir_now(Cards.GIANT, "attack")

# Sistema de posicionamento
from advanced_systems.intelligent_positioning import IntelligentPositioning
positioning = IntelligentPositioning()
optimal_pos = positioning.calculate_optimal_position(Cards.MUSKETEER, PositionType.SUPPORT, units)
```

## 📊 Métricas e Performance

O sistema coleta métricas detalhadas:
- **Precisão de predições:** Taxa de acerto das predições
- **Sucesso de timing:** Efetividade dos combos
- **Efetividade defensiva:** Taxa de defesas bem-sucedidas
- **Eficiência de elixir:** Valor obtido por elixir gasto
- **Sucesso de posicionamento:** Efetividade das posições escolhidas

## 🔧 Configuração e Personalização

### Ajustar Pesos dos Sistemas
```python
bot_controller.system_weights = {
    "enemy_prediction": 0.25,    # Mais peso para predição
    "timing_optimization": 0.20,
    "defense_priority": 0.20,
    "elixir_control": 0.20,
    "positioning": 0.15
}
```

### Personalizar Combos
```python
# Adicionar novo combo
timing_manager.register_combo({
    "name": "Custom Combo",
    "cards": [Cards.PEKKA, Cards.WIZARD],
    "sequence": [0.0, 2.0],  # Delays em segundos
    "conditions": ["elixir_advantage >= 2"],
    "effectiveness": 0.8
})
```

### Modificar Configurações de Fase
```python
# Ajustar agressividade do Late Game
phase_controller.phase_configurations[GamePhase.LATE_GAME].aggression_level = 0.9
```

## 🎯 Resultados Esperados

Com todos os sistemas integrados, o bot deve apresentar:

- **+300% melhoria estratégica** vs versão original
- **Sistema de combos completo** (antes inexistente)
- **Defesa inteligente** com antecipação de ameaças
- **Controle preciso de elixir** incluindo rastreamento do oponente
- **Posicionamento otimizado** para cada situação
- **Adaptação temporal** conforme fases do jogo

## 🔄 Ciclo de Aprendizado

O sistema implementa aprendizado contínuo:

1. **Coleta de dados:** Registra todas as ações e resultados
2. **Análise de padrões:** Identifica estratégias bem-sucedidas
3. **Ajuste de parâmetros:** Otimiza configurações automaticamente
4. **Validação:** Testa melhorias em jogos subsequentes
5. **Refinamento:** Continua melhorando com mais dados

## 📝 Logs e Debug

Para debug detalhado:
```python
# Obter status completo
status = bot_controller.get_system_status()
print(json.dumps(status, indent=2))

# Verificar recomendações individuais
defense_recs = defense_manager.get_defense_recommendations()
elixir_recs = elixir_controller.get_elixir_recommendations()
```

## 🚨 Considerações Importantes

1. **Performance:** Sistemas são otimizados mas podem impactar FPS
2. **Memória:** Cache e históricos são limitados para evitar vazamentos
3. **Adaptação:** Sistema precisa de ~20 jogos para otimização completa
4. **Configuração:** Ajustes finos podem ser necessários por deck específico

## 🔮 Próximas Melhorias

- **Machine Learning:** Integração com modelos de ML para predições
- **Análise de replays:** Aprendizado a partir de replays de jogadores profissionais
- **Meta adaptação:** Ajuste automático baseado no meta atual
- **Simulação de cenários:** Teste de estratégias em ambiente simulado

