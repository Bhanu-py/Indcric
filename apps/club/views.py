from collections import Counter

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect, render

from .forms import ClubConsultationForm, SECTION_QUESTION_FIELDS
from .models import ClubConsultationResponse


SUCCESS_MESSAGE = (
    "Thank you for sharing your opinion. Your response will help us determine whether "
    "there is sufficient support and organizational capacity to establish the cricket club."
)


def cricket_club_view(request):
    if request.method == "POST" and not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())

    summary = consultation_summary()
    response = _existing_response_for(request)
    if request.method == "POST":
        form = ClubConsultationForm(request.POST, user=request.user, instance=response, summary=summary)
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
        form = ClubConsultationForm(user=request.user, instance=response, summary=summary)

    return render(request, "club/cricket_club.html", {
        "form": form,
        "submitted": request.session.pop("club_consultation_submitted", False),
        "success_message": SUCCESS_MESSAGE,
        "summary": summary,
    })


@staff_member_required
def cricket_club_admin_view(request):
    responses = list(
        ClubConsultationResponse.objects
        .select_related("user")
        .order_by("-updated_at", "-id")
    )
    return render(request, "club/admin_summary.html", {
        "responses": responses,
        "summary": consultation_summary(responses),
        "question_rows": consultation_question_rows(responses),
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


def consultation_summary(responses=None):
    responses = list(responses) if responses is not None else list(ClubConsultationResponse.objects.all())
    proceed_values = Counter(response.proceed_choice for response in responses)
    membership_values = Counter(response.membership_preference for response in responses)
    role_values = Counter()
    startup_values = Counter()
    section_question_values = Counter()
    active_role_values = {value for value, label in ClubConsultationResponse.RESPONSIBILITY_CHOICES}
    active_startup_values = {value for value, label in ClubConsultationResponse.STARTUP_TASK_CHOICES}
    for response in responses:
        role_values.update(
            value for value in response.responsibilities or []
            if value in active_role_values
        )
        startup_tasks = [
            value for value in response.startup_tasks or []
            if value in active_startup_values
        ]
        startup_values.update(startup_tasks)
        for field_name, question in (response.section_questions or {}).items():
            if question:
                section_question_values[field_name] += 1

    return {
        "total_responses": len(responses),
        "proceed_counts": _choice_counts(ClubConsultationResponse.PROCEED_CHOICES, proceed_values),
        "membership_counts": _choice_counts(ClubConsultationResponse.MEMBERSHIP_CHOICES, membership_values),
        "role_choice_counts": _choice_counts(ClubConsultationResponse.RESPONSIBILITY_CHOICES, role_values),
        "organizational_role_results": _organizational_role_results(role_values),
        "startup_choice_counts": _choice_counts(ClubConsultationResponse.STARTUP_TASK_CHOICES, startup_values),
        "startup_task_results": _startup_task_results(startup_values),
        "section_question_counts": _choice_counts(SECTION_QUESTION_FIELDS, section_question_values),
        "total_role_votes": sum(role_values.values()),
        "total_startup_task_votes": sum(startup_values.values()),
        "total_questions": sum(section_question_values.values()),
    }


def consultation_question_rows(responses):
    section_labels = dict(SECTION_QUESTION_FIELDS)
    rows = []
    for response in responses:
        display_name = response.name or (
            response.user.get_full_name() or response.user.username
            if response.user_id and response.user
            else "Unknown member"
        )
        for field_name, question in (response.section_questions or {}).items():
            question = (question or "").strip()
            if question:
                rows.append({
                    "member": display_name,
                    "email": response.email,
                    "section": section_labels.get(field_name, field_name),
                    "question": question,
                    "updated_at": response.updated_at,
                })
    return rows


def _choice_counts(choices, values):
    return [
        {
            "value": value,
            "label": label,
            "count": values.get(value, 0),
        }
        for value, label in choices
    ]


def _organizational_role_results(role_values):
    labels = dict(ClubConsultationResponse.RESPONSIBILITY_CHOICES)
    rows = []
    for value in ClubConsultationResponse.ORGANIZATIONAL_ROLE_VALUES:
        interested = role_values.get(value, 0)
        is_director = value in ClubConsultationResponse.DIRECTOR_ROLE_VALUES
        rows.append({
            "value": value,
            "label": labels[value],
            "need_label": "Required" if is_director else "Preferred",
            "need_count": 1,
            "interested": interested,
            "status": (
                "Candidate available"
                if is_director and interested
                else "More candidates needed"
                if is_director
                else "Volunteer available"
                if interested
                else "Volunteer needed"
            ),
            "status_class": "badge-green" if interested else "badge-red",
        })
    return rows


def _startup_task_results(startup_values):
    rows = []
    for value, label in ClubConsultationResponse.STARTUP_RESULT_CHOICES:
        rows.append({
            "value": value,
            "label": label,
            "interested": startup_values.get(value, 0),
        })
    return rows
