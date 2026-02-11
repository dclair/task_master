from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.crypto import constant_time_compare
from django.utils.http import base36_to_int


# Generador de tokens de activación con soporte de expiración explícita.
class ActivationTokenGenerator(PasswordResetTokenGenerator):
    # API compatible con PasswordResetTokenGenerator.
    def check_token(self, user, token):
        return self.get_token_state(user, token) == "valid"

    # Devuelve estado detallado: valid | expired | invalid.
    def get_token_state(self, user, token):
        if not (user and token):
            return "invalid"
        # Same format as PasswordResetTokenGenerator: "{ts}-{hash}"
        try:
            ts_b36, _ = token.split("-", 1)
        except ValueError:
            return "invalid"

        try:
            ts = base36_to_int(ts_b36)
        except ValueError:
            return "invalid"

        # Check that the timestamp/uid has not been tampered with
        for secret in [self.secret, *self.secret_fallbacks]:
            if constant_time_compare(
                self._make_token_with_timestamp(user, ts, secret),
                token,
            ):
                break
        else:
            return "invalid"

        timeout = getattr(settings, "ACTIVATION_TOKEN_TIMEOUT", 60 * 60 * 24)
        if (self._num_seconds(self._now()) - ts) > timeout:
            return "expired"
        return "valid"


# Instancia reutilizable para todo el flujo de activación.
activation_token_generator = ActivationTokenGenerator()
