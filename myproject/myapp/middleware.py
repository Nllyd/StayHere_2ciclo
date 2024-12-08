from django.shortcuts import redirect

class RequireVerifiedUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_verified:
            if request.path not in ['/verificacion/', '/logout/']:  # Rutas permitidas
                return redirect('/verificacion/')  # Redirigir a la página de verificación
        return self.get_response(request)
