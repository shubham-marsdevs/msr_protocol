from django.db import migrations, models
import django.db.models.deletion


def create_default_users(apps, schema_editor):
    # Get the historical models
    UserRole = apps.get_model('msr_control', 'UserRole')
    User = apps.get_model('auth', 'User')
    
    # Create admin user if it doesn't exist
    if not User.objects.filter(username='admin').exists():
        admin_user = User.objects.create(
            username='admin',
            email='admin@example.com',
            is_superuser=True,
            is_staff=True
        )
        admin_user.set_password('admin123')
        admin_user.save()
        UserRole.objects.create(user=admin_user, role='admin')
    
    # Create calibrator user if it doesn't exist
    if not User.objects.filter(username='calibrator').exists():
        calibrator_user = User.objects.create(
            username='calibrator',
            email='calibrator@example.com'
        )
        calibrator_user.set_password('calibrator123')
        calibrator_user.save()
        UserRole.objects.create(user=calibrator_user, role='calibrator')
    
    # Create operator user if it doesn't exist
    if not User.objects.filter(username='operator').exists():
        operator_user = User.objects.create(
            username='operator',
            email='operator@example.com'
        )
        operator_user.set_password('operator123')
        operator_user.save()
        UserRole.objects.create(user=operator_user, role='operator')


def reverse_func(apps, schema_editor):
    # No need to delete users on reverse migration
    pass


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserRole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('operator', 'Operator'), ('calibrator', 'Calibrator'), ('admin', 'Admin')], default='operator', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='role', to='auth.user')),
            ],
            options={
                'verbose_name': 'User Role',
                'verbose_name_plural': 'User Roles',
            },
        ),
        migrations.RunPython(create_default_users, reverse_func),
    ]
