"""
Przykłady integracji BugBot z Docker i Kubernetes
"""

# === DOCKER COMPOSE ===
"""
# docker-compose.yml

version: '3.8'

services:
  # Twoja aplikacja
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs  # Współdzielone logi
      - bugbot-data:/app/data
    environment:
      - LOG_LEVEL=ERROR
      - LOG_PATH=/app/logs/app.log
    depends_on:
      - bugbot
      
  # BugBot jako osobny kontener
  bugbot:
    build:
      context: .
      dockerfile: Dockerfile.bugbot
    volumes:
      - ./logs:/app/logs:ro  # Read-only dostęp do logów
      - bugbot-data:/app/data
    environment:
      # Konfiguracja BugBot
      - BUGBOT_LOG_DIRS=/app/logs
      - BUGBOT_SCAN_INTERVAL=10
      - BUGBOT_SLACK_WEBHOOK=${BUGBOT_SLACK_WEBHOOK}
      - BUGBOT_GITHUB_TOKEN=${BUGBOT_GITHUB_TOKEN}
      - BUGBOT_GITHUB_OWNER=${GITHUB_OWNER}
      - BUGBOT_GITHUB_REPO=${GITHUB_REPO}
    restart: unless-stopped
    
  # Opcjonalnie: agregator logów
  fluentd:
    image: fluent/fluentd:latest
    volumes:
      - ./fluentd.conf:/fluentd/etc/fluent.conf
      - ./logs:/var/log/apps
    ports:
      - "24224:24224"
      
volumes:
  bugbot-data:
"""

# === DOCKERFILE DLA BUGBOT ===
"""
# Dockerfile.bugbot

FROM python:3.11-slim

WORKDIR /app

# Instaluj zależności
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiuj kod BugBot
COPY src/services/bugbot /app/src/services/bugbot
COPY src/services/__init__.py /app/src/services/

# Utwórz katalogi
RUN mkdir -p /app/logs /app/data

# Uruchom BugBot
CMD ["python", "-u", "src/services/bugbot/run_bugbot.py"]
"""

# === KUBERNETES DEPLOYMENT ===
"""
# bugbot-deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: bugbot
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: bugbot
  template:
    metadata:
      labels:
        app: bugbot
    spec:
      serviceAccountName: bugbot
      containers:
      - name: bugbot
        image: myregistry/bugbot:latest
        env:
        - name: BUGBOT_LOG_DIRS
          value: "/var/log/pods,/app/logs"
        - name: BUGBOT_SCAN_INTERVAL
          value: "30"
        - name: BUGBOT_SLACK_WEBHOOK
          valueFrom:
            secretKeyRef:
              name: bugbot-secrets
              key: slack-webhook
        - name: BUGBOT_GITHUB_TOKEN
          valueFrom:
            secretKeyRef:
              name: bugbot-secrets
              key: github-token
        volumeMounts:
        - name: varlog
          mountPath: /var/log
          readOnly: true
        - name: app-logs
          mountPath: /app/logs
          readOnly: true
        - name: bugbot-data
          mountPath: /app/data
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: app-logs
        persistentVolumeClaim:
          claimName: app-logs-pvc
      - name: bugbot-data
        persistentVolumeClaim:
          claimName: bugbot-data-pvc
---
# Serwis dla API BugBot
apiVersion: v1
kind: Service
metadata:
  name: bugbot-api
  namespace: monitoring
spec:
  selector:
    app: bugbot
  ports:
  - port: 8080
    targetPort: 8000
    protocol: TCP
  type: ClusterIP
---
# ServiceAccount z uprawnieniami do czytania logów
apiVersion: v1
kind: ServiceAccount
metadata:
  name: bugbot
  namespace: monitoring
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: bugbot-log-reader
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: bugbot-log-reader-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: bugbot-log-reader
subjects:
- kind: ServiceAccount
  name: bugbot
  namespace: monitoring
"""

# === SIDECAR PATTERN ===
"""
# deployment-with-bugbot-sidecar.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  template:
    spec:
      containers:
      # Główna aplikacja
      - name: app
        image: myapp:latest
        volumeMounts:
        - name: shared-logs
          mountPath: /app/logs
          
      # BugBot jako sidecar
      - name: bugbot-sidecar
        image: bugbot:latest
        env:
        - name: BUGBOT_LOG_DIRS
          value: "/shared/logs"
        - name: BUGBOT_MODE
          value: "sidecar"
        volumeMounts:
        - name: shared-logs
          mountPath: /shared/logs
          readOnly: true
          
      volumes:
      - name: shared-logs
        emptyDir: {}
"""

# === DAEMONSET DLA MONITOROWANIA WSZYSTKICH NODÓW ===
"""
# bugbot-daemonset.yaml

apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: bugbot-node-monitor
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: bugbot-node-monitor
  template:
    metadata:
      labels:
        app: bugbot-node-monitor
    spec:
      hostNetwork: true
      hostPID: true
      containers:
      - name: bugbot
        image: bugbot:latest
        env:
        - name: BUGBOT_LOG_DIRS
          value: "/var/log/containers,/var/log/pods"
        - name: NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        volumeMounts:
        - name: varlog
          mountPath: /var/log
          readOnly: true
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
          readOnly: true
        securityContext:
          privileged: true
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers
"""

