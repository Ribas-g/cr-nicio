# Bot de Clash Royale Aprimorado 🤖⚔️

Sistema inteligente de bot para Clash Royale com capacidades avançadas de estratégia, combos e defesa.

## 🚀 Principais Melhorias

### ✨ Sistema de Análise de Deck
- **Identificação automática de papéis**: Cada carta é classificada (Tanque, Suporte, Defesa, etc.)
- **Estratégias dinâmicas**: O bot adapta seu comportamento baseado na composição do deck
- **Análise contextual**: Entende quando ser agressivo ou defensivo

### 🎯 Sistema de Combos Inteligente
- **Combos coordenados**: Gigante + Mosqueteira, Corredor + Gelo, etc.
- **Timing perfeito**: Aguarda o momento ideal para executar combos
- **Sequenciamento**: Coordena múltiplas cartas com delays apropriados

### 🛡️ Defesa Aprimorada
- **Priorização de ameaças**: Identifica e responde às ameaças mais críticas
- **Contadores específicos**: Usa a carta ideal para cada tipo de ameaça
- **Defesas combinadas**: Coordena múltiplas cartas defensivas

### 🧠 Inteligência Contextual
- **Análise de estado do jogo**: Entende a situação atual e toma decisões apropriadas
- **Contra-ataques oportunos**: Aproveita quando o oponente gasta muito elixir
- **Posicionamento inteligente**: Cada carta sabe onde se posicionar

## 📁 Estrutura do Projeto

```
cr_bot_enhanced/
├── core/                    # Sistemas fundamentais
│   ├── card_roles.py       # Papéis e análise de deck
│   ├── game_state.py       # Análise do estado do jogo
│   ├── combo_system.py     # Sistema de combos
│   ├── defense_system.py   # Sistema de defesa
│   └── enhanced_action.py  # Classe base aprimorada
├── actions/                 # Ações específicas das cartas
│   ├── enhanced_giant_action.py
│   ├── enhanced_musketeer_action.py
│   └── enhanced_hog_rider_action.py
├── bot/                     # Bot principal
│   └── enhanced_bot.py     # Bot aprimorado
└── strategies/              # Estratégias específicas
```

## 🎮 Como Usar

### Integração Básica

```python
from cr_bot_enhanced import EnhancedBot

# Substituir o bot original
bot = EnhancedBot(actions, config)

# O bot automaticamente:
# 1. Analisa seu deck
# 2. Identifica estratégias
# 3. Configura combos disponíveis
# 4. Ativa sistemas inteligentes
```

### Configuração Avançada

```python
# Controlar sistemas individualmente
bot.toggle_intelligence(True)    # Sistema geral
bot.toggle_combo_system(True)    # Combos
bot.toggle_defense_system(True)  # Defesa

# Ver estatísticas
stats = bot.get_bot_stats()
print(f"Estratégia: {stats['deck_strategy']}")
print(f"Combos disponíveis: {stats['available_combos']}")
```

## 🎯 Combos Implementados

### Tanque + Suporte
- **Gigante + Mosqueteira**: Combo clássico de push
- **Gigante + Bombardeiro**: Controle de área
- **Golem + Bruxa Sombria**: Push pesado

### Ataques Rápidos
- **Corredor + Espírito de Gelo**: Contra-ataque veloz
- **Corredor + Tronco**: Limpeza de caminho

### Siege
- **Besta + Tesla**: Controle de área
- **Morteiro + Proteção**: Siege defensivo

## 🛡️ Sistema de Defesa

### Classificação de Ameaças
- **Crítica**: Tanques perto da torre (Gigante, Golem)
- **Alta**: Win conditions rápidas (Corredor, Balão)
- **Média**: Tropas de suporte
- **Baixa**: Tropas distantes

### Respostas Específicas
- **Contra tanques**: Torre Inferno, Mini P.E.K.K.A
- **Contra swarm**: Bombardeiro, Valquíria
- **Contra aéreo**: Mosqueteira, Arqueiras
- **Contra buildings**: Feitiços, tropas pesadas

## 📊 Análise de Deck

### Estratégias Identificadas
- **CYCLE**: Deck rápido com cartas baratas
- **HEAVY_TANK**: Deck com tanques pesados
- **DEFENSIVE**: Foco em defesa e contra-ataque
- **SPELL_BAIT**: Forçar uso de feitiços
- **BALANCED**: Estratégia equilibrada

### Papéis das Cartas
- **WIN_CONDITION**: Cartas que atacam torres
- **TANK**: Absorvem dano
- **SUPPORT**: Apoiam outras tropas
- **DEFENSE**: Especializadas em defender
- **SPELL**: Feitiços e utilidades
- **SWARM**: Tropas em grupo
- **CYCLE**: Cartas baratas para ciclar

## 🔧 Cartas Aprimoradas

### Gigante 🏰
- **Papel**: Tanque principal, iniciador de combos
- **Inteligência**: 
  - Espera momento ideal (vantagem de elixir)
  - Evita contadores pesados
  - Coordena com cartas de suporte
  - Posicionamento baseado em defesas inimigas

### Mosqueteira 🏹
- **Papel**: Suporte versátil, defesa aérea
- **Inteligência**:
  - Prioriza ameaças aéreas críticas
  - Posiciona-se para flanquear
  - Apoia tanques em combos
  - Adapta-se ao contexto (ataque/defesa)

### Corredor 🐗
- **Papel**: Contra-ataque rápido, pressão constante
- **Inteligência**:
  - Aproveita déficit de elixir inimigo
  - Evita contadores diretos
  - Timing perfeito para contra-ataques
  - Escolhe lane com menos defesas

## 📈 Melhorias vs Bot Original

| Aspecto | Bot Original | Bot Aprimorado |
|---------|-------------|----------------|
| **Estratégia** | Reativo simples | Proativo inteligente |
| **Combos** | ❌ Inexistente | ✅ Sistema completo |
| **Defesa** | 2 posições fixas | Priorização dinâmica |
| **Posicionamento** | Básico | Contextual |
| **Timing** | Aleatório | Calculado |
| **Coordenação** | ❌ Nenhuma | ✅ Entre cartas |

## 🎯 Resultados Esperados

### Melhor Performance
- **Combos coordenados** aumentam taxa de sucesso de ataques
- **Defesa inteligente** reduz dano recebido
- **Timing otimizado** maximiza eficiência do elixir

### Jogabilidade Mais Humana
- **Decisões contextuais** simulam pensamento estratégico
- **Adaptação dinâmica** responde a diferentes oponentes
- **Padrões reconhecíveis** como jogadores experientes

## 🔄 Próximas Melhorias

### Cartas Adicionais
- [ ] Golem aprimorado
- [ ] P.E.K.K.A inteligente
- [ ] Balão coordenado
- [ ] Feitiços contextuais

### Sistemas Avançados
- [ ] Predição de cartas inimigas
- [ ] Adaptação ao meta
- [ ] Aprendizado por reforço
- [ ] Análise de replays

## 🛠️ Instalação e Configuração

1. **Backup do projeto original**
2. **Copiar arquivos aprimorados**
3. **Atualizar imports**
4. **Testar funcionalidade**

## 📞 Suporte

Para dúvidas ou problemas:
- Verificar logs do sistema
- Testar com intelligence_enabled=False
- Comparar com bot original
- Ajustar configurações conforme necessário

---

**Desenvolvido com ❤️ para a comunidade Clash Royale**

