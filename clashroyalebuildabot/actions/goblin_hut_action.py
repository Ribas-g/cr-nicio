from clashroyalebuildabot import Cards
from clashroyalebuildabot.actions.generic.action import Action

class Goblin_HutAction(Action):
    CARD = Cards.GOBLIN_HUT
    
    def calculate_score(self, state):
        # Lógica básica - pode ser melhorada depois
        return [0.5] if state.numbers.elixir.number >= self.CARD.cost else [0]
