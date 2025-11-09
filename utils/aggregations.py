from sqlalchemy import func


def compute_aggregations(query, group_attr, avg_attr=None):
    """Compute counts and (optionally) average of an attribute grouped by group_attr.

    Args:
        query: SQLAlchemy Query object (unexecuted)
        group_attr: attribute to group by (e.g., Post.media_type or Post.genre)
        avg_attr: (optional) attribute to average (e.g., Post.rating). If None, averages are empty lists.

    Returns:
        (labels_counts, values_counts), (labels_avg, values_avg)
    """
    # Counts
    counts_q = query.with_entities(group_attr.label('group'), func.count().label('count')).group_by(group_attr)
    counts_results = [(g if g is not None else 'Unknown', c) for (g, c) in counts_q.all()]
    counts_results.sort(key=lambda x: x[1], reverse=True)
    top_labels = [r[0] for r in counts_results]
    top_values = [r[1] for r in counts_results]

    # Averages (optional)
    if avg_attr is not None:
        avg_q = query.filter(avg_attr != None).with_entities(group_attr.label('group'), func.avg(avg_attr).label('avg')).group_by(group_attr)
        avg_results = [(g if g is not None else 'Unknown', float(a) if a is not None else 0.0) for (g, a) in avg_q.all()]
        avg_results.sort(key=lambda x: x[1], reverse=True)
        bottom_labels = [r[0] for r in avg_results]
        bottom_values = [round(r[1], 2) for r in avg_results]
    else:
        bottom_labels = []
        bottom_values = []

    return (top_labels, top_values), (bottom_labels, bottom_values)
