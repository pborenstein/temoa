"""Main entry point for running Ixpantilia server"""
import uvicorn
from .config import Config


def main():
    """Run the Ixpantilia server"""
    config = Config()

    uvicorn.run(
        "ixpantilia.server:app",
        host=config.server_host,
        port=config.server_port,
        reload=False,  # Set to True for development
        log_level="info"
    )


if __name__ == "__main__":
    main()
