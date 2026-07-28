# Migration de données — peuple la base avec les 20 entités de l'ASECNA :
# 1 SIÈGE (Dakar, Sénégal), 17 REPRÉSENTATIONS (États membres hors Sénégal,
# la France étant rattachée à la délégation de Paris) et 2 DÉLÉGATIONS.
# Liste officielle des 19 États membres (source : www.asecna.aero, Rwanda
# 19e État membre depuis le 1er janvier 2024).
from django.db import migrations

ENTITES = [
    # (code, libelle, type_entite, pays, fuseau_horaire)
    ('SIEGE',   'Siège de Dakar',                    'SIEGE',          'Sénégal',            'Africa/Dakar'),
    ('REP-BJ',  'Représentation du Bénin',           'REPRESENTATION', 'Bénin',              'Africa/Porto-Novo'),
    ('REP-BF',  'Représentation du Burkina Faso',    'REPRESENTATION', 'Burkina Faso',       'Africa/Ouagadougou'),
    ('REP-CM',  'Représentation du Cameroun',        'REPRESENTATION', 'Cameroun',           'Africa/Douala'),
    ('REP-CF',  'Représentation de Centrafrique',    'REPRESENTATION', 'Centrafrique',       'Africa/Bangui'),
    ('REP-KM',  'Représentation des Comores',        'REPRESENTATION', 'Union des Comores',  'Indian/Comoro'),
    ('REP-CG',  'Représentation du Congo',           'REPRESENTATION', 'Congo',              'Africa/Brazzaville'),
    ('REP-CI',  "Représentation de Côte d'Ivoire",   'REPRESENTATION', "Côte d'Ivoire",      'Africa/Abidjan'),
    ('REP-GA',  'Représentation du Gabon',           'REPRESENTATION', 'Gabon',              'Africa/Libreville'),
    ('REP-GW',  'Représentation de Guinée-Bissau',   'REPRESENTATION', 'Guinée-Bissau',      'Africa/Bissau'),
    ('REP-GQ',  'Représentation de Guinée équatoriale', 'REPRESENTATION', 'Guinée équatoriale', 'Africa/Malabo'),
    ('REP-MG',  'Représentation de Madagascar',      'REPRESENTATION', 'Madagascar',         'Indian/Antananarivo'),
    ('REP-ML',  'Représentation du Mali',            'REPRESENTATION', 'Mali',               'Africa/Bamako'),
    ('REP-MR',  'Représentation de Mauritanie',      'REPRESENTATION', 'Mauritanie',         'Africa/Nouakchott'),
    ('REP-NE',  'Représentation du Niger',           'REPRESENTATION', 'Niger',              'Africa/Niamey'),
    ('REP-RW',  'Représentation du Rwanda',          'REPRESENTATION', 'Rwanda',             'Africa/Kigali'),
    ('REP-TD',  'Représentation du Tchad',           'REPRESENTATION', 'Tchad',              'Africa/Ndjamena'),
    ('REP-TG',  'Représentation du Togo',            'REPRESENTATION', 'Togo',               'Africa/Lome'),
    ('DEL-PAR', 'Délégation de Paris',               'DELEGATION',     'France',             'Europe/Paris'),
    ('DEL-MTL', 'Délégation de Montréal',            'DELEGATION',     'Canada',             'America/Montreal'),
]


def seed_entites(apps, schema_editor):
    Entite = apps.get_model('accounts', 'Entite')
    for code, libelle, type_entite, pays, tz in ENTITES:
        Entite.objects.update_or_create(
            code=code,
            defaults={
                'libelle': libelle,
                'type_entite': type_entite,
                'pays': pays,
                'fuseau_horaire': tz,
                'actif': True,
            },
        )


def unseed_entites(apps, schema_editor):
    Entite = apps.get_model('accounts', 'Entite')
    Entite.objects.filter(code__in=[e[0] for e in ENTITES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_entites, unseed_entites),
    ]
