from django.contrib.auth.models import Group


def create_groups():
    roles = ['Supply Officer', 'BAC Officer', 'Requisitioner', 'Admin']

    for role in roles:
        group, created = Group.objects.get_or_create(name=role)
        if created:
            print(f'{role} Group Created')


def assign_role_and_save(user, role_name):
    try:
        role_map = {
            "admin": "Admin",

            "supply": "Supply Officer",
            "supply officer": "Supply Officer",

            "bac": "BAC Officer",
            "bac officer": "BAC Officer",

            "requisitioner": "Requisitioner",
        }

        group_name = role_map.get(role_name.lower())

        group = Group.objects.get(name=group_name)
        user.groups.add(group)
        user.save()
        print(f'{role_name} assign to {user} ')
    except Group.DoesNotExist:
        print(f'Role {role_name} Does Not Exist')
