from math import ceil


def paginate(query, page: int, limit: int):

    total = query.count()

    items = (
        query
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "items": items,
        "total": total,
        "pages": ceil(total / limit),
        "page": page,
    }
