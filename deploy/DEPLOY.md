# Deploying TrendCraft to Oracle Cloud (Always Free)

Runs the full stack — app, API, Postgres+pgvector, Redis, Celery worker and beat —
on one always-free ARM VM with automatic HTTPS. **Cost: $0.**

Oracle's Always Free tier grants up to **4 ARM cores and 24 GB RAM**, which is
more than enough; the whole stack idles around 2 GB.

---

## 1. Create the VM

In the OCI console: **Compute → Instances → Create instance**

| Setting | Value |
|---|---|
| Image | Ubuntu 24.04 |
| Shape | `VM.Standard.A1.Flex` — **Ampere/ARM**, marked *Always Free eligible* |
| OCPUs / Memory | 2 OCPU / 12 GB is plenty (4/24 is the free ceiling) |
| Boot volume | 50–100 GB |
| SSH key | Upload your public key |

**Capacity type** (under Placement → Advanced options): choose **On-demand
capacity**. Not *Preemptible* — Oracle can reclaim those at any moment. Not
*Compute cluster* or *Dedicated host* — neither is Always Free eligible.

**Cloud-init** lives at the *bottom* of the form, not under Placement:
**Advanced options → Management → Initialization script**. Paste
[`cloud-init.yaml`](cloud-init.yaml) there.

> Missed it, or the box isn't there? Run [`bootstrap.sh`](bootstrap.sh) after
> your first SSH instead — it does exactly the same work and is safe to re-run.

> **If capacity errors appear** ("Out of host capacity"), that is normal for free
> ARM shapes in busy regions. Retry, or pick a different availability domain.

### Open the ports in the VCN

**Networking → Virtual Cloud Networks → your VCN → Security Lists → Default**

Add two ingress rules:

| Source | Protocol | Port |
|---|---|---|
| `0.0.0.0/0` | TCP | 80 |
| `0.0.0.0/0` | TCP | 443 |

> This is separate from the host firewall. Oracle images also carry an iptables
> ruleset that drops everything but SSH — the cloud-init script handles that side.
> **Both** must be open, and forgetting the iptables half is the most common
> reason a working deployment looks unreachable.

---

## 2. Point a domain at it

Caddy needs a real hostname to issue a certificate. Either:

- A domain you own → `A` record to the instance's public IP, or
- A free subdomain from [DuckDNS](https://www.duckdns.org) → `yourname.duckdns.org`

Verify before continuing — TLS issuance fails otherwise:

```bash
dig +short yourdomain.com     # must print the instance IP
```

---

## 3. Deploy

```bash
ssh ubuntu@<instance-ip>

git clone <your-repo-url> /opt/trendcraft
cd /opt/trendcraft

cp .env.example .env
nano .env
```

Set these — the first three are mandatory:

```bash
DOMAIN=yourdomain.com
POSTGRES_PASSWORD=<generate: openssl rand -base64 24>
PIPELINE_TOKEN=<generate: openssl rand -base64 32>

GOOGLE_API_KEY=...        # Gemini + YouTube
YOUTUBE_API_KEY=...
APIFY_TOKEN=...           # optional, for TikTok/Instagram
```

Then bring it up:

```bash
docker compose -f docker-compose.yml -f deploy/docker-compose.prod.yml up -d --build
```

The first build takes **10–20 minutes on ARM** — it compiles the Next bundle and
installs scikit-learn. Subsequent deploys are much faster.

Watch certificate issuance:

```bash
docker compose logs -f caddy
```

Then open `https://yourdomain.com`.

---

## 4. Seed and collect

```bash
cd /opt/trendcraft
TOKEN=$(sed -n 's/^PIPELINE_TOKEN=//p' .env)   # sed, not cut: base64 padding contains '='

# Verify providers before spending any quota
docker compose exec api python -m scripts.check_keys

# First real collection
curl -X POST https://yourdomain.com/api/v1/pipeline/run \
  -H 'Content-Type: application/json' \
  -H "X-Pipeline-Token: $TOKEN" \
  -d '{"platforms":["youtube"],"niches":["ai tools","productivity"],"async_run":false}'
```

After that, Celery beat runs collection every 3h, analysis every 10 min and
re-clustering nightly — no cron needed.

---

## 5. Backups

```bash
crontab -e
```

```cron
0 4 * * * /opt/trendcraft/deploy/backup.sh >> /var/log/trendcraft-backup.log 2>&1
```

Keeps 7 nightly dumps in `/opt/trendcraft-backups` and fails loudly on a
truncated dump rather than silently retaining a useless file.

Restore:

```bash
gunzip -c /opt/trendcraft-backups/trendcraft-YYYYMMDD-HHMMSS.sql.gz \
  | docker compose exec -T postgres psql -U trendcraft -d trendcraft
```

---

## Updating

```bash
cd /opt/trendcraft && git pull
docker compose -f docker-compose.yml -f deploy/docker-compose.prod.yml up -d --build
```

## Operating notes

**What is exposed.** Only Caddy publishes ports. Postgres, Redis and the API are
reachable only on the internal Docker network — the API is public solely through
`/api/*` on the proxy.

**Same-origin by design.** Caddy serves the app and the API on one hostname, so
the browser never makes a cross-origin request. CORS simply does not arise.

**`/pipeline/*` is guarded** by `X-Pipeline-Token`, because those routes spend
Gemini quota, YouTube quota and Apify credit. `/pipeline/status` stays open — it
is read-only and the Settings page uses it.

**Everything else is still unauthenticated.** Any visitor can browse trends and
generate scenarios, which costs Gemini quota. Before sharing the URL widely,
either put Caddy `basic_auth` in front of the whole site or implement real auth
in `backend/app/api/deps.py::get_current_user`.

**Free-tier reality.** Gemini's free tier allows ~20 requests/day/model, so
trend narration and video analysis will be heavily rate-limited. The pipeline
degrades to deterministic fallbacks rather than failing — see the README.

**Disk.** Images total ~2 GB; Postgres grows slowly (roughly 1 GB per 100k
videos). `docker system prune -af` after updates reclaims old layers.
