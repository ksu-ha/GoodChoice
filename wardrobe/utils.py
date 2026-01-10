def get_display_from_comma_separated(obj, field_name, choices):
    """Утилита для получения отображения строк с запятыми"""
    field_value = getattr(obj, field_name, None)
    if not field_value:
        return "Не указано"
    
    choices_dict = dict(choices)
    result = []
    
    for code in field_value.split(','):
        code = code.strip()
        if code in choices_dict:
            result.append(choices_dict[code])
    
    return ', '.join(result) if result else "Не указано"