from django.apps import AppConfig


class WorkflowsConfig(AppConfig):
    name = 'workflows'

    def ready(self):
        from . import signals  # noqa: F401
