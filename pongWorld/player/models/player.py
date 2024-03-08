from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from config.models import TimestampBaseModel

class PlayerManager(BaseUserManager):
    use_in_migrations = True
    def create_user(self, email, nickname, password=None, **extra_fields):
        if not email:
            raise ValueError('must have user email')
        if not nickname:
            raise ValueError('must have user nickname')

        email = self.normalize_email(email)
        user = self.model(email=email, nickname=nickname, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, nickname, email, password):
        user = self.create_user(
            nickname=nickname,
            email=self.normalize_email(email),
            password=password
        )
        user.is_superuser = True
        user.save(using=self._db)

        return user

class Player(AbstractBaseUser, TimestampBaseModel, PermissionsMixin):
    nickname    = models.CharField(max_length=10, unique=True)
    email       = models.EmailField(max_length=30, unique=True)
    profile_img = models.ImageField(upload_to='profile_imgs', default=None, blank=True, null=True)
    intro       = models.CharField(max_length=200, default='', blank=True)
    matches     = models.PositiveIntegerField(default=0)
    wins        = models.PositiveIntegerField(default=0)
    total_score = models.PositiveIntegerField(default=0)
    online_count = models.PositiveIntegerField(default=0)
    last_login_time = models.DateTimeField()

    objects = PlayerManager()

    USERNAME_FIELD = 'nickname'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = "player"

    def __str__(self):
        return f"Player ID {self.id}"

    @property
    def is_staff(self):
        return self.is_superuser

class Block(TimestampBaseModel):
    blocker    = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='blocks')
    blocked    = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='blocked_by')

    class Meta:
        db_table = "block"

    def __str__(self):
        return f"Player {self.blocker_id.id} blocked Player {self.blocked_id.id}"