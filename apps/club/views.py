from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import ClubConsultationForm
from .models import ClubConsultationResponse


SUCCESS_MESSAGE = (
    "Thank you for sharing your opinion. Your response will help us determine whether "
    "there is sufficient support and organizational capacity to establish the cricket club."
)


def cricket_club_view(request):
    response = _existing_response_for(request)
    if request.method == "POST":
        form = ClubConsultationForm(request.POST, user=request.user, instance=response)
        if form.is_valid():
            consultation_response = form.save(commit=False)
            if request.user.is_authenticated:
                consultation_response.user = request.user
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
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        if email:
            return (
                ClubConsultationResponse.objects
                .filter(email__iexact=email, user__isnull=True)
                .order_by("-updated_at", "-id")
                .first()
            )
    return None
