# Known Limitations

- Demo users and sample data are seeded for evaluation; there is no self-service sign-up.
- Local demo credentials are intentionally simple and must not be reused in production.
- The frontend uses session storage for the JWT; production should use secure HttpOnly cookies and CSRF protection.
- SQLite fallback is intended only for quick local development; use PostgreSQL to evaluate database concurrency.
- No email, file attachments, SSO, WebSockets, or background job worker.
- Search uses database `LIKE` queries; a larger deployment may use PostgreSQL full-text search.
- Cursor pagination and advanced analytics are not implemented in this starter; the API uses bounded page/limit pagination.
- Rate limiting, comprehensive audit-log retention controls, and production observability remain future work.
