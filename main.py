from error_handling import WikifiedError

try:
    import signal
    import sys

    from loguru import logger
    from PyQt6.QtWidgets import QApplication


    from clashroyalebuildabot.gui.main_window import MainWindow
    from clashroyalebuildabot.gui.utils import load_config
    from clashroyalebuildabot.utils.git_utils import check_and_pull_updates
    from clashroyalebuildabot.utils.logger import setup_logger
except Exception as e:
    raise WikifiedError("001", "Missing imports.") from e


def main():
    check_and_pull_updates()
    
    # Carregar deck padrão
    from clashroyalebuildabot.deck_manager import DeckManager
    deck_manager = DeckManager()
    actions = deck_manager.get_deck_actions()
    
    try:
        config = load_config()

        app = QApplication([])
        window = MainWindow(config, actions)
        setup_logger(window, config)

        window.show()
        sys.exit(app.exec())
    except WikifiedError:
        raise
    except Exception as e:
        logger.error(f"An error occurred in main loop: {e}")
        sys.exit(1)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
