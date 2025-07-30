import docker
from docker.api import APIClient
import logging

# --- Basic Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
AGENT_IMAGE_TAG = 'agent-service:latest'


def build_agent_image():
    """Builds the agent Docker image using the low-level APIClient."""
    client = None
    try:
        # Use the low-level APIClient with the verified socket path.
        client = APIClient(base_url='unix:///Users/tc/.docker/run/docker.sock', user_agent='Docker-Py-Builder')
        client.ping()
        logging.info("Successfully connected to Docker.")
    except Exception as e:
        logging.error(f"CRITICAL: Failed to connect to Docker. Please ensure Docker is running. Error: {e}")
        return False

    logging.info(f"Attempting to build Docker image '{AGENT_IMAGE_TAG}' from path './agent'...")
    try:
        build_logs = client.build(
            path='./agent',
            tag=AGENT_IMAGE_TAG,
            rm=True,
            decode=True  # Decode JSON stream
        )
        for log in build_logs:
            if 'stream' in log:
                print(log['stream'].strip())
            elif 'error' in log:
                logging.error(f"Build Error: {log['error']}")
                return False
        logging.info(f"Image '{AGENT_IMAGE_TAG}' built successfully.")
        return True
    except Exception as e:
        # The credential helper warning can sometimes be raised as an exception.
        # We check if the image was built anyway.
        if "docker-credential-desktop" in str(e):
            logging.warning("Ignoring ignorable docker-credential-desktop warning and checking if image exists.")
            try:
                if client.images(name=AGENT_IMAGE_TAG):
                    logging.info("Image found after credential warning. Build is considered successful.")
                    return True
            except Exception as check_e:
                logging.error(f"Build failed after credential warning. Check error: {check_e}")
                return False

        logging.error(f"An unexpected error occurred during image build: {e}")
        return False


if __name__ == '__main__':
    if build_agent_image():
        print("\n✅ Docker image built successfully!")
    else:
        print("\n❌ Docker image build failed.")
