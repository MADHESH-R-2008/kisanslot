# KisanSlot

The Flutter app and admin dashboard use the FastAPI backend at the configured
cloud API URL. The backend persists all centre changes through SQLAlchemy using
`DATABASE_URL`; it must point to a managed cloud database in production.

## Deploying the cloud backend

Deploy this repository using [render.yaml](render.yaml). In the Render service
environment set `DATABASE_URL` to your managed MySQL connection string (using
the `mysql+pymysql://user:password@host:3306/database` format) and `SECRET_KEY`
to a long random value.

Do not use `sqlite:///...` on Render: its local disk is ephemeral, so data may
disappear after a restart or redeploy. For local development, copy
`backend/.env.example` to `backend/.env`.

The blueprint also deploys `kisanslot-admin` as a Render static site. It is
configured at build time with the cloud API and WebSocket endpoints. To use a
different backend, change `VITE_API_URL` and `VITE_WS_URL` in that service's
Render environment, then trigger a new deploy.

## Getting Started

This project is a starting point for a Flutter application.

A few resources to get you started if this is your first Flutter project:

- [Learn Flutter](https://docs.flutter.dev/get-started/learn-flutter)
- [Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Flutter learning resources](https://docs.flutter.dev/reference/learning-resources)

For help getting started with Flutter development, view the
[online documentation](https://docs.flutter.dev/), which offers tutorials,
samples, guidance on mobile development, and a full API reference.
