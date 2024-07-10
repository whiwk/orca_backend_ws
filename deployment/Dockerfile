FROM python:3.10-slim

LABEL maintainer="gintingari73@gmail.com"

# set and install requirement packages
COPY . /app
WORKDIR /install
ENV TZ=Asia/Jakarta
ENV KUBECONFIG=/app/deployment/kube-config
RUN apt-get update && apt-get install -y curl tcpdump tshark && \
    pip install --no-cache-dir -r /app/requirements.txt && \
    curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl && \
    chmod +x ./kubectl && chmod 600 $KUBECONFIG && \
    mv ./kubectl /usr/local/bin/kubectl && \
    curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 && \
    chmod +x get_helm.sh && ./get_helm.sh && \
    rm -rf /install && rm -rf /var/lib/apt/lists/*
WORKDIR /app

#running service
EXPOSE 8002
CMD ["daphne", "-b", "0.0.0.0", "-p", "8002", "orca_backend_ws.asgi:application"]