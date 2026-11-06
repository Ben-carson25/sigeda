from django.db import migrations, models


def lecteur_vers_agent(apps, schema_editor):
    Utilisateur = apps.get_model('accounts', 'Utilisateur')
    Utilisateur.objects.filter(role='LECTEUR').update(role='AGENT')


def agent_vers_lecteur(apps, schema_editor):
    Utilisateur = apps.get_model('accounts', 'Utilisateur')
    Utilisateur.objects.filter(role='AGENT').update(role='LECTEUR')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_seed_entites'),
    ]

    operations = [
        migrations.AlterField(
            model_name='utilisateur',
            name='role',
            field=models.CharField(
                choices=[('ADMIN', 'Administrateur'), ('GESTIONNAIRE', 'Gestionnaire documentaire'),
                         ('VALIDATEUR', 'Validateur'), ('AGENT', 'Agent'), ('RESPONSABLE', 'Responsable')],
                default='AGENT', max_length=20),
        ),
        migrations.RunPython(lecteur_vers_agent, agent_vers_lecteur),
    ]
