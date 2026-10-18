# Engineering Decisions

## 1. Modular monolith
**Context:** The assessment is time-boxed and the core domain is tightly related.  
**Options:** Microservices or a single modular API.  
**Choice:** FastAPI modular monolith, with API, models, schemas, and workflow rules separated.  
**Trade-off:** Simpler local development and transactions; less independent scaling than services.

## 2. Relational persistence
**Context:** Items, teams, memberships, comments, and activity events have relational constraints.  
**Options:** Relational database or document store.  
**Choice:** PostgreSQL for the recommended setup; SQLite is available as a local fallback.  
**Trade-off:** PostgreSQL provides stronger production-like concurrency behaviour; SQLite is easier to start but is not a substitute for PostgreSQL concurrency testing.

## 3. Optimistic concurrency
**Context:** Multiple users may edit an item from stale views.  
**Choice:** Clients submit the `version` they read. The API rejects stale versions with HTTP 409 and increments the version on a successful update.  
**Trade-off:** Conflicts require refresh/retry, but silent lost updates are prevented.

## 4. Authorization at the resource boundary
**Context:** Users belong to teams and roles differ by team.  
**Choice:** The API checks team membership and role for reads and mutations; UI visibility is not treated as a security boundary.  
**Trade-off:** More checks in service code, but unauthorized cross-team actions are rejected.

## 5. Transactional activity history
**Context:** History must not disagree with the work item's current state.  
**Choice:** Write the work-item mutation and its activity event in the same database transaction.  
**Trade-off:** Each mutation performs additional writes; the resulting history is more trustworthy.

## Intentionally not built
Email delivery, SSO, file attachments, WebSockets, a distributed queue, and mobile clients are excluded from the one-day MVP. A production version would add secure cookie-based sessions, rate limiting, structured observability, migrations, a notification outbox/worker, and deployment-specific secrets.
