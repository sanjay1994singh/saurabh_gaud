from django.shortcuts import get_object_or_404, render

from .models import SevaPrakalp


def index(request):
    seva_prakalps = SevaPrakalp.objects.filter(is_active=True)
    return render(
        request,
        "seva_prakalp/index.html",
        {
            "seva_prakalps": seva_prakalps,
        },
    )


def detail(request, pk):
    seva_prakalp = get_object_or_404(SevaPrakalp, pk=pk, is_active=True)
    return render(
        request,
        "seva_prakalp/detail.html",
        {
            "seva_prakalp": seva_prakalp,
        },
    )
