# HLD / System Design Interview Handbook

A static, multi-page reference covering 20 high-level system design interview problems (URL Shortener, Rate Limiter, Twitter/News Feed, Chat System, Uber, Distributed Cache, Payment System, Dynamo-style Key-Value Store, build-your-own-Kafka, and more), each broken into requirements, capacity estimation, API design, data model, a naive design and why it breaks, seven deep dives, a full solution at scale, failure scenarios, trade-offs, and an interview simulation -- plus a Prerequisites primer on the recurring building blocks (Redis, Kafka, consistent hashing, CDNs, etc.) and a final Patterns Playbook synthesizing what recurs across all twenty problems.

Includes sidebar navigation, client-side search, a difficulty filter, dark mode, copy-to-clipboard code blocks, live-rendered Mermaid diagrams, and a mobile-responsive layout.

## Regenerating

This site is generated from `../hld-handbook.html` (the single-page source document). To rebuild after editing that source:

```bash
python3 build.py
```
