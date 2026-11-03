import json
import random

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import LearningCategory, LearningItem, TRACK_CHOICES, TrackVisibility


def _visibility_map():
    settings = TrackVisibility.objects.in_bulk(field_name="track")
    return {
        code: settings.get(code)
        for code, _label in TRACK_CHOICES
    }


def _enabled_tracks(flag_name):
    visibility = _visibility_map()
    return {
        code for code, _label in TRACK_CHOICES
        if visibility[code] is None or getattr(visibility[code], flag_name)
    }


def home(request):
    enabled = _enabled_tracks("show_in_learning")
    return render(request, "home.html", {
        "tracks": [pair for pair in TRACK_CHOICES if pair[0] in enabled],
    })


def learn(request):
    enabled = _enabled_tracks("show_in_learning")
    categories = LearningCategory.objects.prefetch_related("items").all()
    tracks = {}

    for code, label in TRACK_CHOICES:
        if code not in enabled:
            continue
        track_categories = [category for category in categories if category.track == code]
        for category in track_categories:
            category.active_items = [
                item for item in category.items.all() if item.is_active
            ]
        tracks[code] = {
            "label": label,
            "categories": track_categories,
        }

    return render(request, "learn.html", {"tracks": tracks})


def category_detail(request, category_id):
    category = get_object_or_404(LearningCategory, id=category_id)
    if category.track not in _enabled_tracks("show_in_learning"):
        return redirect("learn")
    items = category.items.filter(is_active=True)
    return render(request, "category.html", {
        "category": category,
        "items": items,
    })


def item_detail(request, item_id):
    item = get_object_or_404(LearningItem, id=item_id, is_active=True)
    if item.category.track not in _enabled_tracks("show_in_learning"):
        return redirect("learn")
    siblings = list(item.category.items.filter(is_active=True))
    index = siblings.index(item)
    next_item = siblings[index + 1] if index + 1 < len(siblings) else None
    return render(request, "lesson.html", {
        "item": item,
        "next_item": next_item,
    })


def practice(request):
    enabled = _enabled_tracks("show_in_practice")
    items = list(
        LearningItem.objects.filter(
            is_active=True,
            category__track__in=enabled,
        ).select_related("category")
    )

    if len(items) < 5:
        return render(request, "practice.html", {"ready": False})

    questions = random.sample(items, 5)
    round_data = []
    for question in questions:
        pool = [item for item in items if item.id != question.id]
        choices = random.sample(pool, 3) + [question]
        random.shuffle(choices)
        round_data.append({
            "question_id": question.id,
            "title": question.title,
            "image": question.image.url if question.image else "",
            "choices": [
                {"id": choice.id, "title": choice.title}
                for choice in choices
            ],
        })

    return render(request, "practice.html", {
        "ready": True,
        "first_question": round_data[0],
        "round_data": round_data,
    })


@csrf_exempt
@require_POST
def practice_check(request):
    data = json.loads(request.body or "{}")
    return JsonResponse({
        "correct": str(data.get("question_id")) == str(data.get("selected_id"))
    })


def test_page(request):
    enabled = _enabled_tracks("show_in_validation")
    categories = LearningCategory.objects.prefetch_related("items").all()
    categories = [
        category for category in categories
        if category.track in enabled
        and category.items.filter(is_active=True).exists()
    ]
    return render(request, "test.html", {"categories": categories})


def test_category(request, category_id):
    category = get_object_or_404(LearningCategory, id=category_id)
    if category.track not in _enabled_tracks("show_in_validation"):
        return redirect("test_page")
    items = list(category.items.filter(is_active=True))
    random.shuffle(items)
    return render(request, "test_category.html", {
        "category": category,
        "items": items,
    })


def tts(request):
    enabled = _enabled_tracks("show_in_tts")
    tracks = [
        {"code": code, "label": label}
        for code, label in TRACK_CHOICES
        if code in enabled
    ]
    return render(request, "tts.html", {"tracks": tracks})


@require_POST
def validate_api(request, category_id):
    category = get_object_or_404(LearningCategory, id=category_id)
    if category.track not in _enabled_tracks("show_in_validation"):
        return JsonResponse({"status": "disabled"}, status=404)
    return JsonResponse({
        "status": "ready",
        "category_id": category.id,
        "track": category.track,
        "message": "Use the live camera to validate each sign.",
    })
