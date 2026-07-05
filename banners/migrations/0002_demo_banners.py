from django.db import migrations


DEMO_BANNERS = (
    {
        "title": "Demo Header Top Banner",
        "placement": "header_top",
        "image": "banners/main_image_banner.jpg",
        "text": "Header top banner demo",
        "link_label": "Every page below navigation",
        "display_order": 10,
    },
    {
        "title": "Demo Home After Hero Banner",
        "placement": "home_after_hero",
        "image": "banners/main_image_banner.jpg",
        "text": "Home after hero banner demo",
        "link_label": "Homepage first ad slot",
        "display_order": 20,
    },
    {
        "title": "Demo Home Middle Banner",
        "placement": "home_middle",
        "image": "banners/main_image_banner.jpg",
        "text": "Home middle banner demo",
        "link_label": "Above Hamare Stambh",
        "display_order": 30,
    },
    {
        "title": "Demo Detail Sidebar Ad",
        "placement": "sidebar",
        "text": "Detail page sidebar ad demo",
        "link_label": "Shown beside event, seva, and stambh details",
        "display_order": 40,
    },
    {
        "title": "Demo Footer Top Banner",
        "placement": "footer_top",
        "text": "Footer top banner demo",
        "link_label": "Every page above footer",
        "display_order": 50,
    },
)


def create_demo_banners(apps, schema_editor):
    Banner = apps.get_model("banners", "Banner")
    for banner_data in DEMO_BANNERS:
        Banner.objects.update_or_create(
            title=banner_data["title"],
            defaults={
                **banner_data,
                "is_active": True,
                "link_url": "",
                "starts_at": None,
                "ends_at": None,
            },
        )


def remove_demo_banners(apps, schema_editor):
    Banner = apps.get_model("banners", "Banner")
    Banner.objects.filter(title__in=[banner["title"] for banner in DEMO_BANNERS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("banners", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_demo_banners, remove_demo_banners),
    ]
