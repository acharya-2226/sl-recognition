from pathlib import Path
from shutil import copy2

from django.conf import settings
from django.core.management.base import BaseCommand
from learning.models import LearningCategory, LearningItem


def chunk_list(items, size=5):
    groups = [items[i:i + size] for i in range(0, len(items), size)]

    # If the final group has 1 or 2 items, merge it with the previous group
    if len(groups) > 1 and len(groups[-1]) <= 2:
        groups[-2].extend(groups[-1])
        groups.pop()

    return groups


NUMBERS = list("0123456789")

ASL_ALPHABET = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

NSL_ALPHABET = [
    "क", "ख", "ग", "घ", "ङ",
    "च", "छ", "ज", "झ", "ञ",
    "ट", "ठ", "ड", "ढ", "ण",
    "त", "थ", "द", "ध", "न",
    "प", "फ", "ब", "भ", "म",
    "य", "र", "ल", "व", "श",
    "ष", "स", "ह", "क्ष", "त्र",
    "ज्ञ"
]


SEED = {
    "NUM": NUMBERS,
    "ASL": ASL_ALPHABET,
    "NSL": NSL_ALPHABET,
}

# Existing source images supplied by the project.
SOURCE_MEDIA_ROOT = Path(r"C:\Academics\Minor_Project_Final\Frontend\media")
PROJECT_MEDIA_ROOT = Path(settings.MEDIA_ROOT)


def image_relative_path(track, title):
    if track == "ASL":
        return Path("asl") / f"{title.lower()}.jpeg"
    if track == "NSL":
        return Path("nsl") / f"{NSL_ALPHABET.index(title)}.jpg"
    return None


def copy_image_into_project_media(track, title):
    relative_path = image_relative_path(track, title)
    if relative_path is None:
        return None

    source_path = SOURCE_MEDIA_ROOT / relative_path
    target_path = PROJECT_MEDIA_ROOT / relative_path
    if not source_path.exists():
        return None

    target_path.parent.mkdir(parents=True, exist_ok=True)
    if source_path.resolve() != target_path.resolve():
        copy2(source_path, target_path)
    return relative_path.as_posix()


class Command(BaseCommand):
    help = "Seed learning categories and items."

    def handle(self, *args, **options):

        for track, items in SEED.items():

            groups = chunk_list(items, 5)

            for group in groups:

                category_name = f"{group[0]} to {group[-1]}"

                category, _ = LearningCategory.objects.get_or_create(
                    track=track,
                    name=category_name
                )

                for order, title in enumerate(group):

                    image_name = copy_image_into_project_media(track, title)
                    defaults = {
                        "description": f"Learn how to sign '{title}'.",
                        "order": order,
                    }
                    if image_name:
                        defaults["image"] = image_name

                    LearningItem.objects.update_or_create(
                        category=category,
                        title=title,
                        defaults=defaults,
                    )

        self.stdout.write(
            self.style.SUCCESS("Learning seed data created successfully.")
        )