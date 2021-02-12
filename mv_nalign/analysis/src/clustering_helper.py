import numpy as np
import itertools
from sklearn.cluster import DBSCAN
import statistics


# returns points
def cover_box_with_points_grid(box, threshold):
    x1 = box[0]
    x2 = box[2]
    y1 = box[1]
    y2 = box[3]

    if (abs(x1 - x2) > 0.8) and (abs(y1 - y2) > 0.8):
        return [[x1, y1], [x2, y2]]
    x = [x1]
    y = [y1]
    while(x2 - x1) > threshold:
        x1 += threshold
        x.append(x1)
    x.append(x2)

    while(y2 - y1) > threshold:
        y1 += threshold
        y.append(y1)
    y.append(y2)

    return list(itertools.product(x, y))


# Get bounding box for cloud of points (numpy array)
def get_box_form_points(result_clustered):
    x1 = result_clustered[:, 0].min()
    x2 = result_clustered[:, 0].max()
    y1 = result_clustered[:, 1].min()
    y2 = result_clustered[:, 1].max()
    return [x1, y1, x2, y2]


# Client class must implement prepare_aws_formatted_points method
def cluster_points(points, the_coefficient) -> np.array:
    if not points.shape[0]:
        return np.array([])

    db = DBSCAN(eps=0.05, min_samples=12 / the_coefficient,  n_jobs=-1).fit(points)

    labels = np.array(db.labels_)

    result = np.array([])
    cluster_set = set(labels)
    clusters = []
    clusters_volumes = []
    for c in cluster_set:
        if c == -1:
            continue
        ci = points[labels == c]
        clusters_volumes.append(len(ci))
        clusters.append(ci)

    clusters = np.array(clusters)
    clusters_volumes = np.array(clusters_volumes)
    if len(clusters_volumes):
        median_volume = statistics.median(clusters_volumes)
        result = clusters[clusters_volumes > median_volume*0.05]

    return result
