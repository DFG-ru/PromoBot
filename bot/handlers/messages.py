"""Тексты ответов бота (единый источник для всех хэндлеров)."""


def follow_channel_text(social_media_url: str) -> str:
    return (
        "Следите за новыми предложениями в нашем телеграмм канале:\n"
        "\n"
        f"{social_media_url}\n"
        "💎💎💎\n"
    )


WELCOME_MESSAGE = (
    "Здравствуйте! Чтобы получить купон, поделитесь номером телефона "
    "с помощью кнопки ниже⬇️⬇️⬇️"
)

UNKNOWN_MESSAGE = "⬇️⬇️⬇️Для получения купона нужно поделиться номером по кнопке ниже⬇️⬇️⬇️"

PROMO_ENDED_TEMPLATE = "Выдача купонов завершена.\n\n"

COUPONS_EXHAUSTED_TEMPLATE = "К сожалению, все купоны уже разыграны.\n\n"

COUPONS_TEMPORARILY_UNAVAILABLE = "Купоны временно недоступны. Попробуйте позже."

COUPON_RENDER_ERROR = "Не удалось сформировать ваш купон. Попробуйте позже."

YOUR_COUPON = "Ваш купон:"


def promo_deadline_text(promo_end_date, before=None) -> str:
    """Формирует текст о дедлайне купона из конфигурации (promo_end_date)."""
    if promo_end_date is not None:
        return f"Вы можете использовать купон до {promo_end_date.strftime('%d.%m.%Y')} включительно."
    return "Сроки действия купона уточняйте у организаторов акции."
