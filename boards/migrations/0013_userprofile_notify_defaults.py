from django.db import migrations


def set_notify_default(apps, schema_editor):
    UserProfile = apps.get_model("boards", "UserProfile")
    User = apps.get_model("auth", "User")
    # Ensure all users have a profile and notifications enabled
    for user in User.objects.all():
        profile, created = UserProfile.objects.get_or_create(user=user)
        if profile.notify_task_assigned is False:
            profile.notify_task_assigned = True
            profile.save()


class Migration(migrations.Migration):

    dependencies = [
        ("boards", "0012_userprofile_notify_task_assigned"),
    ]

    operations = [
        migrations.RunPython(set_notify_default, migrations.RunPython.noop),
    ]
