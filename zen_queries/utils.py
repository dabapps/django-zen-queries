def fetch(queryset):
    queryset._fetch_all()
    return queryset
