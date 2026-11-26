# GeoDashboard Backend

**FastAPI-based Geospatial Analytics & AI Insight Backend**

This repository contains the backend system for **GeoDashboard**, a full-stack geospatial analytics platform focused on spatial analysis, system design, and responsible AI integration.

The backend handles authentication, dataset ingestion, geospatial analytics, and AI-assisted analytical insights in a production-style environment.

---

## Key Features

- FastAPI backend with JWT authentication  
- PostgreSQL + SQLAlchemy ORM  
- Deterministic geospatial analysis (density, clustering, aggregation)  
- AI-powered analytical insights with strict per-user rate limits  
- Docker-ready core and optional AI service entrypoints with health and readiness probes
- GitHub Actions validation for linting, tests, and container builds
- Prometheus-compatible API metrics and request-correlated structured logs

---

## Architecture

The Render service runs app.main:app. Its routers share authentication, a SQLAlchemy session and the GIS analysis schema. The AI router reads the signed-in user's analysis, calls Gemini over HTTPS and records usage in Neon PostgreSQL. Set GEMINI_API_KEY on Render to enable summaries. Override GEMINI_MODEL to select an available text model.

The former AWS deployment remains available via app.ai_main:app. Only set AI_MODE=remote and AI_SERVICE_URL on the core API when deliberately routing requests to that service.

---

## Tech Stack

- FastAPI
- SQLAlchemy
- PostgreSQL
- Docker
- Google Gemini (AI insights)
- GitHub Actions (CI)
- Prometheus-compatible metrics

## Deployment notes

The public core API is deployed separately from the Vercel frontend and uses Neon PostgreSQL. Local Kubernetes manifests, Prometheus/Grafana resources, and Terraform registry bootstrap configuration are maintained in the main [GeoDashboard repository](https://github.com/heimweh17/Geo-Dashboard/tree/main/infra).

---

## Main Project

This backend powers the full GeoDashboard platform.

🔗 **Main Repository:**  
https://github.com/heimweh17/Geo-Dashboard

🔗 **Live Demo:**  
https://thegeodashboard.vercel.app/

---

## Author

**Alex Liu**  
Computer Science @ University of Florida  

https://aliu.me  
https://github.com/heimweh17
