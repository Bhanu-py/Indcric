from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect, render

from .forms import ClubConsultationForm
from .models import ClubConsultationResponse


SUCCESS_MESSAGE = (
    "Thank you for sharing your opinion. Your response will help us determine whether "
    "there is sufficient support and organizational capacity to establish the cricket club."
)


def cricket_club_view(request):
    if request.method == "POST" and not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())

    response = _existing_response_for(request)
    if request.method == "POST":
        form = ClubConsultationForm(request.POST, user=request.user, instance=response)
        if form.is_valid():
            consultation_response = form.save(commit=False)
            consultation_response.user = request.user
            consultation_response.name = request.user.get_full_name() or request.user.username
            consultation_response.email = request.user.email or ""
            consultation_response.full_clean()
            consultation_response.save()
            request.session["club_consultation_submitted"] = True
            messages.success(request, SUCCESS_MESSAGE)
            return redirect("club:cricket-club")
    else:
        form = ClubConsultationForm(user=request.user, instance=response)

    return render(request, "club/cricket_club.html", {
        "form": form,
        "submitted": request.session.pop("club_consultation_submitted", False),
        "success_message": SUCCESS_MESSAGE,
    })


def _existing_response_for(request):
    if request.user.is_authenticated:
        return (
            ClubConsultationResponse.objects
            .filter(user=request.user)
            .order_by("-updated_at", "-id")
            .first()
        )
    return None
