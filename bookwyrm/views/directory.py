""" who all's here? """
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.views import View
from django.utils.decorators import method_decorator

from .helpers import get_suggested_users

# pylint: disable=no-self-use
@method_decorator(login_required, name="dispatch")
class Directory(View):
    """ display of known bookwyrm users """

    def get(self, request):
        """ lets see your cute faces """
        try:
            page = int(request.GET.get("page", 1))
        except ValueError:
            page = 1

        # filters
        filters = {}
        software = request.GET.get("software")
        if not software or software == "bookwyrm":
            filters["bookwyrm_user"] = True
        scope = request.GET.get("scope")
        if scope == "local":
            filters["local"] = True

        users = get_suggested_users(request.user, **filters)
        sort = request.GET.get("sort")
        if sort == "recent":
            users = users.order_by("-last_active_date")
        else:
            users = users.order_by("-mutuals", "-shared_books", "-last_active_date")

        paginated = Paginator(users, 12)

        data = {
            "users": paginated.page(page),
        }
        return TemplateResponse(request, "directory.html", data)

    def post(self, request):
        """ join the directory """
        request.user.discoverable = True
        request.user.save()
        return redirect("directory")
