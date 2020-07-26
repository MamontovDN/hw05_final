from datetime import datetime as dt


def year(request):
    return {'year': dt.today().year,}
