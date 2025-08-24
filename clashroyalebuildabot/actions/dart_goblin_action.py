from clashroyalebuildabot import Cards
from clashroyalebuildabot.actions.generic.action import Action

class Dart_GoblinAction(Action):
    CARD = Cards.DART_GOBLIN
    
    def calculate_score(self, state):
        # Lógica básica - pode ser melhorada depois
        return [0.5] if state.numbers.elixir.number >= self.CARD.cost else [0]
