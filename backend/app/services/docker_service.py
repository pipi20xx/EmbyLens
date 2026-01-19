import docker
from typing import List, Dict, Any, Optional
from app.utils.logger import logger

class DockerService:
    def __init__(self, host_config: Dict[str, Any]):
        self.host_config = host_config
        self.client = self._get_client()

    def _get_client(self):
        try:
            host_type = self.host_config.get("type", "local")
            if host_type == "local":
                return docker.from_env()
            elif host_type == "ssh":
                # SSH connection string: ssh://user@host:port
                ssh_host = self.host_config.get("ssh_host")
                ssh_user = self.host_config.get("ssh_user", "root")
                ssh_port = self.host_config.get("ssh_port", 22)
                
                base_url = f"ssh://{ssh_user}@{ssh_host}:{ssh_port}"
                # Docker SDK uses paramiko for SSH if use_ssh_client is False (default)
                # or uses system ssh if use_ssh_client is True.
                # Here we let it handle via base_url.
                return docker.DockerClient(base_url=base_url, use_ssh_client=True)
            else:
                return docker.DockerClient(base_url=self.host_config.get("base_url"))
        except Exception as e:
            logger.error(f"Failed to connect to Docker host {self.host_config.get('name')}: {e}")
            return None

    def list_containers(self, all=True) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        try:
            containers = self.client.containers.list(all=all)
            return [
                {
                    "id": c.short_id,
                    "full_id": c.id,
                    "name": c.name,
                    "image": c.image.tags[0] if c.image.tags else c.image.id,
                    "status": c.status,
                    "state": c.attrs.get("State", {}),
                    "created": c.attrs.get("Created"),
                    "ports": c.attrs.get("NetworkSettings", {}).get("Ports", {})
                }
                for c in containers
            ]
        except Exception as e:
            logger.error(f"Error listing containers: {e}")
            return []

    def container_action(self, container_id: str, action: str):
        if not self.client:
            return False
        try:
            container = self.client.containers.get(container_id)
            if action == "start":
                container.start()
            elif action == "stop":
                container.stop()
            elif action == "restart":
                container.restart()
            elif action == "remove":
                container.remove(force=True)
            return True
        except Exception as e:
            logger.error(f"Error performing action {action} on container {container_id}: {e}")
            return False

    def get_container_logs(self, container_id: str, tail=100) -> str:
        if not self.client:
            return "Not connected to Docker"
        try:
            container = self.client.containers.get(container_id)
            return container.logs(tail=tail).decode("utf-8")
        except Exception as e:
            logger.error(f"Error getting logs for container {container_id}: {e}")
            return str(e)

    def test_connection(self) -> bool:
        if not self.client:
            return False
        try:
            return self.client.ping()
        except Exception:
            return False
