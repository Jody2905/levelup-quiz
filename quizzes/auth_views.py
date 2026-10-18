from django.contrib.auth.views import LoginView

from . import ratelimit

LOCKED_MESSAGE = "Too many failed login attempts. Please wait 15 minutes and try again."


class RateLimitedLoginView(LoginView):
    """Django's LoginView plus lockout after repeated failures.

    Failures are counted per username (stops guessing one account's password)
    and per IP address (stops one machine trying many accounts).
    """

    def _keys(self):
        username = self.request.POST.get("username", "")
        return username, ratelimit.client_ip(self.request)

    def post(self, request, *args, **kwargs):
        username, ip = self._keys()
        if ratelimit.is_limited("login_user", username) or ratelimit.is_limited("login_ip", ip):
            form = self.form_class(request=request, initial={"username": username})
            context = self.get_context_data(form=form, locked_message=LOCKED_MESSAGE)
            return self.render_to_response(context, status=429)
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        username, ip = self._keys()
        ratelimit.hit("login_user", username)
        ratelimit.hit("login_ip", ip)
        return super().form_invalid(form)

    def form_valid(self, form):
        username, _ = self._keys()
        ratelimit.reset("login_user", username)
        return super().form_valid(form)
