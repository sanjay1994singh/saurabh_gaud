from django.shortcuts import get_object_or_404, render

from .models import HamareStambh


def index(request):
    stambh_list = HamareStambh.objects.filter(is_active=True)
    return render(
        request,
        "hamare_stambh/index.html",
        {
            "stambh_list": stambh_list,
        },
    )


def detail(request, pk):
    stambh = get_object_or_404(HamareStambh, pk=pk, is_active=True)
    return render(
        request,
        "hamare_stambh/detail.html",
        {
            "stambh": stambh,
        },
    )
