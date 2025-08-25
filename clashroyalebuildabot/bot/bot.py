import random
import threading
import time

import keyboard
from loguru import logger

from clashroyalebuildabot.constants import ALL_TILES
from clashroyalebuildabot.constants import ALLY_TILES
from clashroyalebuildabot.constants import DISPLAY_CARD_DELTA_X
from clashroyalebuildabot.constants import DISPLAY_CARD_HEIGHT
from clashroyalebuildabot.constants import DISPLAY_CARD_INIT_X
from clashroyalebuildabot.constants import DISPLAY_CARD_WIDTH
from clashroyalebuildabot.constants import DISPLAY_CARD_Y
from clashroyalebuildabot.constants import DISPLAY_HEIGHT
from clashroyalebuildabot.constants import LEFT_PRINCESS_TILES
from clashroyalebuildabot.constants import RIGHT_PRINCESS_TILES
from clashroyalebuildabot.constants import TILE_HEIGHT
from clashroyalebuildabot.constants import TILE_INIT_X
from clashroyalebuildabot.constants import TILE_INIT_Y
from clashroyalebuildabot.constants import TILE_WIDTH
from clashroyalebuildabot.detectors import Detector
from clashroyalebuildabot.emulator import Emulator
from clashroyalebuildabot.namespaces import Screens
from clashroyalebuildabot.visualizer import Visualizer
from clashroyalebuildabot.utils.health_monitor import HealthMonitor
from error_handling import WikifiedError

pause_event = threading.Event()
pause_event.set()
is_paused_logged = False
is_resumed_logged = True


