from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from i18nfield.fields import I18nCharField, I18nTextField
from pretix.base.models import LoggedModel


class Page(LoggedModel):
    event = models.ForeignKey("pretixbase.Event", on_delete=models.CASCADE)
    slug = models.CharField(
        max_length=150,
        db_index=True,
        verbose_name=_("URL form"),
        validators=[
            RegexValidator(
                regex="^[a-zA-Z0-9.-]+$",
                message=_(
                    "The slug may only contain letters, numbers, dots and dashes."
                ),
            ),
        ],
        help_text=_(
            "This will be used to generate the URL of the page. Please only use latin letters, "
            "numbers, dots and dashes. You cannot change this afterwards."
        ),
    )
    position = models.IntegerField(default=0)
    title = I18nCharField(verbose_name=_("Page title"))
    text = I18nTextField(verbose_name=_("Page content"))
    link_on_frontpage = models.BooleanField(
        default=False, verbose_name=_("Show link on the event start page")
    )
    link_in_footer = models.BooleanField(
        default=False, verbose_name=_("Show link in the event footer")
    )
    require_confirmation = models.BooleanField(
        default=False,
        verbose_name=_(
            "Require the user to acknowledge this page before an "
            "order is created (e.g. for terms of service)."
        ),
    )
    content_type = models.CharField(verbose_name='Content type', default='html', choices=[('html', 'HTML'), ('markdown', 'Markdown')], max_length=10)

    class Meta:
        ordering = ["position", "title"]
