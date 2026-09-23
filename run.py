"""ETL et reporting Chinook. Exécuter : python run.py"""
from pathlib import Path
from urllib.request import urlopen
from decimal import Decimal
import sqlite3, csv, json, hashlib, re, html, logging, shutil

ROOT=Path(__file__).resolve().parent
URL='https://github.com/lerocha/chinook-database/releases/download/v1.4.5/Chinook_Sqlite.sqlite'

def cents(value):
    return int((Decimal(str(value))*100).quantize(Decimal('1')))

def run():
    out=ROOT/'reports'; out.mkdir(exist_ok=True)
    raw=ROOT/'data/raw/chinook.sqlite'; raw.parent.mkdir(parents=True,exist_ok=True)
    if not raw.exists():
        with urlopen(URL,timeout=90) as r,raw.with_suffix('.part').open('wb') as f:
            shutil.copyfileobj(r,f)
        raw.with_suffix('.part').replace(raw)
    src=sqlite3.connect(f'{raw.as_uri()}?mode=ro',uri=True)
    # Reconstruire uniquement notre base générée dans data/processed.
    processed=ROOT/'data/processed'; processed.mkdir(exist_ok=True)
    db=processed/'reporting.sqlite'
    tmp=processed/'reporting.tmp.sqlite'
    tmp.unlink(missing_ok=True)
    con=sqlite3.connect(tmp); con.execute('PRAGMA foreign_keys=ON')
    con.executescript((ROOT/'sql/01_schema.sql').read_text(encoding='utf-8'))
    queries={
        'customers':'SELECT CustomerId,Country FROM Customer',
        'genres':'SELECT GenreId,Name FROM Genre',
        'tracks':'SELECT TrackId,Name,GenreId FROM Track',
        'invoices':'SELECT InvoiceId,CustomerId,InvoiceDate,BillingCountry,Total FROM Invoice',
        'invoice_lines':'SELECT InvoiceLineId,InvoiceId,TrackId,UnitPrice,Quantity FROM InvoiceLine',
    }
    for table,query in queries.items():
        rows=[list(r) for r in src.execute(query)]
        if table=='invoices':
            for row in rows: row[-1]=cents(row[-1])
        if table=='invoice_lines':
            for row in rows: row[3]=cents(row[3])
        con.executemany(f'INSERT INTO {table} VALUES ({",".join("?" for _ in rows[0])})',rows)
        headers=[r[1] for r in con.execute(f'PRAGMA table_info({table})')]
        with (processed/f'{table}.csv').open('w',newline='',encoding='utf-8') as f:
            writer=csv.writer(f); writer.writerow(headers); writer.writerows(rows)
    con.executescript((ROOT/'sql/02_views.sql').read_text(encoding='utf-8'))
    checks={'foreign_key_errors':len(con.execute('PRAGMA foreign_key_check').fetchall())}
    result={}
    for name,query in re.findall(r'-- name: (\w+)\n(.*?)(?=-- name:|\Z)',(ROOT/'sql/03_analysis.sql').read_text(encoding='utf-8'),re.S):
        cur=con.execute(query); columns=[d[0] for d in cur.description]
        rows=cur.fetchall(); result[name]=[dict(zip(columns,r)) for r in rows]
        with (out/f'{name}.csv').open('w',newline='',encoding='utf-8') as f:
            writer=csv.writer(f); writer.writerow(columns); writer.writerows(rows)
    checks['invoice_mismatches']=len(result['reconciliation'])
    checks['joined_line_count_matches']=con.execute('SELECT COUNT(*) FROM v_sales').fetchone()[0]==con.execute('SELECT COUNT(*) FROM invoice_lines').fetchone()[0]
    checks['revenue_totals_match']=con.execute('SELECT SUM(total_cents) FROM invoices').fetchone()[0]==con.execute('SELECT SUM(revenue_cents) FROM v_sales').fetchone()[0]
    assert checks['foreign_key_errors']==0 and checks['invoice_mismatches']==0
    assert checks['joined_line_count_matches'] and checks['revenue_totals_match']
    totals=dict(zip(['orders','revenue_cents','buyers','first_date','last_date'],con.execute('SELECT COUNT(*),SUM(total_cents),COUNT(DISTINCT customer_id),MIN(invoice_date),MAX(invoice_date) FROM invoices').fetchone()))
    months=[r['month'] for r in result['monthly_growth']]
    # LAG doit comparer des mois consécutifs, pas simplement des observations.
    serial=[int(m[:4])*12+int(m[5:]) for m in months]
    assert all(b-a==1 for a,b in zip(serial,serial[1:])), 'Mois absents : compléter un calendrier avant le calcul de croissance.'
    report={'source_sha256':hashlib.file_digest(raw.open('rb'),'sha256').hexdigest(),'totals':totals,'checks':checks}
    (out/'metrics.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    dashboard(result,totals,out)
    top=result['countries'][0]; genre=result['genres'][0]
    (out/'synthese.md').write_text(f'''# Résultats exécutés

{totals['orders']} factures, {totals['buyers']} acheteurs, CA de {totals['revenue_cents']/100:.2f} unités monétaires.
Période : {totals['first_date']} à {totals['last_date']}.
Premier pays de facturation : {top['billing_country']} ({top['share_percent']} % du CA).
Premier genre : {genre['genre']} ({genre['revenue_cents']/100:.2f}).

Les contrôles de jointure, de clés étrangères et de rapprochement des montants passent.
Chinook contient des ventes générées : ces résultats illustrent la méthode et ne décrivent pas un marché réel.
Le taux de réachat porte sur toute la fenêtre observée, sans interprétation causale ni prévision.
Une décision commerciale nécessiterait des données réelles sur la marge, les coûts et les périodes comparables.
''',encoding='utf-8')
    con.commit(); con.close(); src.close(); tmp.replace(db)
    logging.info('Reporting produit : %s',out)
    print(json.dumps(report,indent=2))
    return report

def dashboard(results,totals,out):
    rows=results['countries'][:10]; maximum=max(r['revenue_cents'] for r in rows)
    bars=''.join(f'<div class="bar"><span>{html.escape(r["billing_country"])}</span><i style="width:{r["revenue_cents"]/maximum*65:.1f}%"></i><b>{r["revenue_cents"]/100:.2f}</b></div>' for r in rows)
    monthrows=''.join('<tr>'+''.join(f'<td>{html.escape(str(r[k]))}</td>' for k in ['month','orders','active_customers'])+f'<td>{r["revenue_cents"]/100:.2f}</td></tr>' for r in results['monthly_growth'])
    page=f'''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Chinook | Reporting</title>
<style>body{{font:16px system-ui;background:#f3f6fa;color:#183047;margin:0;padding:40px;max-width:1050px;margin:auto}}h1{{font-size:42px}}.cards{{display:flex;gap:16px;flex-wrap:wrap}}article{{background:white;padding:24px;border-radius:12px;flex:1}}strong{{font-size:30px;display:block;color:#007f86}}.bar{{display:flex;align-items:center;gap:10px;margin:12px 0}}.bar span{{width:150px}}i{{background:#008d93;height:20px}}b{{font-size:13px}}table{{border-collapse:collapse;width:100%}}td,th{{padding:10px;text-align:left;border-bottom:1px solid #ccd5df}}summary{{cursor:pointer}}footer{{margin-top:30px;color:#536577}}</style>
<p>LAYLA EL GOZMIR · PROJET SQL</p><h1>Ventes et clients</h1><p>Base pédagogique Chinook · montants en unités monétaires</p>
<div class="cards"><article>Chiffre d'affaires<strong>{totals['revenue_cents']/100:,.2f}</strong></article><article>Factures<strong>{totals['orders']}</strong></article><article>Acheteurs<strong>{totals['buyers']}</strong></article></div>
<h2>Les dix premiers pays de facturation</h2>{bars}<h2>Évolution mensuelle</h2><details open><summary>Afficher les indicateurs mensuels</summary><table><thead><tr><th>Mois</th><th>Factures</th><th>Clients actifs</th><th>CA</th></tr></thead><tbody>{monthrows}</tbody></table></details>
<footer>Source : Chinook v1.4.5. Ventes synthétiques. Total de facture jamais additionné après jointure au détail. Les CSV complets accompagnent ce tableau de bord.</footer></html>'''
    (out/'dashboard.html').write_text(page,encoding='utf-8')

if __name__=='__main__':
    logging.basicConfig(level=logging.INFO,format='%(levelname)s %(message)s')
    run()
