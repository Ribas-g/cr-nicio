from clashroyalebuildabot import Cards
from clashroyalebuildabot.actions.generic.action import Action

class Minion_HordeAction(Action):
    CARD = Cards.MINION_HORDE
    
    def calculate_score(self, state):
        # Lógica básica - pode ser melhorada depois
        return [0.5] if state.numbers.elixir.number >= self.CARD.cost else [0]
