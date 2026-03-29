from import_export import resources, fields
from .models import Profile, CustomUser
from import_export import resources
from .models import CustomUser

class UserResource(resources.ModelResource):

    class Meta:
        model = CustomUser
        import_id_fields = ('email',)
        fields = (
            'email',
            'is_staff',
            'is_active',
        )


class ProfileResource(resources.ModelResource):

    email = fields.Field(column_name='email')

    class Meta:
        model = Profile
        import_id_fields = ('email',)
        fields = (
            'email',
            'membership_type',
            'surname',
            'first_name',
            'call_name',
            'cell_number',
            'gender',
            'owned_stand',
        )

    def before_import_row(self, row, **kwargs):
        email = (row.get("email") or "").strip().lower()

        if not email:
            raise ValueError("Missing email in row")

        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={"username": email}
        )

        row["user"] = user.id
