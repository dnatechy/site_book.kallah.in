# Database migrations

Booking/queue/payment tables are deliberately not created in foundation phase.
Use versioned, reviewed MariaDB migrations here once the domain model is approved.
Never run production migrations automatically on import or during Passenger startup.
