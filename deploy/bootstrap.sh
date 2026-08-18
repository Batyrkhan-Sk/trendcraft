#!/usr/bin/env bash
# Same work as cloud-init.yaml, for when the console's initialization-script box
# was missed or is unavailable. Safe to run more than once.
#
#   ssh ubuntu@<instance-ip>
#   curl -fsSL https://raw.githubusercontent.com/<you>/<repo>/main/deploy/bootstrap.sh | bash
#
# ...or just paste this file into the instance and run `bash bootstrap.sh`.
set -euo pipefail

log() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }

# Never prompt. iptables-persistent in particular asks whether to save the
# current ruleset, and answering "No" there silently discards the port 80/443
# rules on the next reboot — the site simply stops responding with no obvious
# cause. Pre-answer both questions instead of relying on the operator.
export DEBIAN_FRONTEND=noninteractive

log "Updating packages"
sudo apt-get update -qq
sudo apt-get install -y -qq ca-certificates curl git gnupg ufw

log "Installing Docker Engine + Compose plugin"
if ! command -v docker >/dev/null 2>&1; then
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo tee /etc/apt/keyrings/docker.asc >/dev/null
  sudo chmod a+r /etc/apt/keyrings/docker.asc
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
  sudo apt-get update -qq
  sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  sudo systemctl enable --now docker
  sudo usermod -aG docker "$USER"
else
  echo "Docker already present, skipping."
fi

# Oracle's Ubuntu images carry an iptables ruleset that DROPs everything except
# SSH, and it persists across reboots. Opening 80/443 in the VCN security list
# is not sufficient — this half is the one people miss.
log "Opening ports 80/443 on the host firewall"
sudo iptables -C INPUT -p tcp --dport 80 -j ACCEPT 2>/dev/null \
  || sudo iptables -I INPUT 5 -p tcp --dport 80 -j ACCEPT
sudo iptables -C INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null \
  || sudo iptables -I INPUT 6 -p tcp --dport 443 -j ACCEPT
if ! command -v netfilter-persistent >/dev/null 2>&1; then
  echo 'iptables-persistent iptables-persistent/autosave_v4 boolean true' | sudo debconf-set-selections
  echo 'iptables-persistent iptables-persistent/autosave_v6 boolean true' | sudo debconf-set-selections
  sudo apt-get install -y -qq iptables-persistent || true
fi
# Save unconditionally: the install-time autosave only captures rules that
# existed before this script inserted its own.
sudo netfilter-persistent save >/dev/null 2>&1 || true

if sudo grep -qE 'dport (80|443)' /etc/iptables/rules.v4 2>/dev/null; then
  echo "  ports 80/443 persisted to /etc/iptables/rules.v4"
else
  echo "  WARNING: could not confirm persistence; ufw below is the fallback"
fi
sudo ufw allow OpenSSH  >/dev/null 2>&1 || true
sudo ufw allow 80/tcp   >/dev/null 2>&1 || true
sudo ufw allow 443/tcp  >/dev/null 2>&1 || true
sudo ufw --force enable >/dev/null 2>&1 || true

# `next build` is the memory-hungry step; swap is cheap insurance against an OOM
# part-way through a deploy.
log "Adding 4G swap"
if ! sudo swapon --show | grep -q /swapfile; then
  sudo fallocate -l 4G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile >/dev/null
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
else
  echo "Swap already configured, skipping."
fi

log "Enabling unattended security upgrades"
sudo apt-get install -y -qq unattended-upgrades
sudo dpkg-reconfigure -f noninteractive unattended-upgrades

log "Creating directories"
sudo mkdir -p /opt/trendcraft /opt/trendcraft-backups
sudo chown -R "$USER:$USER" /opt/trendcraft /opt/trendcraft-backups

cat <<'DONE'

Bootstrap complete.

  IMPORTANT: log out and back in so your shell picks up the docker group,
  otherwise every docker command needs sudo:

    exit
    ssh ubuntu@<instance-ip>

  Then:

    git clone <your-repo-url> /opt/trendcraft
    cd /opt/trendcraft
    cp .env.example .env && nano .env      # set DOMAIN, POSTGRES_PASSWORD, PIPELINE_TOKEN
    docker compose -f docker-compose.yml -f deploy/docker-compose.prod.yml up -d --build

DONE
