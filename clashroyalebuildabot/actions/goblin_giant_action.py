from clashroyalebuildabot import Cards
from clashroyalebuildabot.actions.generic.action import Action

class Goblin_GiantAction(Action):
    CARD = Cards.GOBLIN_GIANT
    
    def calculate_score(self, state):
        # Lógica básica - pode ser melhorada depois
        return [0.5] if state.numbers.elixir.number >= self.CARD.cost else [0]
