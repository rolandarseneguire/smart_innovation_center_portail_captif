from django import template

register = template.Library()


@register.filter
def format_bytes(value):
    try:
        bytes_val = int(value)
    except (ValueError, TypeError):
        return "0 Octet"

    if bytes_val <= 0:
        return "Illimité"

    gb = 1073741824
    mb = 1048576

    if bytes_val >= gb:
        return f"{round(bytes_val / gb, 1)} Go"
    elif bytes_val >= mb:
        return f"{round(bytes_val / mb)} Mo"
    else:
        return f"{round(bytes_val / 1024)} Ko"


@register.filter
def format_bps(value):
    try:
        bps_val = int(value)
    except (ValueError, TypeError):
        return "0 bps"

    if bps_val >= 1000000:
        return f"{round(bps_val / 1000000)} Mbps"
    elif bps_val >= 1000:
        return f"{round(bps_val / 1000)} Kbps"
    return f"{bps_val} bps"


@register.filter
def format_duration(minutes):
    try:
        mins = int(minutes)
    except (ValueError, TypeError):
        return "N/A"

    if mins < 60:
        return f"{mins} min"
    elif mins < 1440:
        heures = mins // 60
        reste = mins % 60
        return f"{heures}h{f'{reste:02d}' if reste else ''}"
    else:
        jours = mins // 1440
        return f"{jours} Jour{'s' if jours > 1 else ''}"