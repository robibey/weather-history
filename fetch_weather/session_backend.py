from django.contrib.sessions.backends.db import SessionStore as DbSessionStore
from .models import Location
from users.models import UserPreferences

class SessionStore(DbSessionStore):
    def cycle_key(self):
        old_session_key = super(SessionStore, self).session_key
        super(SessionStore, self).cycle_key()
        self.save()
        Location.objects.filter(session=old_session_key).update(session=self.session_key)
        UserPreferences.objects.filter(session=old_session_key).update(session=self.session_key)