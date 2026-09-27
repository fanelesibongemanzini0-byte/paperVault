import hashlib

from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .models import PastPaper, FACULTY_CHOICES, SEMESTER_CHOICES, PAPER_TYPE_CHOICES


class PastPaperForm(forms.ModelForm):
    class Meta:
        model = PastPaper
        fields = ["module_code", "module_name", "faculty", "year", "semester", "paper_type", "file"]

    def clean_file(self):
        uploaded_file = self.cleaned_data["file"]
        uploaded_file.seek(0)
        content = uploaded_file.read()
        uploaded_file.seek(0)  # reset so Django can still save the file afterwards

        file_hash = hashlib.sha256(content).hexdigest()

        existing = PastPaper.objects.filter(file_hash=file_hash)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)

        if existing.exists():
            match = existing.first()
            raise forms.ValidationError(
                f"This exact file has already been submitted (as {match.module_code}, "
                f"{match.year} {match.get_paper_type_display()}). No need to upload it again."
            )

        # Stash the hash on the instance now, so form.save() persists it
        # along with everything else in a single write.
        self.instance.file_hash = file_hash
        return uploaded_file


def index(request):
    q = request.GET.get("q", "").strip()
    faculty = request.GET.get("faculty", "")
    year = request.GET.get("year", "")
    semester = request.GET.get("semester", "")
    paper_type = request.GET.get("paper_type", "")

    papers = PastPaper.objects.filter(status="approved")

    if q:
        papers = papers.filter(
            Q(module_code__icontains=q) | Q(module_name__icontains=q)
        )
    if faculty:
        papers = papers.filter(faculty=faculty)
    if year:
        papers = papers.filter(year=year)
    if semester:
        papers = papers.filter(semester=semester)
    if paper_type:
        papers = papers.filter(paper_type=paper_type)

    available_years = (
        PastPaper.objects.order_by("-year").values_list("year", flat=True).distinct()
    )

    context = {
        "papers": papers,
        "faculty_choices": FACULTY_CHOICES,
        "semester_choices": SEMESTER_CHOICES,
        "paper_type_choices": PAPER_TYPE_CHOICES,
        "available_years": available_years,
        "selected": {
            "q": q, "faculty": faculty, "year": year,
            "semester": semester, "paper_type": paper_type,
        },
    }
    return render(request, "index.html", context)


def submit_paper(request):
    if request.method == "POST":
        form = PastPaperForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Paper submitted - it'll appear in the vault once approved by an admin.")
            return redirect("paper_vault_index")
    else:
        form = PastPaperForm()

    return render(request, "submit.html", {"form": form})


# ---------------------------------------------------------------------------
# Staff review queue - a themed in-app alternative to raw Django admin, for
# non-technical reviewers. Reuses Django's built-in staff-account system
# (@staff_member_required redirects anyone who isn't logged in as staff to
# the standard admin login page) so no separate auth system is needed.
# ---------------------------------------------------------------------------
@staff_member_required
def review_queue(request):
    pending = PastPaper.objects.filter(status="pending").order_by("-uploaded_at")
    return render(request, "papervault/review.html", {"pending": pending})


@staff_member_required
def review_action(request, pk):
    if request.method != "POST":
        return redirect("paper_vault_review")

    paper = get_object_or_404(PastPaper, pk=pk)
    action = request.POST.get("action")

    if action == "approve":
        paper.status = "approved"
        paper.save(update_fields=["status"])
        messages.success(request, f"Approved: {paper.module_code} ({paper.year}).")
    elif action == "reject":
        paper.status = "rejected"
        paper.save(update_fields=["status"])
        messages.info(request, f"Rejected: {paper.module_code} ({paper.year}).")

    return redirect("paper_vault_review")