# === HELM CHART ===
"""
# helm/bugbot/values.yaml

replicaCount: 1

image:
  repository: myregistry/bugbot
  tag: latest
  pullPolicy: IfNotPresent

config:
  logDirs:
    - /var/log/pods
    - /app/logs
  scanInterval: 30
  escalationThreshold: 10
  
notifications:
  slack:
    enabled: true
    webhookUrl: ""  # Set via --set or secrets
  discord:
    enabled: false
    webhookUrl: ""
  email:
    enabled: false
    smtpServer: smtp.gmail.com
    smtpPort: 587
    
github:
  enabled: false
  token: ""  # Set via secrets
  owner: ""
  repo: ""
  
resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"
    
persistence:
  enabled: true
  size: 10Gi
  storageClass: "standard"
  
monitoring:
  prometheus:
    enabled: true
    port: 9090
"""

# === INTEGRACJA Z LOGGING STACK ===
"""
# fluentd.conf dla agregacji logów

<source>
  @type tail
  path /var/log/apps/*.log
  pos_file /var/log/fluentd/app.log.pos
  tag app.*
  <parse>
    @type multiline
    format_firstline /^\d{4}-\d{2}-\d{2}/
    format1 /^(?<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (?<level>\w+) \[(?<component>\w+)\] (?<message>.*)/
  </parse>
</source>

# Filtruj błędy
<filter app.**>
  @type grep
  <regexp>
    key level
    pattern /ERROR|CRITICAL|WARNING/
  </regexp>
</filter>

# Wyślij do BugBot
<match app.**>
  @type http
  endpoint http://bugbot-api:8080/webhooks/error-report
  open_timeout 2
  <format>
    @type json
  </format>
  <buffer>
    flush_interval 10s
  </buffer>
</match>
"""

# === DOCKER SDK INTEGRATION ===

import docker
import json
import asyncio
from datetime import datetime

class DockerLogMonitor:
    """Monitor logów kontenerów Docker"""
    
    def __init__(self, bugbot_url: str = "http://localhost:8000/api/bugbot"):
        self.client = docker.from_env()
        self.bugbot_url = bugbot_url
        
    async def monitor_container_logs(self, container_name: str):
        """Monitoruje logi konkretnego kontenera"""
        try:
            container = self.client.containers.get(container_name)
            
            # Stream logów
            for log_line in container.logs(stream=True, follow=True):
                log_text = log_line.decode('utf-8').strip()
                
                # Sprawdź czy to błąd
                if any(level in log_text.upper() for level in ['ERROR', 'CRITICAL', 'EXCEPTION']):
                    await self._report_error(container_name, log_text)
                    
        except docker.errors.NotFound:
            print(f"Container {container_name} not found")
        except Exception as e:
            print(f"Error monitoring container: {e}")
            
    async def monitor_all_containers(self, label_filter: str = None):
        """Monitoruje wszystkie kontenery (opcjonalnie z filtrem label)"""
        filters = {}
        if label_filter:
            filters['label'] = label_filter
            
        containers = self.client.containers.list(filters=filters)
        
        # Uruchom monitoring dla każdego kontenera
        tasks = []
        for container in containers:
            task = asyncio.create_task(
                self.monitor_container_logs(container.name)
            )
            tasks.append(task)
            
        await asyncio.gather(*tasks)
        
    async def _report_error(self, container_name: str, log_line: str):
        """Raportuje błąd do BugBot"""
        error_data = {
            "source": f"docker:{container_name}",
            "timestamp": datetime.now().isoformat(),
            "log_line": log_line,
            "container": container_name
        }
        
        # Log lokalnie
        with open(f"logs/docker_{container_name}.log", "a") as f:
            f.write(f"{error_data['timestamp']} {log_line}\n")


# Użycie
async def main():
    monitor = DockerLogMonitor()
    
    # Monitoruj wszystkie kontenery z etykietą "monitor=bugbot"
    await monitor.monitor_all_containers(label_filter="monitor=bugbot")

# === GITHUB ACTIONS INTEGRATION ===
"""
# .github/workflows/error-monitoring.yml

name: Error Monitoring
on:
  workflow_run:
    workflows: ["CI/CD Pipeline"]
    types: [completed]

jobs:
  check-logs:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    
    steps:
    - name: Download logs artifact
      uses: actions/download-artifact@v3
      with:
        name: test-logs
        path: ./logs
        
    - name: Send logs to BugBot
      run: |
        # Znajdź błędy w logach
        grep -E "ERROR|FAILED|EXCEPTION" ./logs/*.log > errors.txt || true
        
        if [ -s errors.txt ]; then
          # Wyślij do BugBot przez webhook
          curl -X POST ${{ secrets.BUGBOT_WEBHOOK }} \
            -H "Content-Type: application/json" \
            -d '{
              "system": "github-actions",
              "workflow": "${{ github.event.workflow_run.name }}",
              "run_id": "${{ github.event.workflow_run.id }}",
              "errors": "'$(cat errors.txt | jq -Rs .)'"
            }'
        fi
"""