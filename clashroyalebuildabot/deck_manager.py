import os
import yaml
from typing import Dict, List, Any

from clashroyalebuildabot.constants import SRC_DIR
from clashroyalebuildabot.actions import *

# Mapeamento de nomes de ação para classes
ACTION_MAPPING = {}

# Criar mapeamento dinamicamente para todas as Actions
from clashroyalebuildabot.actions import __all__ as action_names
for action_name in action_names:
    action_class = globals()[action_name]
    ACTION_MAPPING[action_name] = action_class


class DeckManager:
    def __init__(self):
        self.decks_file = os.path.join(SRC_DIR, "decks.yaml")
        self.decks = self._load_decks()
        self.current_deck = self.decks.get("default_deck", "meu_deck_atual")

    def _load_decks(self) -> Dict[str, Any]:
        """Carrega os decks do arquivo YAML"""
        try:
            with open(self.decks_file, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
                if data is None:
                    raise FileNotFoundError("Arquivo vazio")
                return data
        except (FileNotFoundError, yaml.YAMLError) as e:
            # Retorna deck padrão se arquivo não existir
            return {
                "meu_deck_atual": {
                    "name": "Meu Deck Atual",
                    "description": "Deck padrão",
                    "cards": ["KnightAction", "ArchersAction", "SkeletonsAction", 
                             "SpearGoblinsAction", "CannonAction", "GiantAction", 
                             "MinipekkaAction", "MusketeerAction"]
                },
                "default_deck": "meu_deck_atual"
            }

    def get_available_decks(self) -> List[Dict[str, str]]:
        """Retorna lista de decks disponíveis"""
        available_decks = []
        decks_data = self.decks.get("decks", {})
        for deck_id, deck_data in decks_data.items():
            available_decks.append({
                "id": deck_id,
                "name": deck_data["name"],
                "description": deck_data["description"]
            })
        return available_decks

    def get_deck_actions(self, deck_id: str = None) -> List:
        """Retorna as ações de um deck específico"""
        if deck_id is None:
            deck_id = self.current_deck
        
        decks_data = self.decks.get("decks", {})
        if deck_id not in decks_data:
            raise ValueError(f"Deck '{deck_id}' não encontrado")
        
        deck_data = decks_data[deck_id]
        actions = []
        
        for card_name in deck_data["cards"]:
            if card_name in ACTION_MAPPING:
                actions.append(ACTION_MAPPING[card_name])
            else:
                raise ValueError(f"Ação '{card_name}' não encontrada")
        
        return actions

    def get_current_deck_info(self) -> Dict[str, str]:
        """Retorna informações do deck atual"""
        decks_data = self.decks.get("decks", {})
        deck_data = decks_data[self.current_deck]
        return {
            "id": self.current_deck,
            "name": deck_data["name"],
            "description": deck_data["description"]
        }

    def set_current_deck(self, deck_id: str):
        """Define o deck atual"""
        decks_data = self.decks.get("decks", {})
        if deck_id in decks_data:
            self.current_deck = deck_id
        else:
            raise ValueError(f"Deck '{deck_id}' não encontrado")

    def save_deck(self, deck_id: str, name: str, description: str, cards: List[str]):
        """Salva um novo deck ou atualiza um existente"""
        if "decks" not in self.decks:
            self.decks["decks"] = {}
        
        self.decks["decks"][deck_id] = {
            "name": name,
            "description": description,
            "cards": cards
        }
        
        with open(self.decks_file, 'w', encoding='utf-8') as file:
            yaml.dump(self.decks, file, default_flow_style=False, allow_unicode=True)

    def delete_deck(self, deck_id: str):
        """Remove um deck"""
        decks_data = self.decks.get("decks", {})
        if deck_id in decks_data and deck_id != "meu_deck_atual":
            del decks_data[deck_id]
            with open(self.decks_file, 'w', encoding='utf-8') as file:
                yaml.dump(self.decks, file, default_flow_style=False, allow_unicode=True)
        else:
            raise ValueError("Não é possível deletar este deck")
