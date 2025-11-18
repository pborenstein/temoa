"""Main entry point for running Temoa server"""
import uvicorn
from .config import Config


def main():
    """Run the Temoa server"""
    config = Config()

    uvicorn.run(
        "temoa.server:app",
        host=config.server_host,
        port=config.server_port,
        reload=False,  # Set to True for development
        log_level="info"
    )


if __name__ == "__main__":
    main()
