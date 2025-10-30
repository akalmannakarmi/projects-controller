import os
import logging
import subprocess

NGINX_AVAILABLE = "/etc/nginx/sites-available"
NGINX_ENABLED = "/etc/nginx/sites-enabled"

logger = logging.getLogger(__name__)

STARTING_TEMPLATE = """
server {{
    server_name {domain};
    location / {{
        return 200 '<html><body style="text-align:center;font-family:sans-serif;"><h2>🚀 {project} is starting...</h2></body></html>';
        add_header Content-Type text/html;
    }}
}}
"""

OFFLINE_TEMPLATE = """
server {{
    server_name {domain};
    location / {{
        return 200 '<html><body style="text-align:center;font-family:sans-serif;"><h2>❌ {project} is offline.</h2></body></html>';
        add_header Content-Type text/html;
    }}
}}
"""

PROXY_TEMPLATE = """
server {{
    server_name {domain};
    location / {{
        proxy_pass http://{target_ip};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}
}}
"""


class NginxManager:
    def __init__(self):
        os.makedirs(NGINX_AVAILABLE, exist_ok=True)
        os.makedirs(NGINX_ENABLED, exist_ok=True)

    def _write_conf(self, name: str, content: str):
        path = os.path.join(NGINX_AVAILABLE, f"{name}.conf")
        with open(path, "w") as f:
            f.write(content)
        enabled = os.path.join(NGINX_ENABLED, f"{name}.conf")
        if not os.path.exists(enabled):
            os.symlink(path, enabled)
        self.reload_nginx()

    def set_state(
        self, project_name: str, domain: str, state: str, target_ip: str | None = None
    ):
        """Create conf for given state."""
        if state == "starting":
            conf = STARTING_TEMPLATE.format(domain=domain, project=project_name)
        elif state == "offline":
            conf = OFFLINE_TEMPLATE.format(domain=domain, project=project_name)
        elif state == "running" and target_ip:
            conf = PROXY_TEMPLATE.format(
                domain=domain, project=project_name, target_ip=target_ip
            )
        else:
            raise ValueError("Invalid Nginx state or missing target_ip")

        self._write_conf(project_name, conf)
        logger.info(f"Nginx config for {project_name} set to {state}")

    def reload_nginx(self):
        subprocess.run(["systemctl", "reload", "nginx"], check=False)