class Bot:
    is_paused_logged = False
    is_resumed_logged = True

    def __init__(self, actions, config):
        self.actions = actions
        self.auto_start = config["bot"]["auto_start_game"]
        self.end_of_game_clicked = False
        self.should_run = True

        cards = [action.CARD for action in actions]
        if len(cards) != 8:
            raise WikifiedError(
                "005", f"Must provide 8 cards but {len(cards)} was given"
            )
        self.cards_to_actions = dict(zip(cards, actions))

        self.visualizer = Visualizer(**config["visuals"])
        self.emulator = Emulator(**config["adb"])
        self.detector = Detector(cards=cards)
        self.state = None
        self.play_action_delay = config.get("ingame", {}).get("play_action", 1)
        
        # Sistema de performance monitoring
        self.performance_monitor = {
            'step_times': [],
            'avg_step_time': 0.0,
            'last_optimization': time.time(),
            'optimization_interval': 30.0  # Otimizar a cada 30 segundos
        }
        
        # Inicializar monitor de saúde
        self.health_monitor = HealthMonitor(config)
        self.health_monitor.add_health_callback(self._on_health_issue)
        self.health_monitor.start_monitoring()

        keyboard_thread = threading.Thread(
            target=self._handle_keyboard_shortcut, daemon=True
        )
        keyboard_thread.start()

        if config["bot"]["load_deck"]:
            self.emulator.load_deck(cards)

    @staticmethod
    def _log_and_wait(prefix, delay):
        suffix = ""
        if delay > 1:
            suffix = "s"
        message = f"{prefix}. Waiting for {delay} second{suffix}."
        logger.info(message)
        time.sleep(delay)

    @staticmethod
    def _handle_keyboard_shortcut():
        while True:
            keyboard.wait("ctrl+p")
            Bot.pause_or_resume()

    @staticmethod
    def pause_or_resume():
        if pause_event.is_set():
            logger.info("Bot paused.")
            pause_event.clear()
            Bot.is_paused_logged = True
            Bot.is_resumed_logged = False
        else:
            logger.info("Bot resumed.")
            pause_event.set()
            Bot.is_resumed_logged = True
            Bot.is_paused_logged = False

    @staticmethod
    def _get_nearest_tile(x, y):
        tile_x = round(((x - TILE_INIT_X) / TILE_WIDTH) - 0.5)
        tile_y = round(
            ((DISPLAY_HEIGHT - TILE_INIT_Y - y) / TILE_HEIGHT) - 0.5
        )
        return tile_x, tile_y

    @staticmethod
    def _get_tile_centre(tile_x, tile_y):
        x = TILE_INIT_X + (tile_x + 0.5) * TILE_WIDTH
        y = DISPLAY_HEIGHT - TILE_INIT_Y - (tile_y + 0.5) * TILE_HEIGHT
        return x, y

    @staticmethod
    def _get_card_centre(card_n):
        x = (
            DISPLAY_CARD_INIT_X
            + DISPLAY_CARD_WIDTH / 2
            + card_n * DISPLAY_CARD_DELTA_X
        )
        y = DISPLAY_CARD_Y + DISPLAY_CARD_HEIGHT / 2
        return x, y

    def _get_valid_tiles(self):
        tiles = ALLY_TILES
        if self.state.numbers.left_enemy_princess_hp.number == 0:
            tiles += LEFT_PRINCESS_TILES
        if self.state.numbers.right_enemy_princess_hp.number == 0:
            tiles += RIGHT_PRINCESS_TILES
        return tiles

    def get_actions(self):
        if not self.state:
            return []
        valid_tiles = self._get_valid_tiles()
        actions = []
        for i in self.state.ready:
            card = self.state.cards[i + 1]
            if self.state.numbers.elixir.number < card.cost:
                continue

            tiles = ALL_TILES if card.target_anywhere else valid_tiles
            card_actions = [
                self.cards_to_actions[card](i, x, y) for (x, y) in tiles
            ]
            actions.extend(card_actions)

        return actions

    def set_state(self):
        try:
            screenshot = self.emulator.take_screenshot()
            self.state = self.detector.run(screenshot)
            self.visualizer.run(screenshot, self.state)
        except Exception as e:
            logger.error(f"Erro ao definir estado: {str(e)}")
            import traceback
            logger.error(f"Traceback do set_state: {traceback.format_exc()}")
            # Criar estado vazio em caso de erro
            from clashroyalebuildabot.namespaces import State
            self.state = State([], [], [], [], False, None)

    def play_action(self, action):
        card_centre = self._get_card_centre(action.index)
        tile_centre = self._get_tile_centre(action.tile_x, action.tile_y)
        self.emulator.click(*card_centre)
        self.emulator.click(*tile_centre)

    def _handle_play_pause_in_step(self):
        if not pause_event.is_set():
            if not Bot.is_paused_logged:
                logger.info("Bot paused.")
                Bot.is_paused_logged = True
            time.sleep(0.05)  # Reduzido de 0.1 para 0.05
            return
        if not Bot.is_resumed_logged:
            logger.info("Bot resumed.")
            Bot.is_resumed_logged = True

    def step(self):
        step_start_time = time.time()
        try:
            self._handle_play_pause_in_step()
            old_screen = self.state.screen if self.state else None
            self.set_state()
            new_screen = self.state.screen
            if new_screen != old_screen:
                logger.info(f"New screen state: {new_screen}")

            if new_screen == Screens.UNKNOWN:
                self._log_and_wait("Unknown screen", 0.5)  # Reduzido de 2 para 0.5
                return

            if new_screen == Screens.END_OF_GAME:
                if not self.end_of_game_clicked:
                    self.emulator.click(*self.state.screen.click_xy)
                    self.end_of_game_clicked = True
                    self._log_and_wait("Clicked END_OF_GAME screen", 0.5)  # Reduzido de 2 para 0.5
                return

            self.end_of_game_clicked = False

            if self.auto_start and new_screen == Screens.LOBBY:
                self.emulator.click(*self.state.screen.click_xy)
                self.end_of_game_clicked = False
                self._log_and_wait("Starting game", 0.5)  # Reduzido de 2 para 0.5
                return

            self._handle_game_step()
            
        except Exception as e:
            logger.error(f"Erro no step: {str(e)}")
            import traceback
            logger.error(f"Traceback do step: {traceback.format_exc()}")
            time.sleep(0.5)  # Reduzido de 1 para 0.5 segundos
        finally:
            # Monitorar performance
            self._monitor_performance(step_start_time)

    def _handle_game_step(self):
        actions = self.get_actions()
        if not actions:
            self._log_and_wait("No actions available", self.play_action_delay)
            return

        random.shuffle(actions)
        best_score = [0]
        best_action = None
        for action in actions:
            score = action.calculate_score(self.state)
            if score > best_score:
                best_action = action
                best_score = score

        if best_score[0] == 0:
            self._log_and_wait(
                "No good actions available", self.play_action_delay
            )
            return

        self.play_action(best_action)
        self._log_and_wait(
            f"Playing {best_action} with score {best_score}",
            self.play_action_delay,
        )

    def run(self):
        try:
            logger.info("Bot iniciado com sucesso")
            last_step_time = time.time()
            min_step_interval = 0.1  # Intervalo mínimo entre steps (100ms)
            
            while self.should_run:
                try:
                    if not pause_event.is_set():
                        time.sleep(0.05)  # Reduzido de 0.1 para 0.05
                        continue

                    # Controle de framerate para evitar sobrecarga
                    current_time = time.time()
                    if current_time - last_step_time < min_step_interval:
                        time.sleep(0.01)  # Sleep muito pequeno para manter responsividade
                        continue
                    
                    last_step_time = current_time
                    self.step()
                    
                except Exception as e:
                    logger.error(f"Erro durante execução do step: {str(e)}")
                    logger.error(f"Tipo de erro: {type(e).__name__}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    
                    # Registrar erro no monitor de saúde
                    if hasattr(self, 'health_monitor'):
                        self.health_monitor.record_error()
                    
                    time.sleep(1)  # Reduzido de 2 para 1 segundo
                    continue
                    
            logger.info("Thanks for using CRBAB, see you next time!")
        except KeyboardInterrupt:
            logger.info("Bot interrompido pelo usuário")
        except Exception as e:
            logger.error(f"Erro crítico no bot: {str(e)}")
            import traceback
            logger.error(f"Traceback completo: {traceback.format_exc()}")
        finally:
            logger.info("Bot finalizado")

    def _on_health_issue(self, issue_type: str, value: float):
        """Callback para problemas de saúde detectados"""
        logger.warning(f"Problema de saúde detectado: {issue_type} = {value}")
        
        if issue_type == "high_error_rate":
            logger.warning("Muitos erros detectados, pausando bot temporariamente")
            pause_event.clear()  # Pausar bot
            time.sleep(10)  # Pausa de 10 segundos
            pause_event.set()  # Retomar bot
            
    def stop(self):
        self.should_run = False
        if hasattr(self, 'health_monitor'):
            self.health_monitor.stop_monitoring()
    
    def _monitor_performance(self, step_start_time: float):
        """Monitora a performance do bot e ajusta automaticamente"""
        
        step_time = time.time() - step_start_time
        self.performance_monitor['step_times'].append(step_time)
        
        # Manter apenas os últimos 100 steps
        if len(self.performance_monitor['step_times']) > 100:
            self.performance_monitor['step_times'] = self.performance_monitor['step_times'][-100:]
        
        # Calcular tempo médio
        self.performance_monitor['avg_step_time'] = sum(self.performance_monitor['step_times']) / len(self.performance_monitor['step_times'])
        
        # Otimizar periodicamente
        current_time = time.time()
        if current_time - self.performance_monitor['last_optimization'] > self.performance_monitor['optimization_interval']:
            self._optimize_performance()
            self.performance_monitor['last_optimization'] = current_time
    
    def _optimize_performance(self):
        """Otimiza a performance baseada nos dados coletados"""
        
        avg_time = self.performance_monitor['avg_step_time']
        
        # Se o tempo médio está muito alto, reduzir delays
        if avg_time > 0.5:  # Mais de 500ms por step
            if self.play_action_delay > 0.1:
                self.play_action_delay *= 0.8  # Reduzir 20%
                logger.info(f"Performance lenta detectada. Reduzindo delay para {self.play_action_delay:.2f}s")
        
        # Se o tempo médio está muito baixo, podemos ser mais agressivos
        elif avg_time < 0.1:  # Menos de 100ms por step
            if self.play_action_delay < 0.5:
                self.play_action_delay *= 1.1  # Aumentar 10%
                logger.info(f"Performance boa detectada. Aumentando delay para {self.play_action_delay:.2f}s")
        
        # Log de performance a cada 30 segundos
        logger.info(f"Performance: {avg_time:.3f}s/step, Delay: {self.play_action_delay:.2f}s")
    
    def get_performance_stats(self) -> dict:
        """Retorna estatísticas de performance"""
        
        return {
            'avg_step_time': self.performance_monitor['avg_step_time'],
            'play_action_delay': self.play_action_delay,
            'total_steps': len(self.performance_monitor['step_times']),
            'fps_estimate': 1.0 / max(0.001, self.performance_monitor['avg_step_time'])
        }
