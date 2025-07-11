import logging


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with the specified name and logging level.

    Args:
        name (str): Name of the logger.
        level (int, optional): Logging level (default is logging.INFO).

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding multiple handlers if logger already has handlers
    if not logger.handlers:
        # Create console handler and set level
        ch = logging.StreamHandler()
        ch.setLevel(level)

        # Create formatter and add it to the handler
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        ch.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(ch)

    return logger
