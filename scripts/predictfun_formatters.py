#!/usr/bin/env python3

def cents(x):
    return round(float(x) * 100, 1)


def format_buy_order_set(project, date, yes_price, no_price, spread, my_yes, my_no):
    return (
        f"**{project} ({date})**\n"
        f"• рынок: Yes {cents(yes_price):.1f}¢, No {cents(no_price):.1f}¢, spread {cents(spread):.1f}¢\n"
        f"• твои ордера: Yes {my_yes}, No {my_no}"
    )


def format_buy_confirm(project, date, yes_price, no_price, spread, my_yes, my_no, actions):
    return (
        format_buy_order_set(project, date, yes_price, no_price, spread, my_yes, my_no)
        + "\n❗️**Что делать:**\n"
        + "\n".join(actions)
        + "\n\n**Подтвердить переставление?**"
    )


def format_buy_placed(project, date, side, price_cents, shares):
    return (
        f"**{project} ({date})**\n"
        f"• рынок: buy-ордер выставлен\n"
        f"• твои ордера: {side} {price_cents:.1f}¢ ({shares:.2f} shares)\n"
        f"❗️**Что делать:**\n"
        f"• **{side}** — ордер поставлен, дальше модуль мониторит и при необходимости предложит перестановку."
    )


def format_replaced(project, date, side, old_price_cents, new_price_cents, shares):
    return (
        f"**{project} ({date})**\n"
        f"• рынок: ордер переставлен\n"
        f"• твои ордера: {side} {old_price_cents:.1f}¢ → {new_price_cents:.1f}¢ ({shares:.2f} shares)\n"
        f"❗️**Что делать:**\n"
        f"• **{side}** — переставление выполнено после твоего подтверждения."
    )
