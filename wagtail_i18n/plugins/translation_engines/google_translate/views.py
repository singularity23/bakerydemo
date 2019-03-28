from collections import defaultdict

from django.contrib import messages
from django.db import transaction
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect
from django.utils.text import slugify

from wagtail_i18n.plugins.workflow.models import TranslationRequest
from wagtail_i18n.segments import SegmentValue, TemplateValue
from wagtail_i18n.segments.extract import extract_segments
from wagtail_i18n.segments.ingest import ingest_segments

# TODO: Switch to official Google API client
from googletrans import Translator


@require_POST
def translate(request, translation_request_id):
    translation_request = get_object_or_404(TranslationRequest, id=translation_request_id)
    translator = Translator()

    for page in translation_request.pages.all():
        instance = page.source_revision.as_page_object()

        segments = extract_segments(instance)

        text_segments = [segment for segment in segments if isinstance(segment, SegmentValue)]
        template_segments = [segment for segment in segments if isinstance(segment, TemplateValue)]

        # Group segments by source text so we only submit them once
        text_segments_grouped = defaultdict(list)
        for segment in text_segments:
            text_segments_grouped[segment.text].append(segment.path)

        translations = translator.translate(
            list(text_segments_grouped.keys()),
            src='en',  # FIXME (Google Translate doesn't like 'en-gb')
            dest=translation_request.target_locale.language.code,
        )

        translated_segments = template_segments.copy()
        for translation in translations:
            translated_segments.extend([
                SegmentValue(path, translation.text)
                for path in text_segments_grouped[translation.origin]
            ])

        with transaction.atomic():
            try:
                translation = instance.get_translation(translation_request.target_locale)
            except instance.__class__.DoesNotExist:
                translation = instance.copy_for_translation(translation_request.target_locale)

            ingest_segments(instance, translation, translation_request.source_locale, translation_request.target_locale, translated_segments)
            translation.slug = slugify(translation.slug)
            translation.save_revision()

    # TODO: Plural
    messages.success(request, "%d pages successfully translated with Google Translate" % translation_request.pages.count())

    return redirect('wagtail_i18n_workflow_management:detail', translation_request_id)