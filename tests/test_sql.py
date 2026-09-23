import unittest, sqlite3, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class ReportingTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:'); self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript((ROOT/'sql/01_schema.sql').read_text(encoding='utf-8'))
        self.db.executescript("""
        INSERT INTO customers VALUES(1,'France'); INSERT INTO genres VALUES(1,'Rock');
        INSERT INTO tracks VALUES(1,'A',1); INSERT INTO tracks VALUES(2,'B',1);
        INSERT INTO invoices VALUES(1,1,'2026-01-01','France',300);
        INSERT INTO invoices VALUES(2,1,'2026-02-01','France',100);
        INSERT INTO invoice_lines VALUES(1,1,1,100,1);
        INSERT INTO invoice_lines VALUES(2,1,2,200,1);
        INSERT INTO invoice_lines VALUES(3,2,1,100,1);
        """)
        self.db.executescript((ROOT/'sql/02_views.sql').read_text(encoding='utf-8'))
    def tearDown(self): self.db.close()
    def test_one_to_many_does_not_inflate_revenue(self):
        self.assertEqual(self.db.execute('SELECT SUM(revenue_cents) FROM v_sales').fetchone()[0],400)
        self.assertEqual(self.db.execute('SELECT orders,revenue_cents FROM v_customer_value').fetchone(),(2,400))
    def test_reconciliation_detects_changed_invoice(self):
        text=(ROOT/'sql/03_analysis.sql').read_text(encoding='utf-8')
        query=text.split('-- name: reconciliation')[1]
        self.assertEqual(self.db.execute(query).fetchall(),[])
        self.db.execute('UPDATE invoices SET total_cents=301 WHERE invoice_id=1')
        self.assertEqual(len(self.db.execute(query).fetchall()),1)
    def test_invalid_foreign_key_and_quantity_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError): self.db.execute('INSERT INTO invoice_lines VALUES(4,999,1,100,1)')
        with self.assertRaises(sqlite3.IntegrityError): self.db.execute('INSERT INTO invoice_lines VALUES(4,1,1,100,0)')

if __name__=='__main__': unittest.main()
