from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_customuser_totp_enabled_customuser_totp_secret_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='totp_secret',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='totp_enabled',
            field=models.BooleanField(default=False),
        ),
    ]