from django.db import models
from django.db import models


FACULTY_CHOICES = [
    ("science_it", "Computer Science & IT"),
    ("math", "Mathematical Sciences"),
    ("commerce", "Commerce, Administration & Law"),
    ("arts", "Arts"),
    ("education", "Education"),
]

SEMESTER_CHOICES = [(1, "Semester 1"), (2, "Semester 2")]

PAPER_TYPE_CHOICES = [
    ("exam", "Examination"),
    ("test", "Test"),
    ("quiz", "Quiz"),
    ("assignment", "Assignment"),
]

STATUS_CHOICES = [
    ("pending", "Pending Review"),
    ("approved", "Approved"),
    ("rejected", "Rejected"),
]


class PastPaper(models.Model):
    module_code = models.CharField(max_length=20)
    module_name = models.CharField(max_length=200)
    faculty = models.CharField(max_length=30, choices=FACULTY_CHOICES, blank=True)
    year = models.PositiveSmallIntegerField()
    semester = models.PositiveSmallIntegerField(choices=SEMESTER_CHOICES)
    paper_type = models.CharField(max_length=20, choices=PAPER_TYPE_CHOICES)

    # Public submissions default to "pending" (model default below) and only
    # become visible in the public vault once a staff member approves them
    # via /admin/. Papers added directly through admin default to "approved"
    # instead (see PastPaperAdmin.get_form) since staff are the trusted source.
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")

    # SQLite stores this row (code, year, type...) - the actual PDF lives on
    # disk under MEDIA_ROOT/past_papers/<year>/, and this field just stores
    # the path to it.
    file = models.FileField(upload_to="past_papers/%Y/")

    # SHA-256 of the uploaded file's content - used to detect when someone
    # submits the exact same PDF twice, regardless of what metadata they
    # entered. Checked at submission time in PastPaperForm.clean_file().
    file_hash = models.CharField(max_length=64, db_index=True, blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    @property
    def title(self):
        return f"{self.module_name} - {self.get_paper_type_display()}"

    def __str__(self):
        return f"{self.module_code} ({self.year}) - {self.get_paper_type_display()}"

    def save(self, *args, **kwargs):
        # Normalize so "4cps312" and "4CPS312" aren't treated as different
        # modules when searching/filtering.
        self.module_code = self.module_code.strip().upper()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-year", "module_code"]
# Create your models here.
