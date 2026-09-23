# Dictionnaire des indicateurs

| Indicateur | Définition | Grain / limite |
|---|---|---|
| CA | Somme quantité × prix unitaire, en centimes ; affichage /100 | Ligne ; devise non attestée ici, unités monétaires |
| Factures | COUNT(*) de invoices | Facture |
| Acheteurs | COUNT(DISTINCT customer_id) | Période filtrée ; non additif |
| Panier moyen | CA / nombre de factures | Facture, pas prix moyen d'un morceau |
| Croissance mensuelle | (CA mois - CA précédent) / CA précédent | Premier mois et dénominateur nul : NULL |
| Part pays | CA pays / CA global | Pays de facturation, pas nationalité |
| Réachat | Acheteurs avec ≥2 factures / acheteurs | Toute la fenêtre ; pas taux de rétention mensuel |
| Valeur client observée | Somme des factures de ce client | Historique, pas customer lifetime value prédite |

## Tables

- `customers` : une ligne par identifiant client, pays de résidence source.
- `genres` : une ligne par genre.
- `tracks` : une ligne par morceau ; genre optionnel.
- `invoices` : une ligne par facture ; date source ISO stockée en texte pour portabilité.
- `invoice_lines` : une ligne par ligne de facture ; quantité positive.

## Connexion à Power BI

Le HTML livré est le tableau de bord exécuté. Aucun `.pbix` n'est revendiqué.
Pour créer une version Power BI : importer les cinq CSV de `data/processed/`, fixer les types numériques entiers, convertir `invoice_date` en date, puis créer les relations 1-N selon le schéma. Utiliser un filtre à sens unique des dimensions vers les faits.

```dax
CA = DIVIDE(SUMX(invoice_lines, invoice_lines[quantity] * invoice_lines[unit_price_cents]), 100)
Factures = DISTINCTCOUNT(invoices[invoice_id])
Acheteurs = DISTINCTCOUNT(invoices[customer_id])
Panier moyen = DIVIDE([CA], [Factures])
```

Ces mesures doivent être rapprochées de `reports/metrics.json` avant publication. Ne pas additionner le CA facture et le CA ligne dans une même mesure.
