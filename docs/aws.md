# Extension AWS — PostgreSQL RDS

**Statut : procédure proposée, non exécutée.** Le projet livré et validé fonctionne en SQLite local. Aucun compte, secret ou service AWS n'a été créé. RDS peut être payant.

1. Exécuter `python run.py` pour produire les CSV contrôlés.
2. Préparer une base PostgreSQL dédiée, accessible seulement depuis un poste/réseau autorisé. Utiliser TLS (`sslmode=verify-full` et certificat CA approprié), un utilisateur aux droits limités et un secret hors du dépôt.
3. Depuis `psql`, dans une base vide, exécuter `sql/01_schema.sql`. Le schéma utilise des types compatibles PostgreSQL, sans fonctionnalité SQLite spécifique.
4. Importer les CSV dans l'ordre des dépendances. Depuis la racine du dépôt :

```sql
\copy customers FROM 'data/processed/customers.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
\copy genres FROM 'data/processed/genres.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
\copy tracks FROM 'data/processed/tracks.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
\copy invoices FROM 'data/processed/invoices.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
\copy invoice_lines FROM 'data/processed/invoice_lines.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
\i sql/02_views.sql
\i sql/03_analysis.sql
```

5. Comparer les sorties avec les CSV `reports/` et exiger zéro ligne au rapprochement. Adapter les fonctions numériques si la version PostgreSQL l'exige, puis tester la précision des montants.
6. Donner au compte de reporting des droits SELECT seulement. Connecter Power BI aux vues validées. Documenter date, région, version PostgreSQL, coûts et résultats des contrôles.
7. Prévoir une sauvegarde et l'arrêt/suppression des ressources de démonstration après usage, selon les règles du compte.

Une mention « hébergé sur AWS » sur le CV ne correspondra à cette version qu'après ce déploiement et sa vérification.
