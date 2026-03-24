from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Profile, CustomUser


class ProfileResource(resources.ModelResource):
    # Map CSV column "user" (email) to FK via email
    user = fields.Field(
        column_name='user',
        attribute='user',
        widget=ForeignKeyWidget(CustomUser, 'email')
    )

    class Meta:
        model = Profile
        import_id_fields = ('user',)
        fields = (
            'user',
            'membership_type',
            'surname',
            'first_name',
            'call_name',
            'cell_number',
            'gender',
            'owned_stand',
        )
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        email = (row.get("user") or "").strip().lower()

        # 🚫 Block bad rows early
        if not email:
            raise ValueError("Missing 'user' (email) value in this row")

        # Ensure user exists
        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={"username": email}  # safe even if username unused
        )

        # Keep email (not id) so ForeignKeyWidget resolves it
        row["user"] = user.email
