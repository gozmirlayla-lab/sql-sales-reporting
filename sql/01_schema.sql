-- Grain : une ligne de facture = un morceau acheté sur une facture.
CREATE TABLE customers (customer_id INTEGER PRIMARY KEY, country TEXT NOT NULL);
CREATE TABLE genres (genre_id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE tracks (track_id INTEGER PRIMARY KEY, name TEXT NOT NULL,
    genre_id INTEGER REFERENCES genres(genre_id));
CREATE TABLE invoices (invoice_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    invoice_date TEXT NOT NULL, billing_country TEXT NOT NULL,
    total_cents INTEGER NOT NULL CHECK(total_cents >= 0));
CREATE TABLE invoice_lines (line_id INTEGER PRIMARY KEY,
    invoice_id INTEGER NOT NULL REFERENCES invoices(invoice_id),
    track_id INTEGER NOT NULL REFERENCES tracks(track_id),
    unit_price_cents INTEGER NOT NULL CHECK(unit_price_cents >= 0),
    quantity INTEGER NOT NULL CHECK(quantity > 0));
CREATE INDEX ix_invoice_customer ON invoices(customer_id);
CREATE INDEX ix_line_invoice ON invoice_lines(invoice_id);
